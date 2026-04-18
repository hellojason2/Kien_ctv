#!/bin/bash
set -e

echo "=== CTV Deploy Script ==="

# Config
APP_DIR="${APP_DIR:-/opt/ctv}"
REPO="https://github.com/hellojason2/Kien_ctv.git"
PYTHON="python3"

# 1. Update code
echo "[1/5] Pulling latest code..."
if [ -d "$APP_DIR/.git" ]; then
    cd "$APP_DIR"
    git pull origin main
else
    git clone "$REPO" "$APP_DIR"
    cd "$APP_DIR"
fi

# 2. Install/update dependencies
echo "[2/5] Installing dependencies..."
$PYTHON -m pip install -r requirements.txt --quiet

# 3. Check/create .env if missing
echo "[3/5] Checking environment..."
if [ ! -f ".env" ]; then
    echo "WARNING: .env not found. Creating template..."
    cat > .env << 'EOF'
PORT=2002
DATABASE_URL=postgresql://user:pass@localhost/ctv_db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-me-in-production
EOF
    echo "EDIT .env BEFORE RUNNING IN PRODUCTION!"
fi

# 4. Restart services (if systemd)
echo "[4/5] Restarting services..."
if command -v systemctl &> /dev/null; then
    sudo systemctl restart ctv-web 2>/dev/null || echo "  ctv-web service not found (run install-services.sh)"
    sudo systemctl restart ctv-worker 2>/dev/null || echo "  ctv-worker service not found"
else
    echo "  systemd not available. Start manually with:"
    echo "    gunicorn backend:app --bind 0.0.0.0:\$PORT --timeout 300 --workers 2 --threads 4"
    echo "    python sync_worker.py"
fi

echo "[5/5] Deploy complete!"
