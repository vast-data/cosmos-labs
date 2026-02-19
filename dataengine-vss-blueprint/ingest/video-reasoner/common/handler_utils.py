import logging
from typing import Dict, Any, Tuple
from urllib.parse import unquote


def parse_s3_event(event_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Parse S3 event data to extract bucket and key
    
    Args:
        event_data: Raw event data from VastEvent
    
    Returns:
        Dict with 'bucket', 'key', and 'event_name'
    """
    logging.info(f"[PARSER] Parsing S3 event: {event_data}")
    
    # Handle different event formats
    if "Records" in event_data:
        # Standard S3 event format
        record = event_data["Records"][0]
        s3_info = record.get("s3", {})
        bucket = s3_info.get("bucket", {}).get("name", "")
        key = s3_info.get("object", {}).get("key", "")
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
    
    logging.info(f"[PARSER] Parsed S3 event - bucket: {bucket}, key: {key}, event: {event_name}")
    return {
        "bucket": bucket,
        "key": key,
        "event_name": event_name
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
    
    # Must be MP4 file
    if not key.lower().endswith('.mp4'):
        return False, f"Not an MP4 file - skipping (key: {key})"
    
    # Must be a segment (avoid processing original videos)
    if not ("_segment_" in key.lower() or "-segment-" in key.lower() or "/segments/" in key.lower()):
        return False, "Not a segment - skipping (only process segments)"
    
    return True, ""

