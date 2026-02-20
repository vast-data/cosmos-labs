#!/bin/sh
# Custom entrypoint for nginx to handle cache directory permissions

# Create temp directories for nginx cache (using /tmp which is writable)
mkdir -p /tmp/nginx_proxy
mkdir -p /tmp/nginx_client
mkdir -p /tmp/nginx_fastcgi
mkdir -p /tmp/nginx_uwsgi
mkdir -p /tmp/nginx_scgi
mkdir -p /var/run

# Execute the original nginx entrypoint with nginx command
exec /docker-entrypoint.sh "$@"

