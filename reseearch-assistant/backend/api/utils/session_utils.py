"""
Utility functions for session management
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def generate_summary_from_prompt(agent, prompt: str) -> str:
    """
    Generate a chat summary from the first prompt using the agent.
    
    Uses a simple system prompt: "your job is to make chat summary based on this prompt"
    
    Args:
        agent: The agent instance
        prompt: The user's first prompt
        
    Returns:
        A summary string (can be longer than title, typically 1-2 sentences)
    """
    try:
        # Create a simple agent for summarization with the user's requested system prompt
        from agno.agent import Agent
        
        summary_agent = Agent(
            model=agent.model,  # Use the same model as the main agent
            instructions="Your job is to make a short, concise chat summary based on this prompt. It needs to be the title of the session. It should be no more than a sentence.",
            tools=[],  # No tools needed for summarization
            add_history_to_context=False,
            db=None  # No DB needed for this temporary agent
        )
        
        # Create a more specific prompt for summarization
        summary_prompt = f"Create a short title (one sentence maximum) for this user question: {prompt}"
        
        # Run the summary agent with the summary prompt
        summary_result = summary_agent.run(summary_prompt, stream=False)
        
        # Extract the summary from the response
        if hasattr(summary_result, 'content'):
            summary = summary_result.content
            if isinstance(summary, str):
                summary = summary.strip()
            elif isinstance(summary, list):
                # Extract text from content blocks
                text_parts = []
                for block in summary:
                    if isinstance(block, dict) and block.get('type') == 'text':
                        text_parts.append(block.get('text', ''))
                    elif isinstance(block, str):
                        text_parts.append(block)
                summary = ' '.join(text_parts).strip()
            else:
                summary = str(summary).strip()
            
            # Clean up the summary (remove quotes)
            summary = summary.strip('"\'')
            
            # Limit summary length - take first 200 characters or first sentence
            if summary:
                # Try to get first sentence if it's too long
                if len(summary) > 200:
                    # Find first sentence ending
                    sentence_endings = ['.', '!', '?']
                    first_sentence_end = -1
                    for ending in sentence_endings:
                        idx = summary.find(ending)
                        if idx != -1 and (first_sentence_end == -1 or idx < first_sentence_end):
                            first_sentence_end = idx
                    
                    if first_sentence_end != -1 and first_sentence_end < 200:
                        summary = summary[:first_sentence_end + 1].strip()
                    else:
                        # Just truncate at 200 chars
                        summary = summary[:197].strip() + "..."
                
                logger.info(f"Successfully generated summary ({len(summary)} chars): {summary[:100]}...")
                return summary
        
        # Fallback: use the prompt itself as summary
        logger.warning("Could not extract summary from result, using prompt as fallback")
        return prompt[:200] + "..." if len(prompt) > 200 else prompt
    except Exception as e:
        logger.warning(f"Failed to generate summary from prompt: {e}", exc_info=True)
        # Fallback: use the prompt itself as summary
        return prompt[:200] + "..." if len(prompt) > 200 else prompt

