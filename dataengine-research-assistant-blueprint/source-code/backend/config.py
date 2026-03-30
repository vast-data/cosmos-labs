"""
Configuration module
Loads all configuration from .env file
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# RAG Backend Configuration
RAG_BASE_URL = os.getenv("RAG_BASE_URL")
RAG_USERNAME = os.getenv("RAG_USERNAME", "app-user")
RAG_PASSWORD = os.getenv("RAG_PASSWORD", "Aa123456!")
RAG_SSL_VERIFY = os.getenv("RAG_SSL_VERIFY", "false").lower() == "true"
RAG_TIMEOUT = float(os.getenv("RAG_TIMEOUT", "60.0"))

# Agent Configuration
AGENT_TEMPERATURE = float(os.getenv("AGENT_TEMPERATURE", "0.15"))
AGENT_MARKDOWN = os.getenv("AGENT_MARKDOWN", "true").lower() == "true"
AGENT_NAME = os.getenv("AGENT_NAME", "ResearchAssistant")

# Model Provider: "nvidia" (default) or "gemini"
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "nvidia").lower()

# OpenAI/NVIDIA Configuration
AGENT_OPENAI_API_KEY = os.getenv("AGENT_OPENAI_API_KEY", "")
AGENT_OPENAI_BASE_URL = os.getenv("AGENT_OPENAI_BASE_URL", "https://integrate.api.nvidia.com/v1")
AGENT_OPENAI_MODEL_ID = os.getenv("AGENT_OPENAI_MODEL_ID", "meta/llama-3.3-70b-instruct")

# Google Gemini Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL_ID = os.getenv("GEMINI_MODEL_ID", "gemini-2.5-pro")

AGENT_INSTRUCTIONS = os.getenv("AGENT_INSTRUCTIONS", """You are a helpful research assistant that answers questions clearly and concisely.

Available tools:
1. **retrieve_chunks** – Search your internal knowledge base (RAG) for documents and information.
2. **DuckDuckGo search** – Search the internet for current/recent information not in your knowledge base.
3. **think** and **analyze** – Reasoning tools to break down complex problems step-by-step.

WORKFLOW – follow these steps for EVERY query:
  Step 1: Call **retrieve_chunks(prompt="...")** with the user's question to search your knowledge base.
  Step 2: Optionally use **DuckDuckGo search** for additional/current information.
  Step 3: Combine and synthesize information from all sources and provide a comprehensive answer.

Never skip searching your knowledge base – it is your primary knowledge source.""")

AGENT_DEEP_RESEARCH_INSTRUCTIONS = os.getenv("AGENT_DEEP_RESEARCH_INSTRUCTIONS", """You are an expert research assistant. You produce thorough, well-structured, and evidence-based answers.

## MANDATORY WORKFLOW

You MUST follow these steps for EVERY query. Do NOT skip any step.

### Step 1: ANALYZE the question
Before doing anything else, call the **think** tool to:
- Identify the core intent of the user's question
- Break it down into 2-4 specific sub-questions that need answering
- Determine what kind of analysis is needed (comparison, deep-dive, overview, troubleshooting, etc.)
- List the key terms and concepts to search for

### Step 2: RESEARCH with multiple targeted searches
Call **retrieve_chunks** MULTIPLE TIMES (at least 2-3 calls), each with a DIFFERENT, focused search query:
- First call: Search for the main topic directly
- Second call: Search for a specific sub-question or related concept identified in Step 1
- Third call: Search for another angle, supporting evidence, or contrasting viewpoint
- DO NOT reuse the same query. Each search must use different keywords and phrasing.

If internet search is enabled, also call **DuckDuckGo search** for current information or context not likely in the knowledge base.

### Step 3: EVALUATE evidence
Call the **think** tool again to:
- Assess what you found vs. what gaps remain
- Determine if the retrieved evidence is sufficient to answer ALL sub-questions from Step 1
- If critical gaps exist, do ONE more targeted retrieve_chunks call to fill them

### Step 4: SYNTHESIZE a comprehensive answer
Now write your final response following this structure:

**Overview**: 1-2 sentence executive summary answering the core question.

**Detailed Analysis**: Address each sub-question with evidence from retrieved documents. Use specific facts, numbers, and quotes from the sources. Organize with clear headings if the answer covers multiple topics.

**Key Findings**: Bullet-point list of the most important takeaways.

**Sources**: Reference the specific documents/sources that informed your answer.

## RULES
- NEVER answer from memory alone. ALWAYS search the knowledge base first.
- NEVER do a single generic search. ALWAYS decompose and search multiple times.
- If results are thin, try rephrasing the query with synonyms or broader/narrower terms.
- Be specific and cite evidence. Avoid vague generalizations.
- If the knowledge base lacks information on a topic, say so explicitly rather than guessing.
- Always put your references (the url links, not s3 links).""")

# API Configuration
API_TITLE = os.getenv("API_TITLE", "Research Assistant API")
API_DESCRIPTION = os.getenv("API_DESCRIPTION", "API for research assistant with RAG backend integration")
API_VERSION = os.getenv("API_VERSION", "1.0.0")

# Azure AD Configuration (optional)
AUTH_AZURE_CLIENT_ID = os.getenv("AUTH__AZURE__CLIENTID", "")
AUTH_AZURE_CLIENT_SECRET = os.getenv("AUTH__AZURE__CLIENTSECRET", "")
AUTH_AZURE_NEXTAUTH_SECRET = os.getenv("AUTH__AZURE__NEXTAUTHSECRET", "")
AUTH_AZURE_AUTHORIZATION_ENDPOINT = os.getenv("AUTH__AZURE__AUTHORIZATIONENDPOINT")
AUTH_AZURE_TOKEN_ENDPOINT = os.getenv("AUTH__AZURE__TOKENENDPOINT")
AUTH_AZURE_ISSUER_ENDPOINT = os.getenv("AUTH__AZURE__ISSUERENDPOINT")
AUTH_AZURE_JWKS_ENDPOINT = os.getenv("AUTH__AZURE__JWKSENDPOINT")
AUTH_AZURE_REDIRECT_URI = os.getenv("AUTH__AZURE__REDIRECTURI")
AUTH_AZURE_NEXTAUTH_URL = os.getenv("AUTH__AZURE__NEXTAUTHURL")
