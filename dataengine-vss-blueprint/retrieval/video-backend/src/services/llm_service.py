"""
LLM Service for generating AI summaries using NVIDIA API

Note: System prompt is now managed by the frontend and sent with each request.
The backend no longer requires a ConfigMap for the system prompt.
"""
import httpx
import time
import os
from typing import List, Dict, Optional
from src.config import get_settings


# Fallback system prompt (only used if frontend doesn't send one)
DEFAULT_SYSTEM_PROMPT = """Always use relevant Emojis in every line in your response!
Role: You are a witty, sharp-eyed Video Analyst. Your primary goal is to answer the user's specific question accurately using the video data.

The Rules:

Direct Answer First: Start immediately with a clear, direct answer to the user's question. No fluff.

Contextual Vibe Check: Follow the answer with a 1-sentence snarky or relatable observation about the scene (e.g., "Standard city chaos—everyone’s in a rush.").

The Evidence (Play-by-Play): Always show the timestamp for each segment (use the exact Timestamp given for each segment, e.g. "At 14:32" or "22 Feb 2025 14:32"). Provide short, titled chapters. Only include segments that are relevant to the user's question or provide necessary context. Use bold for the action.

Human Commentary: Be opinionated but brief. If a driver is being aggressive or a logo is distinct, call it out. ALWAYS ! Use relevant emojis sparingly !

TL;DR: One punchy sentence which is addressing the user query simply and right away."""


class LLMService:
    """Service for interacting with NVIDIA LLM API"""
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.nvidia_api_key
        self.base_url = f"{self.settings.llm_http_scheme}://{self.settings.llm_host}:{self.settings.llm_port}"
        self.model_name = self.settings.llm_model_name
        self.timeout = self.settings.llm_timeout_seconds
        # Default prompt is only used as fallback if frontend doesn't send one
        self.default_prompt = DEFAULT_SYSTEM_PROMPT
        print(f"[LLM] Service initialized (prompt will be provided by frontend)")
    
    def synthesize_search_results(
        self, 
        query: str, 
        top_results: List[Dict],
        custom_system_prompt: Optional[str] = None
    ) -> Dict:
        """
        Generate AI synthesis from search results
        
        Args:
            query: User's search query
            top_results: List of search results with summaries (already limited by search API)
            custom_system_prompt: System prompt from frontend (uses default fallback if not provided)
            
        Returns:
            Dict containing synthesis response and metadata
        """
        start_time = time.time()
        
        # Use all provided results (limiting is now done by the search API using llm_top_n)
        top_n = len(top_results)
        
        if top_n == 0:
            return {
                "response": "No video segments found to analyze.",
                "segments_used": 0,
                "segments_analyzed": [],
                "model": self.model_name,
                "tokens_used": 0,
                "processing_time": 0.0,
                "error": None
            }
        
        # Determine which system prompt to use
        # Priority: prompt from frontend > hardcoded default fallback
        effective_prompt = custom_system_prompt.strip() if custom_system_prompt and custom_system_prompt.strip() else self.default_prompt
        
        # Prepare summaries for LLM
        summaries_text = self._format_summaries(top_results[:top_n])
        
        # Construct user message
        user_message = f"""User Query: {query}

Video Segment Summaries:
{summaries_text}

Please synthesize this information to answer the user's query."""
        
        try:
            # Call NVIDIA API with the effective system prompt
            response_data = self._call_llm_api(user_message, system_prompt=effective_prompt)
            
            processing_time = time.time() - start_time
            
            # Extract segment names for reference
            segment_names = [
                f"{r.get('original_video', 'Unknown')} (segment {r.get('segment_number', '?')})"
                for r in top_results[:top_n]
            ]
            
            return {
                "response": response_data.get("content", ""),
                "segments_used": top_n,
                "segments_analyzed": segment_names,
                "model": self.model_name,
                "tokens_used": response_data.get("tokens_used", 0),
                "processing_time": round(processing_time, 2),
                "error": None
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            print(f"LLM API error: {error_msg}")
            
            # Extract segment names even on error
            segment_names = [
                f"{r.get('original_video', 'Unknown')} (segment {r.get('segment_number', '?')})"
                for r in top_results[:top_n]
            ]
            
            return {
                "response": f"Failed to generate AI synthesis: {error_msg}",
                "segments_used": top_n,
                "segments_analyzed": segment_names,
                "model": self.model_name,
                "tokens_used": 0,
                "processing_time": round(processing_time, 2),
                "error": error_msg
            }
    
    def _format_summaries(self, results: List[Dict]) -> str:
        """Format video summaries for LLM input with timestamps and segment information so the LLM can reference real times."""
        formatted = []
        for i, result in enumerate(results, 1):
            summary = result.get("summary", "No summary available")
            original_video = result.get("original_video", "Unknown video")
            segment_num = result.get("segment_number", "?")
            total_segments = result.get("total_segments", "?")
            filename = result.get("filename", result.get("source", "Unknown").split('/')[-1])
            score = result.get("similarity_score", 0)
            # Human-readable timestamp so the LLM can say "At 14:32" or "22 Feb 2025 14:32"
            upload_ts = result.get("upload_timestamp")
            if upload_ts is not None:
                try:
                    if hasattr(upload_ts, "strftime"):
                        ts_str = upload_ts.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        ts_str = str(upload_ts)[:19].replace("T", " ")
                except Exception:
                    ts_str = str(upload_ts)[:19] if upload_ts else "?"
            else:
                ts_str = "?"
            header = (
                f"Segment {i}: {original_video} (segment {segment_num}/{total_segments}) "
                f"[match: {score:.1%}] | Timestamp: {ts_str}"
            )
            formatted.append(f"{header}\n{summary}")
        return "\n\n".join(formatted)
    
    def _call_llm_api(self, user_message: str, system_prompt: Optional[str] = None) -> Dict:
        """
        Call NVIDIA LLM API
        
        Args:
            user_message: The user message to send to the LLM
            system_prompt: System prompt to use (uses hardcoded default if not provided)
            
        Returns:
            Dict with content and token usage
        """
        url = f"{self.base_url}/v1/chat/completions"
        
        # Use provided system prompt or fall back to default
        effective_system_prompt = system_prompt if system_prompt else self.default_prompt
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": effective_system_prompt
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "temperature": 0.2,
            "top_p": 0.7,
            "max_tokens": 300,
            "stream": False
        }
        
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract content and token usage
            content = ""
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0].get("message", {}).get("content", "")
            
            tokens_used = data.get("usage", {}).get("total_tokens", 0)
            
            return {
                "content": content,
                "tokens_used": tokens_used
            }


# Global LLM service instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create global LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service

