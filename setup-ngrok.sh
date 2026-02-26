#!/bin/bash

# ngrok Setup Script for Gerrys-Game
# This script helps you quickly set up ngrok for hosting the app

BACKEND_URL="$1"
ENV_LOCAL_PATH="./frontend/.env.local"

echo "========================================"
echo "ngrok Setup Script - Gerrys-Game"
echo "========================================"
echo ""

# Function to parse ngrok URL and extract domain and protocol
parse_ngrok_url() {
    local url="$1"
    
    # Remove https:// or http://
    local domain="${url#https://}"
    domain="${domain#http://}"
    
    # Remove port if present
    domain="${domain%:*}"
    
    # Determine protocol (default to https)
    if [[ "$url" == http://* ]]; then
        echo "http|$domain|80"
    else
        echo "https|$domain|443"
    fi
}

if [ -n "$BACKEND_URL" ]; then
    echo "Parsing ngrok URL: $BACKEND_URL"
    IFS='|' read -r protocol domain port <<< "$(parse_ngrok_url "$BACKEND_URL")"
    
    echo "Updating .env.local with ngrok backend URL..."
    echo "Backend: $protocol://$domain:$port"
    
    cat > "$ENV_LOCAL_PATH" <<EOF
# Local development environment variables
# ngrok backend URL (https with port 443)
VUE_APP_BACKEND_IP=$domain
VUE_APP_BACKEND_PORT=$port
VUE_APP_BACKEND_PROTOCOL=$protocol
EOF
    
    echo ".env.local updated successfully!"
else
    echo "MANUAL NGROK SETUP GUIDE"
    echo ""
    echo "Step 1: Start ngrok tunnels"
    echo "=============================="
    echo "Terminal 1 (Backend):"
    echo "  cd backend"
    echo "  python run.py"
    echo ""
    echo "Terminal 2 (Frontend):"
    echo "  cd frontend"
    echo "  npm run serve"
    echo ""
    echo "Terminal 3 (ngrok for backend):"
    echo "  ngrok http 5000"
    echo ""
    echo "Step 2: Copy the ngrok URL"
    echo "=============================="
    echo "From the ngrok output, copy the Forwarding URL (https://...)"
    echo ""
    echo "Step 3: Update environment or run this script"
    echo "=============================="
    echo "Either:"
    echo "  Option A - Edit $ENV_LOCAL_PATH manually"
    echo ""
    echo "  Option B - Run this script with your ngrok URL:"
    echo "  ./setup-ngrok.sh 'https://xxxx-xx-xxx-xx-xxxx.ngrok.io'"
    echo ""
    echo "EXAMPLE .env.local for ngrok:"
    echo "=============================="
    echo "VUE_APP_BACKEND_IP=xxxx-xx-xxx-xx-xxxx.ngrok.io"
    echo "VUE_APP_BACKEND_PORT=443"
    echo "VUE_APP_BACKEND_PROTOCOL=https"
    echo ""
    echo "Note: ngrok uses HTTPS and port 443 by default!"
fi

echo ""
echo "========================================"
echo "Setup complete! The frontend will now use the configured backend URL."
echo "========================================"
