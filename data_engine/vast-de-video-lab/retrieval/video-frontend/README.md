# Video Reasoning GUI

Modern Angular 18 frontend for Video Reasoning Lab with AI-powered semantic search.

## Features

- 🔐 **VAST Authentication** - Secure login with VAST credentials
- 🔍 **Semantic Search** - Natural language video search with AI
- 🎬 **Video Player** - Segment playback with reasoning summaries
- ⬆️ **Video Upload** - Drag & drop with permission control
- ✨ **AI Animations** - Visual effects for search process
- 🎨 **Cosmic Theme** - Modern glassmorphism design

## Tech Stack

- Angular 18 (standalone components)
- Angular Material
- TypeScript 5
- RxJS 7
- SCSS

## Prerequisites

- Node.js 18+
- npm or yarn

## Installation

```bash
# Install dependencies
npm install
```

## Development

```bash
# Start development server (with proxy to backend)
npm start

# Opens at http://localhost:4200
# API requests proxied to http://localhost:8000
```

Make sure backend is running at `http://localhost:8000` before starting!

## Build

```bash
# Production build
npm run build

# Output in dist/video-gui/
```

## Docker

```bash
# Build image
docker build -t video-frontend:latest .

# Run container
docker run -p 80:80 video-frontend:latest
```

## Project Structure

```
src/
├── app/
│   ├── features/
│   │   ├── auth/              # Authentication
│   │   │   ├── components/
│   │   │   │   └── login/    # Login page
│   │   │   ├── services/      # Auth service
│   │   │   ├── guards/        # Route guards
│   │   │   └── interceptors/  # Token interceptor
│   │   ├── search/            # Search feature
│   │   │   ├── components/
│   │   │   │   ├── search-bar.component.ts
│   │   │   │   ├── video-card.component.ts
│   │   │   │   └── search-animation.component.ts
│   │   │   ├── services/      # Search service
│   │   │   └── search-page.component.ts
│   │   ├── player/            # Video player
│   │   │   └── video-player.component.ts
│   │   └── upload/            # Upload feature
│   │       └── upload-dialog.component.ts
│   ├── shared/
│   │   ├── models/            # TypeScript interfaces
│   │   ├── services/          # Video service
│   │   └── settings.ts        # App constants
│   ├── app.component.ts       # Root component
│   ├── app.config.ts          # App providers
│   └── app.routes.ts          # Routing
├── environments/              # Environment configs
├── assets/                    # Static assets
└── styles.scss               # Global styles
```

## Features Detail

### Authentication
- **Login page** with VAST credentials
- **JWT token** management
- **Route guards** for protected pages
- **Auth interceptor** for API requests

### Search
- **Search bar** with query input
- **AI animation** showing:
  - Embedding generation (NVIDIA NIM)
  - Vector search (VastDB)
  - Permission filtering
- **Results grid** with video cards
- **Similarity scores** displayed
- **Tags filtering**
- **Public/private** indicators

### Video Player
- **Modal player** with controls
- **Segment navigation** (previous/next)
- **Reasoning panel** showing Cosmos summary
- **Metadata display** (owner, tags, duration)
- **Auto-load** streaming URL from backend

### Upload
- **Drag & drop** file upload
- **Permission settings**:
  - Public (all users)
  - Private (owner only)
  - Shared (specific users)
- **Tags** for categorization
- **Progress tracking**
- **S3 presigned** URL upload

### AI Animations
- **Embedding phase** - Text to vector conversion
- **Search phase** - Vector similarity computation
- **Filtering phase** - Permission checks
- **Complete phase** - Results summary with timings

## Configuration

### Development Proxy

`src/proxy.conf.js` proxies API requests to backend:

```javascript
{
  "/api": {
    "target": "http://localhost:8000",
    "secure": false,
    "changeOrigin": true
  }
}
```

### Environments

**Development:** `src/environments/environment.development.ts`
```typescript
export const environment = {
  production: false,
  apiUrl: '/api/v1'
};
```

**Production:** `src/environments/environment.ts`
```typescript
export const environment = {
  production: true,
  apiUrl: '/api/v1'  // Served through ingress
};
```

## Deployment

### Kubernetes

```bash
# Build image
docker build -t video-frontend:latest .

# Deploy
kubectl apply -f ../k8s/frontend-deployment.yaml

# Check status
kubectl get pods -n ie-collections -l app=video-frontend
```

### Nginx Configuration

The `nginx.conf` file:
- Serves Angular SPA
- Handles routing
- Proxies `/api/` to backend
- Caches static assets

## Styling

### Theme Colors

- **Primary:** `#667eea` (purple gradient)
- **Accent:** `#06ffa5` (cyan)
- **Background:** `#0f0f1e` (dark cosmic)
- **Text:** `#fff` (white)

### Design System

- **Glassmorphism** cards with backdrop blur
- **Gradients** for buttons and headers
- **Smooth animations** (300ms ease)
- **Material Design** components
- **Responsive** grid layouts

## API Integration

All API calls go through `VideoService`:

```typescript
// Search
search(request: SearchRequest): Observable<SearchResponse>

// Stream video
getStreamUrl(source: string): Observable<{stream_url: string}>

// Upload
requestUpload(filename: string, metadata: UploadRequest): Observable<UploadResponse>
uploadToS3(url: string, file: File, fields: any): Observable<any>
```

## Testing

```bash
# Run tests
npm test

# With coverage
npm run test -- --coverage
```

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Troubleshooting

### Backend Not Responding

Check proxy configuration in `proxy.conf.js` and ensure backend is running:

```bash
curl http://localhost:8000/health
```

### Build Errors

Clear cache and reinstall:

```bash
rm -rf node_modules package-lock.json
npm install
```

### CORS Issues

Backend must include frontend origin in CORS settings:

```python
cors_origins=["http://localhost:4200", "https://video-lab.vastdata.com"]
```

## Contributing

1. Follow Angular style guide
2. Use standalone components
3. Implement Material Design
4. Add proper TypeScript types
5. Write unit tests
6. Update documentation

## License

Proprietary - VAST Data

---

**Built with ❤️ for VAST Data Insight Engine**

