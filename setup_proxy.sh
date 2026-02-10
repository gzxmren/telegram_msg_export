#!/bin/bash
# Check if python-socks is installed
if ! pip show python-socks > /dev/null 2>&1; then
    echo "Installing python-socks[asyncio]..."
    pip install "python-socks[asyncio]"
fi

# Ask for proxy details
read -p "Enter Proxy Host (e.g. 127.0.0.1): " PROXY_HOST
read -p "Enter Proxy Port (e.g. 7890): " PROXY_PORT
read -p "Enter Proxy Type (SOCKS5/HTTP, default SOCKS5): " PROXY_TYPE
PROXY_TYPE=${PROXY_TYPE:-SOCKS5}
read -p "Enter Proxy Username (optional): " PROXY_USER
read -p "Enter Proxy Password (optional): " PROXY_PASS

# Append to .env
echo "" >> .env
echo "# Proxy Configuration" >> .env
echo "PROXY_HOST=$PROXY_HOST" >> .env
echo "PROXY_PORT=$PROXY_PORT" >> .env
echo "PROXY_TYPE=$PROXY_TYPE" >> .env
if [ -n "$PROXY_USER" ]; then
    echo "PROXY_USER=$PROXY_USER" >> .env
fi
if [ -n "$PROXY_PASS" ]; then
    echo "PROXY_PASS=$PROXY_PASS" >> .env
fi

echo "Proxy configuration added to .env"
