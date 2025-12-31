import logging
from typing import Dict, Any


def parse_reasoning_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse reasoning event data from video-reasoner
    
    Args:
        event_data: Raw event data from VastEvent (CloudEvent from video-reasoner)
    
    Returns:
        Parsed reasoning event dict
    """
    logging.info(f"[PARSER] Parsing reasoning event: {event_data}")
    
    # Validate required fields
    required_fields = ["source", "filename", "reasoning_content"]
    for field in required_fields:
        if field not in event_data:
            raise ValueError(f"Missing required field '{field}' in reasoning event")
    
    logging.info(f"[PARSER] Parsed reasoning event - filename: {event_data['filename']}, content_length: {len(event_data.get('reasoning_content', ''))}")
    
    return event_data


def validate_reasoning_content(reasoning_content: str) -> bool:
    """
    Validate reasoning content is not empty
    
    Args:
        reasoning_content: The reasoning text
    
    Returns:
        True if valid, False otherwise
    """
    if not reasoning_content or len(reasoning_content.strip()) == 0:
        logging.warning("[VALIDATOR] Reasoning content is empty")
        return False
    
    logging.info(f"[VALIDATOR] Reasoning content is valid ({len(reasoning_content)} characters)")
    return True

