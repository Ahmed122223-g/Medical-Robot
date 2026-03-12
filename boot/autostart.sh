#!/bin/bash
# ============================================
# AI Robot OS - Boot Script
# نظام تشغيل الروبوت الطبي الذكي - سكريبت الإقلاع
# ============================================
# This script is used to auto-start the AI Robot OS
# on Raspberry Pi boot.
#
# Installation:
# 1. Copy this script to /home/pi/mariam_pro/AI/boot/
# 2. Make it executable: chmod +x autostart.sh
# 3. Add to /etc/rc.local or create a systemd service
#
# Systemd service example (/etc/systemd/system/airobot.service):
# [Unit]
# Description=AI Robot Operating System
# After=multi-user.target
#
# [Service]
# Type=simple
# User=pi
# WorkingDirectory=/home/pi/mariam_pro/AI
# ExecStart=/home/pi/mariam_pro/AI/boot/autostart.sh
# Restart=always
# RestartSec=5
#
# [Install]
# WantedBy=multi-user.target
#
# Enable with: sudo systemctl enable airobot.service
# ============================================

# Set display for GUI
export DISPLAY=:0

# Navigate to project directory
cd /home/pi/mariam_pro/AI

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Wait for display to be ready
sleep 5

# Start the application
python3 main.py --fullscreen

# Keep running if fails
while true; do
    echo "AI Robot OS exited. Restarting in 5 seconds..."
    sleep 5
    python3 main.py --fullscreen
done
