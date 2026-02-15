#!/bin/bash
# ═══════════════════════════════════════════════════════
#  AutoMemeBot — Server Setup Script
#  Run on a fresh Ubuntu 22.04 VPS
# ═══════════════════════════════════════════════════════

set -e

echo "=== 1. System Update ==="
apt update && apt upgrade -y

echo "=== 2. Install Docker ==="
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker

echo "=== 3. Install Docker Compose ==="
apt install -y docker-compose-plugin

echo "=== 4. Install Python 3.11 ==="
apt install -y python3.11 python3.11-venv python3-pip git

echo "=== 5. Create project directory ==="
mkdir -p /opt/automemebot
cd /opt/automemebot

echo "=== 6. Create virtual environment ==="
python3.11 -m venv venv
source venv/bin/activate

echo ""
echo "═══════════════════════════════════════════════"
echo "  Server is ready!"
echo ""
echo "  Next steps:"
echo "  1. Upload project files to /opt/automemebot/"
echo "  2. cp .env.example .env && nano .env"
echo "  3. docker compose up -d"
echo "  4. source venv/bin/activate"
echo "  5. pip install -r requirements.txt"
echo "  6. python main.py"
echo "═══════════════════════════════════════════════"
