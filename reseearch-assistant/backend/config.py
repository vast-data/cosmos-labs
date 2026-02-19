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

# OpenAI/NVIDIA Configuration
AGENT_OPENAI_API_KEY = os.getenv("AGENT_OPENAI_API_KEY", "")
AGENT_OPENAI_BASE_URL = os.getenv("AGENT_OPENAI_BASE_URL", "https://integrate.api.nvidia.com/v1")
AGENT_OPENAI_MODEL_ID = os.getenv("AGENT_OPENAI_MODEL_ID", "meta/llama-3.3-70b-instruct")

AGENT_INSTRUCTIONS = os.getenv("AGENT_INSTRUCTIONS", """You are a helpful research assistant that answers questions clearly and concisely.

Available tools:
1. **hybrid_query** – Analyse the user prompt and split it into metadata filters and a similarity query. This is an analysis step ONLY (it does NOT retrieve documents).
2. **retrieve_chunks** – Search your internal knowledge base (RAG). Accepts both a prompt AND an optional metadata_query. ALWAYS use this after hybrid_query.
3. **DuckDuckGo search** – Search the internet for current/recent information not in your knowledge base.
4. **think** and **analyze** – Reasoning tools to break down complex problems step-by-step.

CRITICAL WORKFLOW – follow these steps for EVERY query:
  Step 1: Call **hybrid_query(similarity_query="...", filters="...")**
          Analyse ONLY the CURRENT user message. Extract any filterable attributes into filters
          and put the rest into similarity_query.
          IMPORTANT: Do NOT carry over filters from previous messages in the conversation.
          Each query must be analysed independently based ONLY on what the user wrote NOW.
          If the current message mentions no file_type, author, year, etc., filters MUST be "".
  Step 2: Call **retrieve_chunks(prompt=<similarity_query from step 1>, filters=<same filters string from step 1>)**
          This performs the actual document retrieval. Pass the SAME filters string, NOT the metadata_query.
  Step 3: Optionally use **DuckDuckGo search** for additional/current information.
  Step 4: Combine and synthesize information from all sources and provide a comprehensive answer.

Supported filter fields (use these friendly names – the system maps them to the correct JSON keys):
  file_type, author (maps to source-owner), year (maps to source-creation-time),
  category, department, language, title (maps to source-title), source, tags,
  creation_time (maps to source-creation-time), modified (maps to source-last-modified)

Supported operators: =, <, >, <=, >=, !=

The filters parameter is a simple comma-separated list of field{operator}value expressions:
  - "file_type=pdf"
  - "author=Yuval Peretz"   (this filters by source-owner)
  - "year>2024"             (documents created after 2024)
  - "year<2020"             (documents created before 2020)
  - "file_type=pdf, year>=2025"
The system converts these into the correct SQL syntax automatically.

If the user's CURRENT message has NO filterable attributes, pass filters as "" (empty string).
Do NOT reuse filters from earlier messages unless the user explicitly asks to.

Do NOT include the metadata_query in your text response — it is automatically shown to the user in the UI.

Never skip searching your knowledge base – it is your primary knowledge source.""")

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
