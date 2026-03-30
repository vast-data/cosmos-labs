# Stage 1: Build the Angular application
# Build context should be the gui/ directory
ARG SOURCE_REGISTRY=""
FROM ${SOURCE_REGISTRY}docker.io/library/node:20-alpine AS build

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy the entire project
COPY . .

# Build the application for production
# Set BASE_API_URL environment variable for production build
ENV BASE_API_URL=http://research-assistant:8000
RUN npm run generate-prod-env
RUN npm run build-prod

# Stage 2: Serve the application using nginx
FROM ${SOURCE_REGISTRY}docker.io/library/nginx:1.27.5-alpine

# Remove default nginx website
RUN rm -rf /usr/share/nginx/html/*

# Copy built application from the build stage
# build-prod uses --output-path /gui_dist
COPY --from=build /gui_dist /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy custom entrypoint script
COPY docker-entrypoint.sh /custom-entrypoint.sh
RUN chmod +x /custom-entrypoint.sh

# Expose port 80
EXPOSE 80

# Use custom entrypoint (override nginx's entrypoint)
ENTRYPOINT ["/custom-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
