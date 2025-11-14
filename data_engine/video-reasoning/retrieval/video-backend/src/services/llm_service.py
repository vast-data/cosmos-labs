"""
LLM Service for generating AI summaries using NVIDIA API
"""
import httpx
import time
import os
from typing import List, Dict, Optional
from src.config import get_settings


class LLMService:
    """Service for interacting with NVIDIA LLM API"""
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.nvidia_api_key
        self.base_url = f"{self.settings.llm_http_scheme}://{self.settings.llm_host}:{self.settings.llm_port}"
        self.model_name = self.settings.llm_model_name
        self.timeout = self.settings.llm_timeout_seconds
        self.system_prompt = self._load_system_prompt()
        
    def _load_system_prompt(self) -> str:
        """Load system prompt from ConfigMap file"""
        try:
            prompt_path = self.settings.system_prompt_path
            if os.path.exists(prompt_path):
                with open(prompt_path, 'r') as f:
                    return f.read().strip()
            else:
                # Fallback to default prompt
                return """You are an AI assistant helping users find relevant information from a video surveillance database. 
You will receive a user's search query and summaries of the top most relevant video segments.
Synthesize the information and provide a concise, helpful answer (under 200 words).
Be factual and based only on the provided summaries."""
        except Exception as e:
            print(f"Warning: Failed to load system prompt from {self.settings.system_prompt_path}: {e}")
            return "You are an AI assistant. Synthesize the provided video summaries to answer the user's query concisely."
    
    def synthesize_search_results(
        self, 
        query: str, 
        top_results: List[Dict],
        top_n: Optional[int] = None
    ) -> Dict:
        """
        Generate AI synthesis from search results
        
        Args:
            query: User's search query
            top_results: List of search results with summaries
            top_n: Number of results to use (defaults to config setting)
            
        Returns:
            Dict containing synthesis response and metadata
        """
        start_time = time.time()
        
        # Use configured top N if not specified
        if top_n is None:
            top_n = self.settings.llm_top_n_summaries
        
        # Limit to available results
        top_n = min(top_n, len(top_results))
        
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
        
        # Prepare summaries for LLM
        summaries_text = self._format_summaries(top_results[:top_n])
        
        # Construct user message
        user_message = f"""User Query: {query}

Video Segment Summaries:
{summaries_text}

Please synthesize this information to answer the user's query."""
        
        try:
            # Call NVIDIA API
            response_data = self._call_llm_api(user_message)
            
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
        """Format video summaries for LLM input with detailed segment information"""
        formatted = []
        for i, result in enumerate(results, 1):
            summary = result.get("summary", "No summary available")
            original_video = result.get("original_video", "Unknown video")
            segment_num = result.get("segment_number", "?")
            filename = result.get("filename", result.get("source", "Unknown").split('/')[-1])
            score = result.get("similarity_score", 0)
            
            # Format: Segment X: video_name.mp4 (segment Y) [score: Z%]
            header = f"Segment {i}: {original_video} (segment {segment_num}) [match: {score:.1%}]"
            formatted.append(f"{header}\n{summary}")
        
        return "\n\n".join(formatted)
    
    def _call_llm_api(self, user_message: str) -> Dict:
        """
        Call NVIDIA LLM API
        
        Args:
            user_message: The user message to send to the LLM
            
        Returns:
            Dict with content and token usage
        """
        url = f"{self.base_url}/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": self.system_prompt
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

