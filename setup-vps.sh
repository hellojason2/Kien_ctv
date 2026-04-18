#!/bin/bash
set -e

# CTV VPS Full Setup Script
# Run this on your new VPS as root or a sudo user
# IMPORTANT: Set GOOGLE_CREDS_JSON and GROQ_API_KEY env vars before running,
# or edit this script to include them.

APP_DIR="${APP_DIR:-/opt/ctv}"
USER="${USER:-$(whoami)}"

echo "=== CTV VPS Setup ==="
echo "App dir: $APP_DIR"
echo "User: $USER"

# Check required secrets
if [ -z "$GOOGLE_CREDS_JSON" ]; then
    echo "ERROR: Set GOOGLE_CREDS_JSON environment variable before running."
    echo "  export GOOGLE_CREDS_JSON='{...your google service account json...}'"
    exit 1
fi
if [ -z "$GROQ_API_KEY" ]; then
    echo "ERROR: Set GROQ_API_KEY environment variable before running."
    echo "  export GROQ_API_KEY='gsk_...'"
    exit 1
fi

# 1. System deps
echo "[1/8] Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y git python3 python3-pip python3-venv redis-server postgresql postgresql-contrib nginx

# 2. Create app directory
echo "[2/8] Setting up app directory..."
sudo mkdir -p "$APP_DIR"
sudo chown "$USER:$USER" "$APP_DIR"

# 3. Clone repo
echo "[3/8] Cloning repository..."
if [ -d "$APP_DIR/.git" ]; then
    cd "$APP_DIR"
    git pull origin main
else
    git clone https://github.com/hellojason2/Kien_ctv.git "$APP_DIR"
    cd "$APP_DIR"
fi

# 4. Virtualenv & dependencies
echo "[4/8] Installing Python dependencies..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 5. Create google_credentials.json
echo "[5/8] Creating Google credentials file..."
echo "$GOOGLE_CREDS_JSON" > "$APP_DIR/google_credentials.json"

# 6. Create .env
echo "[6/8] Creating .env file..."
cat > "$APP_DIR/.env" << ENV_EOF
PORT=2002
DATABASE_URL=postgresql://ctv_user:ctv_password@localhost/ctv_db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=ctv-secret-key-$(openssl rand -hex 16)
GROQ_API_KEY=${GROQ_API_KEY}
ENV_EOF

# 7. Setup PostgreSQL DB
echo "[7/8] Setting up PostgreSQL database..."
sudo systemctl start postgresql
sudo -u postgres psql -c "CREATE USER ctv_user WITH PASSWORD 'ctv_password';" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE ctv_db OWNER ctv_user;" 2>/dev/null || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ctv_db TO ctv_user;" 2>/dev/null || true

# 8. Install systemd services
echo "[8/8] Installing systemd services..."

sudo tee /etc/systemd/system/ctv-web.service > /dev/null << EOF
[Unit]
Description=CTV Web Server
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn backend:app --bind 0.0.0.0:\${PORT} --timeout 300 --workers 2 --threads 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/ctv-worker.service > /dev/null << EOF
[Unit]
Description=CTV Sync Worker
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/python sync_worker.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ctv-web ctv-worker
sudo systemctl start ctv-web ctv-worker

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Services status:"
sudo systemctl status ctv-web --no-pager
sudo systemctl status ctv-worker --no-pager
echo ""
echo "App running on port 2002"
echo ""
echo "Next steps:"
echo "  - Set up Nginx reverse proxy (see nginx-ctv.conf)"
echo "  - Run database migrations if needed"
echo "  - Configure your domain and SSL (Certbot)"
