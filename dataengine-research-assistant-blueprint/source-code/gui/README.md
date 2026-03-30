# Research Assistant Frontend

An Angular web application that provides the chat interface for the Research Assistant.

## What It Does

- **Chat Interface**: Conversational UI for asking questions across document collections
- **Collection Selection**: Choose which document collection to query
- **Tool Visibility**: See RAG retrieval results, citations, and tool execution in real-time
- **Document Upload**: Upload single or multiple documents (or entire directories) to collections
- **Conversation History**: Browse and resume previous chat sessions
- **Internet Search Toggle**: Enable/disable web search augmentation
- **System Prompt Editor**: Customize the agent's system prompt per session
- **Architecture Blueprint**: Visual diagram of the system architecture

## Easy to Adjust

### Frontend Configuration

Configuration is managed via environment variables injected at build time and the backend API:

- **Backend API**: All data comes from the backend REST API (`/api/v1/`)
- **Proxy**: Nginx proxies API requests to the backend service

### User Settings (Browser Storage)

Users can customize in the UI:
- **Collection**: Select which document collection to search
- **Internet Search**: Toggle DuckDuckGo web search
- **System Prompt**: Custom instructions for the AI agent

### Build Configuration

Edit `angular.json` or `package.json` for:
- Build output directory
- Development server port
- Production build optimizations

## About the Application

- **Framework**: Angular 19
- **UI Library**: Angular Material
- **State Management**: Services with Angular Signals
- **Streaming**: fetch() + ReadableStream for real-time token delivery
- **Markdown**: ngx-markdown for rendering AI responses
- **Features**:
  - Chat page with streaming responses and tool blocks
  - Citation display with source titles and links
  - Upload dialog with multi-file and directory support
  - Sidebar with conversation history
  - Collection selector with auto-selection

## What Runs It

- **Runtime**: Nginx web server (containerized)
- **Image**: Built from `source-code/gui/Dockerfile`
- **Deployment**: Kubernetes deployment (see [k8s-application](../../deployments/k8s-application/README.md))
- **Build**: Angular CLI builds static files served by Nginx
- **Dependencies**: Node.js for build, Nginx for serving
