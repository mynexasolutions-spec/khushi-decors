#!/bin/bash
set -e

SERVER="ec2-user@ec2-13-200-255-139.ap-south-1.compute.amazonaws.com"
PEM="deploy-guide/nexa-solutions.pem"
REMOTE_DIR="/home/ec2-user/khushi-decors"
SERVICE="khushi-decors"

echo "==> Pulling latest code on server..."
ssh -i "$PEM" "$SERVER" \
  "cd $REMOTE_DIR && \
   git pull origin main && \
   source venv/bin/activate && \
   pip install -r requirements.txt && \
   sudo systemctl restart $SERVICE && \
   sleep 3 && \
   sudo systemctl is-active $SERVICE"

echo "✅ Deployed!"
