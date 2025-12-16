import logging
from typing import Dict, Any, Tuple
from urllib.parse import unquote


def parse_s3_event(event_data: Dict[str, Any]) -> Dict[str, str]:
    """Parse S3 event data to extract bucket and key."""
    sequencer = None
    etag = None
    
    if "Records" in event_data:
        record = event_data["Records"][0]
        s3_info = record.get("s3", {})
        bucket = s3_info.get("bucket", {}).get("name", "")
        key = s3_info.get("object", {}).get("key", "")
        sequencer = s3_info.get("object", {}).get("sequencer", "")
        etag = s3_info.get("object", {}).get("eTag", "")
        event_name = record.get("eventName", "unknown")
    elif "bucket" in event_data and "key" in event_data:
        bucket = event_data["bucket"]
        key = event_data["key"]
        event_name = event_data.get("eventName", "unknown")
    else:
        raise ValueError(f"Unsupported event format: {event_data}")
    
    key = unquote(key)
    
    return {
        "bucket": bucket,
        "key": key,
        "event_name": event_name,
        "sequencer": sequencer,
        "etag": etag
    }


def should_process_event(key: str, event_name: str) -> Tuple[bool, str]:
    """Check if the event should be processed. Returns (should_process, skip_reason)."""
    if "Delete" in event_name:
        return False, "Delete event"
    
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm']
    key_lower = key.lower()
    
    if not any(key_lower.endswith(ext) for ext in video_extensions):
        return False, f"Not a video file: {key}"
    
    if "_segment_" in key_lower or "-segment-" in key_lower:
        return False, "Already a segment"
    
    return True, ""


def get_output_bucket_name(input_bucket: str, suffix: str = "-segments") -> str:
    """Get output bucket name for segments."""
    return f"{input_bucket}{suffix}"


def get_segment_key(original_filename: str, segment_number: int, total_segments: int) -> str:
    """Generate S3 key for a segment."""
    name_parts = original_filename.rsplit('.', 1)
    base_name = name_parts[0]
    extension = name_parts[1] if len(name_parts) > 1 else 'mp4'
    return f"segments/{base_name}_segment_{segment_number:03d}_of_{total_segments:03d}.{extension}"


def prepare_metadata(
    original_metadata: Dict[str, str],
    segment_number: int,
    total_segments: int,
    duration: float,
    original_filename: str
) -> Dict[str, str]:
    """Prepare metadata for a video segment, preserving original S3 metadata."""
    metadata = {}
    if "Metadata" in original_metadata:
        metadata = dict(original_metadata["Metadata"])
    
    # Add segment-specific metadata
    metadata["segment_number"] = str(segment_number)
    metadata["total_segments"] = str(total_segments)
    metadata["segment_duration"] = f"{duration:.2f}"
    metadata["original_video"] = original_filename
    metadata["segment_type"] = "video_segment"
    
    return metadata

