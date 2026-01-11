# Video Frontend

An Angular web application that provides the user interface for the Video Reasoning Lab system.

## What It Does

- **Video Search**: Semantic search across processed video segments using natural language queries
- **Video Upload**: Upload videos with metadata (camera_id, capture_type, neighborhood)
- **Video Playback**: Play video segments with reasoning text overlays
- **User Authentication**: Login with VAST credentials (username + S3 secret key)
- **Settings Management**: Configure LLM settings, system prompts, and video streaming
- **Metadata Filtering**: Filter search results by camera, location, capture type, and time

## Easy to Adjust

### Frontend Configuration

Configuration is managed via the backend service. The frontend reads configuration from:
- **Backend API**: `/api/v1/config` endpoint provides frontend configuration
- **Settings**: Stored in `retrieval/k8s/frontend-config.yaml` ConfigMap

### User Settings (Browser Storage)

Users can customize these settings in the UI (stored in browser localStorage):

- **Advanced LLM Settings**: LLM analysis count, max search results, minimum similarity threshold
- **System Prompt**: Custom LLM system prompt for search result synthesis
- **Time Filters**: Preset or custom date ranges for filtering

### Build Configuration

Edit `angular.json` or `package.json` for:
- Build output directory
- Development server port
- Production build optimizations

## About the Application

- **Framework**: Angular 18
- **UI Library**: Angular Material
- **State Management**: Services with RxJS observables
- **Authentication**: JWT tokens stored in localStorage
- **API Communication**: REST API calls to backend service
- **Features**:
  - Search page with vector search and LLM synthesis
  - Upload dialog with metadata input
  - Video player with segment navigation
  - Settings dialogs for customization
  - Streaming service integration

## What Runs It

- **Runtime**: Nginx web server (containerized)
- **Image**: `vastdatasolutions/vde-video-frontend:v1`
- **Deployment**: Kubernetes deployment (see main README Part 2)
- **Access**: Via ingress at `http://video-lab.<cluster_name>.vastdata.com`
- **Build**: Angular CLI builds static files served by Nginx
- **Dependencies**: Node.js for build, Nginx for serving

