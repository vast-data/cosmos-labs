# VAST Agents GUI

Angular-based frontend application for VAST Agents platform.

## Tech Stack

- **Angular** 18.2
- **Angular Material** 18.2
- **TypeScript** 5.5
- **SCSS** for styling
- **RxJS** 7.8
- **ngx-markdown** for Markdown rendering
- **PrismJS** for code syntax highlighting

## Prerequisites

- **Node.js** >= 18.x
- **npm** >= 9.x

## Installation

```bash
cd gui/angular
npm install
```

## Development Server

### Quick Start

```bash
npm run start
```

Navigate to `http://localhost:4200/`. The application will automatically reload on source file changes.

### With Custom Backend

By default, the dev server proxies API requests to `http://v151lg1:8001`. To use a different backend:

1. Edit `src/proxy.conf.js` and update the `target` URLs
2. Restart the dev server

## Proxy Configuration

The proxy configuration is defined in `src/proxy.conf.js`. It forwards API requests from the Angular dev server to the backend server, avoiding CORS issues during development.

### Default Configuration

```javascript
const PROXY_CONFIG = {
  "/users": {
    "target": "http://v151lg1:8001",
    "secure": false,
    "logLevel": "info",
    "headers": {'Access-Control-Allow-Origin': '*'}
  },
  "/token": {
    "target": "http://v151lg1:8001",
    "secure": false,
    "logLevel": "info",
    "headers": {'Access-Control-Allow-Origin': '*'}
  },
  "/api/v1": {
    "target": "http://v151lg1:8001",
    "secure": false,
    "logLevel": "info",
    "headers": {'Access-Control-Allow-Origin': '*'}
  },
};
```

### How to Change Proxy Target

1. Open `src/proxy.conf.js`
2. Update the `target` value for each endpoint group:
   ```javascript
   "/api/v1": {
     "target": "http://localhost:8001",  // Your backend URL
     "secure": false,
     "logLevel": "info",
     "headers": {'Access-Control-Allow-Origin': '*'}
   }
   ```
3. Restart the dev server

### Proxy Log Levels

Available log levels for debugging proxy issues:
- `silent` - No logs
- `error` - Only errors
- `warn` - Warnings and errors
- `info` - General information (default)
- `debug` - Detailed debug output

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run start` | Start development server |
| `npm run build` | Build for production |
| `npm run build-prod` | Build for production with output to `/gui_dist` |
| `npm run watch` | Build and watch for changes |
| `npm run test` | Run unit tests |
| `npm run lint` | Run ESLint |
| `npm run lint:fix` | Run ESLint with auto-fix |

## Build

### Development Build

```bash
npm run build
```

Build artifacts are stored in `dist/gui/`.

### Production Build

```bash
npm run build-prod
```

Production build with optimizations, output to `/gui_dist`.

## Environment Configuration

Environment files are located in `src/environments/`:

| File | Purpose |
|------|---------|
| `environment.ts` | Base environment (default) |
| `environment.development.ts` | Development configuration |
| `environment.prod.ts` | Production configuration |

### API Base URL

Configure the API base URL in the environment files:

```typescript
export const environment = {
  production: false,
  base_API_URL: 'http://localhost:8000'
};
```

## Project Structure

```
src/
├── app/
│   ├── features/           # Feature modules
│   │   ├── auth/           # Authentication (login, guards, interceptors)
│   │   ├── collections/    # Collections management
│   │   ├── conversation/   # Chat/conversation components
│   │   ├── reports/        # Reports and sessions
│   │   ├── sessions/       # Session management
│   │   ├── shared/         # Shared components, services, pipes
│   │   └── sources/        # Data sources management
│   └── pages/              # Page layouts
├── assets/                 # Static assets
├── environments/           # Environment configurations
└── styles/                 # Global SCSS styles
```

## Features

- **Collections** - Create and manage document collections
- **Sources** - Upload and manage data sources
- **Sessions** - AI conversation sessions
- **Reports** - View and interact with AI-generated reports
- **Authentication** - User login with JWT token handling

## Troubleshooting

### Proxy Not Working

1. Verify the backend is running at the configured target URL
2. Check `src/proxy.conf.js` for correct endpoint mappings
3. Set `"logLevel": "debug"` to see detailed proxy logs
4. Restart the dev server after configuration changes

### CORS Issues

If you encounter CORS errors:
1. Ensure the proxy is configured correctly in `src/proxy.conf.js`
2. API calls should use relative paths (e.g., `/api/v1/...`) not absolute URLs

### Build Errors

```bash
# Clear node_modules and reinstall
rm -rf node_modules
npm install
```
