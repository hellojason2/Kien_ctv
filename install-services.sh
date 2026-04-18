#!/bin/bash
set -e

APP_DIR="${APP_DIR:-/opt/ctv}"
USER="${USER:-root}"

# Create systemd service for web server
cat > /etc/systemd/system/ctv-web.service << EOF
[Unit]
Description=CTV Web Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
Environment=PORT=2002
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn backend:app --bind 0.0.0.0:\${PORT} --timeout 300 --workers 2 --threads 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for worker
cat > /etc/systemd/system/ctv-worker.service << EOF
[Unit]
Description=CTV Sync Worker
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/python sync_worker.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ctv-web ctv-worker

echo "Services installed. Start with:"
echo "  systemctl start ctv-web ctv-worker"
echo "  systemctl status ctv-web ctv-worker"
