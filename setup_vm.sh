#!/bin/bash
# Run this on the Ubuntu VM as root or with sudo
# Sets up Python face service + cleans unused Docker resources

set -e
echo "======================================================"
echo "  FACEPAY VM SETUP"
echo "======================================================"

# ── 1. CLEAN UP UNUSED DOCKER RESOURCES ────────────────
echo ""
echo "[1/5] Cleaning unused Docker images and containers..."
docker stop $(docker ps -aq) 2>/dev/null || true
docker rm $(docker ps -aq) 2>/dev/null || true
docker rmi $(docker images -q --filter "dangling=true") 2>/dev/null || true
docker system prune -f 2>/dev/null || true
echo "Done."

# ── 2. INSTALL SYSTEM DEPS ──────────────────────────────
echo ""
echo "[2/5] Installing system dependencies..."
apt-get update -q
apt-get install -y -q \
    python3 python3-pip python3-dev \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 \
    curl git
echo "Done."

# ── 3. INSTALL PYTORCH CPU ─────────────────────────────
echo ""
echo "[3/5] Installing PyTorch (CPU only)..."
pip3 install --quiet torch==2.2.2 --index-url https://download.pytorch.org/whl/cpu
echo "Done."

# ── 4. INSTALL PYTHON PACKAGES ─────────────────────────
echo ""
echo "[4/5] Installing Python packages..."
pip3 install --quiet \
    fastapi==0.136.1 \
    uvicorn==0.47.0 \
    opencv-python-headless==4.9.0.80 \
    numpy==1.26.4 \
    deepface==0.0.100 \
    scipy==1.13.1 \
    pydantic==2.13.4 \
    tf-keras \
    python-multipart
echo "Done."

# ── 5. PRE-DOWNLOAD DEEPFACE MODELS ────────────────────
echo ""
echo "[5/5] Pre-downloading DeepFace models (first run only)..."
python3 - <<'PYEOF'
from deepface import DeepFace
import numpy as np
img = np.zeros((100, 100, 3), dtype=np.uint8)
try:
    DeepFace.extract_faces(img_path=img, anti_spoofing=True, enforce_detection=False)
except Exception as e:
    print("Warmup:", e)
print("Models ready.")
PYEOF

# ── CREATE SYSTEMD SERVICE ──────────────────────────────
echo ""
echo "Creating systemd service for face service..."

APP_DIR="/opt/facepay"
mkdir -p "$APP_DIR/face_dataset"

# Copy face_service.py and haarcascade if running from project directory
if [ -f "./face_service.py" ]; then
    cp face_service.py "$APP_DIR/"
    cp haarcascade_frontalface_alt.xml "$APP_DIR/"
    echo "Copied face_service.py to $APP_DIR"
else
    echo "WARNING: Run this script from the project root so face_service.py gets copied."
fi

cat > /etc/systemd/system/facepay-python.service <<EOF
[Unit]
Description=FacePay Python Face Service
After=network.target

[Service]
Type=simple
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/python3 $APP_DIR/face_service.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable facepay-python
systemctl start facepay-python

echo ""
echo "======================================================"
echo "  SETUP COMPLETE"
echo "  Face service: systemctl status facepay-python"
echo "  Logs:         journalctl -u facepay-python -f"
echo "======================================================"
