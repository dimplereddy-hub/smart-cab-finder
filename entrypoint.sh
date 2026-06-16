#!/bin/sh
set -e

mkdir -p /app/.streamlit

cat > /app/.streamlit/secrets.toml <<EOF
GITLAB_URL="${GITLAB_URL:-https://gitlab.com}"
GITLAB_TOKEN="${GITLAB_TOKEN:-}"

[auth]
redirect_uri = "${AUTH_REDIRECT_URI:-https://projects-compliance-checker.apps.swecha.org/oauth2callback}"
cookie_secret = "${AUTH_COOKIE_SECRET:-}"
client_id = "${AUTH_CLIENT_ID:-}"
client_secret = "${AUTH_CLIENT_SECRET:-}"
server_metadata_url = "${AUTH_SERVER_METADATA_URL:-https://code.swecha.org/.well-known/openid-configuration}"
EOF

exec streamlit run app.py
