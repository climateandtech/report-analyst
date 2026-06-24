#!/bin/sh
# Optional HTTP Basic Auth in front of Streamlit. Credentials from Coolify app env
# (HTTP_BASIC_AUTH_USERNAME / HTTP_BASIC_AUTH_PASSWORD). When unset, proxies without auth.
set -eu

UPSTREAM="${UPSTREAM_HOST:-report-analyst}:${UPSTREAM_PORT:-8080}"
AUTH_FILE=/etc/nginx/auth.htpasswd
CONF=/etc/nginx/conf.d/default.conf

if [ -n "${HTTP_BASIC_AUTH_USERNAME:-}" ] && [ -n "${HTTP_BASIC_AUTH_PASSWORD:-}" ]; then
  htpasswd -nbB "$HTTP_BASIC_AUTH_USERNAME" "$HTTP_BASIC_AUTH_PASSWORD" > "$AUTH_FILE"
  AUTH_DIRECTIVES="auth_basic \"Report Analyst\";
        auth_basic_user_file ${AUTH_FILE};"
else
  rm -f "$AUTH_FILE"
  AUTH_DIRECTIVES=""
fi

cat > "$CONF" <<EOF
server {
    listen 8080;
    location /health {
        auth_basic off;
        return 200 'ok';
        add_header Content-Type text/plain;
    }
    location / {
        ${AUTH_DIRECTIVES}
        proxy_pass http://${UPSTREAM};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400;
    }
}
EOF

exec nginx -g 'daemon off;'
