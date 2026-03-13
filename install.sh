#!/bin/bash

# AI Robot OS - Installation Script for Raspberry Pi
echo "🚀 Starting Installation of AI Robot OS..."

# 1. Update System
echo "🔄 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# 2. Install System Dependencies
echo "📦 Installing system dependencies..."
sudo apt install -y python3-venv python3-pip libglib2.0-0 libgl1-mesa-glx libhdf5-dev libqt5gui5 libqt5test5 libavcodec-dev libavformat-dev libswscale-dev libv4l-dev libxvidcore-dev libx264-dev portaudio19-dev

# 3. Create Virtual Environment
echo "🐍 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# 4. Install Python Requirements
echo "📥 Installing python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# 5. Setup Desktop Shortcut & Autostart
echo "🖥️ Creating desktop shortcut and enabling autostart..."
mkdir -p ~/.config/autostart
cp airobot.desktop ~/Desktop/
cp airobot.desktop ~/.config/autostart/
chmod +x ~/Desktop/airobot.desktop
chmod +x ~/.config/autostart/airobot.desktop

# 6. Setup Systemd Service (Optional for background tasks)
echo "⚙️ Setting up background service..."
sudo bash -c "cat <<EOF > /etc/systemd/system/airobot.service
[Unit]
Description=AI Robot Operating System
After=multi-user.target

[Service]
Type=simple
User=pi
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF"

sudo systemctl daemon-reload
# sudo systemctl enable airobot.service # Uncomment if you want it as a system service too

echo "✅ Installation Complete!"
echo "📍 Please update your .env file with your API keys before running."
