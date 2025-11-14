import logging
from typing import Dict, Any, Tuple
from urllib.parse import unquote


def parse_s3_event(event_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Parse S3 event data to extract bucket and key
    
    Args:
        event_data: Raw event data from VastEvent
    
    Returns:
        Dict with 'bucket', 'key', 'event_name', 'sequencer', 'etag'
    """
    logging.info(f"Parsing S3 event: {event_data}")
    
    # Handle different event formats
    sequencer = None
    etag = None
    
    if "Records" in event_data:
        # Standard S3 event format
        record = event_data["Records"][0]
        s3_info = record.get("s3", {})
        bucket = s3_info.get("bucket", {}).get("name", "")
        key = s3_info.get("object", {}).get("key", "")
        sequencer = s3_info.get("object", {}).get("sequencer", "")
        etag = s3_info.get("object", {}).get("eTag", "")
        event_name = record.get("eventName", "unknown")
    elif "bucket" in event_data and "key" in event_data:
        # Direct format
        bucket = event_data["bucket"]
        key = event_data["key"]
        event_name = event_data.get("eventName", "unknown")
    else:
        raise ValueError(f"Unsupported event format: {event_data}")
    
    # URL-decode the key (S3 events often have URL-encoded keys)
    key = unquote(key)
    
    logging.info(f"Parsed S3 event - bucket: {bucket}, key: {key}, event: {event_name}, sequencer: {sequencer}, etag: {etag}")
    return {
        "bucket": bucket,
        "key": key,
        "event_name": event_name,
        "sequencer": sequencer,
        "etag": etag
    }


def should_process_event(key: str, event_name: str) -> Tuple[bool, str]:
    """
    Check if the event should be processed
    
    Args:
        key: S3 object key
        event_name: S3 event name
    
    Returns:
        Tuple of (should_process, skip_reason)
    """
    # Skip delete events
    if "Delete" in event_name:
        return False, "Delete event - skipping"
    
    # Check if it's a video file
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm']
    key_lower = key.lower()
    
    if not any(key_lower.endswith(ext) for ext in video_extensions):
        return False, f"Not a video file - skipping (key: {key})"
    
    # Skip if already a segment (to avoid infinite loop)
    if "_segment_" in key_lower or "-segment-" in key_lower:
        return False, "Already a segment - skipping"
    
    return True, ""


def get_output_bucket_name(input_bucket: str, suffix: str = "-segments") -> str:
    """
    Get output bucket name for segments
    
    Args:
        input_bucket: Input bucket name
        suffix: Suffix to add to bucket name
    
    Returns:
        Output bucket name
    """
    return f"{input_bucket}{suffix}"


def get_segment_key(original_filename: str, segment_number: int, total_segments: int) -> str:
    """
    Generate S3 key for a segment
    
    Args:
        original_filename: Original video filename
        segment_number: Segment number (1-indexed)
        total_segments: Total number of segments
    
    Returns:
        S3 key for the segment
    """
    # Extract filename without extension
    name_parts = original_filename.rsplit('.', 1)
    base_name = name_parts[0]
    extension = name_parts[1] if len(name_parts) > 1 else 'mp4'
    
    # Create segment key with zero-padded number
    segment_key = f"segments/{base_name}_segment_{segment_number:03d}_of_{total_segments:03d}.{extension}"
    
    return segment_key


def prepare_metadata(
    original_metadata: Dict[str, str],
    segment_number: int,
    total_segments: int,
    duration: float,
    original_filename: str
) -> Dict[str, str]:
    """
    Prepare metadata for a video segment
    
    Args:
        original_metadata: Metadata from original video
        segment_number: Segment number (1-indexed)
        total_segments: Total number of segments
        duration: Segment duration in seconds
        original_filename: Original video filename
    
    Returns:
        Metadata dict for the segment
    """
    # Copy original metadata (includes is-public, allowed-users, tags, etc.)
    metadata = {}
    if "Metadata" in original_metadata:
        metadata = dict(original_metadata["Metadata"])
    
    # Add segment-specific metadata
    metadata["segment_number"] = str(segment_number)
    metadata["total_segments"] = str(total_segments)
    metadata["segment_duration"] = f"{duration:.2f}"
    metadata["original_video"] = original_filename  # Changed from "original_filename"
    metadata["segment_type"] = "video_segment"
    
    # Ensure critical fields are preserved (they should be in the copy, but be explicit)
    # These fields come from the frontend upload and MUST be preserved:
    # - is-public: "true" or "false" (default true for CLI uploads)
    # - allowed-users: comma-separated usernames (empty for CLI uploads)
    # - tags: comma-separated tags
    # - upload-timestamp: when video was uploaded
    
    return metadata

