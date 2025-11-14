import os
import json
from typing import Any, Optional, Dict, List
from pydantic import BaseModel


class Settings(BaseModel):
    """Configuration settings for safety alerts"""
    
    vdbendpoint: str
    vdbbucket: str
    vdbschema: str
    vdbaccesskey: str
    vdbsecretkey: str
    vdbcollection: str
    
    embeddingmodel: str
    embeddingdimensions: int
    embeddinghost: str
    embeddingport: int
    embeddinghttpscheme: str
    nvidia_api_key: str
    
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_messaging_service_sid: str
    twilio_to_phone: str
    
    alert_queries: List[Dict[str, Any]]
    alert_top_k: int = 5
    default_threshold: float = 0.5
    cooldown_minutes: int = 5
    alert_lookback_minutes: int = 6
    
    alerts_table: str = "safety_alerts"
    
    @classmethod
    def from_ctx_secrets(cls, secrets: Dict[str, str]) -> 'Settings':
        """Load all settings from runtime context secrets"""
        secret_data = secrets["safetyalertssecret"]
        
        alert_queries_str = secret_data.get("alert_queries", "[]")
        alert_queries = json.loads(alert_queries_str) if isinstance(alert_queries_str, str) else alert_queries_str
        
        config = {
            "vdbendpoint": secret_data["vdbendpoint"],
            "vdbbucket": secret_data["vdbbucket"],
            "vdbschema": secret_data["vdbschema"],
            "vdbaccesskey": secret_data["vdbaccesskey"],
            "vdbsecretkey": secret_data["vdbsecretkey"],
            "vdbcollection": secret_data["vdbcollection"],
            
            "embeddingmodel": secret_data["embeddingmodel"],
            "embeddingdimensions": int(secret_data["embeddingdimensions"]),
            "embeddinghost": secret_data["embeddinghost"],
            "embeddingport": int(secret_data["embeddingport"]),
            "embeddinghttpscheme": secret_data["embeddinghttpscheme"],
            "nvidia_api_key": secret_data["nvidia_api_key"],
            
            "twilio_account_sid": secret_data["twilio_account_sid"],
            "twilio_auth_token": secret_data["twilio_auth_token"],
            "twilio_messaging_service_sid": secret_data["twilio_messaging_service_sid"],
            "twilio_to_phone": secret_data["twilio_to_phone"],
            
            "alert_queries": alert_queries,
            "alert_top_k": int(secret_data.get("alert_top_k", 5)),
            "default_threshold": float(secret_data.get("default_threshold", 0.5)),
            "cooldown_minutes": int(secret_data.get("cooldown_minutes", 5)),
            "alert_lookback_minutes": int(secret_data.get("alert_lookback_minutes", 6)),
            "alerts_table": secret_data.get("alerts_table", "safety_alerts")
        }
        
        return cls(**config)

