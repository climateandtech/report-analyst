#!/bin/sh
set -eu

UPSTREAM="${UPSTREAM:-http://report-analyst:8080}"
export UPSTREAM

HTPASSWD="/etc/nginx/.htpasswd"
TEMPLATE="/etc/nginx/templates/default.conf.template"
CONFIG="/etc/nginx/conf.d/default.conf"

if [ -n "${HTTP_BASIC_AUTH_USERNAME:-}" ] && [ -n "${HTTP_BASIC_AUTH_PASSWORD:-}" ]; then
  htpasswd -cb "$HTPASSWD" "$HTTP_BASIC_AUTH_USERNAME" "$HTTP_BASIC_AUTH_PASSWORD"
  echo "HTTP basic auth enabled for user ${HTTP_BASIC_AUTH_USERNAME}"
else
  # Pass-through when credentials are not configured (local dev).
  cat >"$CONFIG" <<EOF
server {
    listen 8080;
    server_name _;
    location / {
        proxy_pass ${UPSTREAM};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
EOF
  exec nginx -g 'daemon off;'
fi

envsubst '${UPSTREAM}' <"$TEMPLATE" >"$CONFIG"
exec nginx -g 'daemon off;'
