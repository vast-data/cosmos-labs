# Research Assistant Backend

FastAPI-based agent service powered by LLMs and RAG (InsightEngine).

## What It Does

- **RAG-Powered Q&A**: Retrieves relevant document chunks from collections and generates comprehensive answers
- **Streaming Responses**: Real-time SSE streaming of agent responses with tool execution visibility
- **Session Management**: Conversation history stored in VastDB with session persistence
- **Internet Search**: Optional DuckDuckGo integration for supplementing knowledge base answers
- **Authentication**: JWT-based auth with optional Azure AD integration

## Easy to Adjust

### Agent Configuration

Environment variables control agent behavior:

| Variable | Description | Default |
|----------|-------------|---------|
| `AGENT_OPENAI_BASE_URL` | LLM API endpoint | `https://integrate.api.nvidia.com/v1` |
| `AGENT_OPENAI_MODEL_ID` | Model to use | `meta/llama-3.3-70b-instruct` |
| `AGENT_TEMPERATURE` | Response creativity | `0.15` |
| `AGENT_INSTRUCTIONS` | System prompt | Built-in RAG workflow prompt |

### RAG Backend

| Variable | Description | Default |
|----------|-------------|---------|
| `RAG_BASE_URL` | InsightEngine backend URL | `http://backend-webserver.research-assistant:8080` |
| `RAG_TIMEOUT` | Request timeout (seconds) | `60.0` |

### VastDB Storage

| Variable | Description |
|----------|-------------|
| `VASTDB_ENDPOINT` | VastDB endpoint URL |
| `VASTDB_ACCESS_KEY` | VastDB access key |
| `VASTDB_SECRET_KEY` | VastDB secret key |

## About the Application

- **Framework**: FastAPI with async SSE streaming
- **Agent Framework**: Agno (tool-based LLM agent)
- **Tools**: `retrieve_chunks` (RAG), DuckDuckGo search, reasoning tools
- **Storage**: VastDB for session/conversation persistence
- **Auth**: JWT tokens, optional Azure AD

## What Runs It

- **Runtime**: Python 3.11+ (containerized)
- **Image**: Built from `source-code/backend/Dockerfile`
- **Deployment**: Kubernetes deployment (see [k8s-application](../../deployments/k8s-application/README.md))
- **Dependencies**: See `requirements.txt`
