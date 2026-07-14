#!/bin/bash
# ☿ AZOTH — Deploy harness to S20FE over WiFi (SSH/SCP)
# Run from your Linux machine: bash deploy_to_phone.sh <phone-ip>
#
# Prerequisites on phone (do once in Termux):
#   pkg install openssh
#   sshd                    ← starts SSH server on port 8022
#   passwd                  ← set a password
#
# Then find phone IP: Settings → About phone → Status → IP address
# Or: ip addr show wlan0 | grep "inet "

set -e

PHONE_IP="${1:-}"
PHONE_PORT="8022"
PHONE_USER="$(whoami)"
REMOTE_DIR="/data/data/com.termux/files/home/AZOTH"
LOCAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -z "$PHONE_IP" ]; then
    echo "Usage: bash deploy_to_phone.sh <phone-ip>"
    echo "Example: bash deploy_to_phone.sh 192.168.1.45"
    echo ""
    echo "Find phone IP in Termux: ip addr show wlan0 | grep 'inet '"
    exit 1
fi

echo "☿ AZOTH → S20FE"
echo "  From: $LOCAL_DIR"
echo "  To:   $PHONE_USER@$PHONE_IP:$REMOTE_DIR"
echo ""

# Create remote dir
ssh -p "$PHONE_PORT" "$PHONE_USER@$PHONE_IP" "mkdir -p $REMOTE_DIR"

# Sync harness files — exclude .env, __pycache__, .git, sessions, crashes
rsync -avz --progress \
    --exclude='.env' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.git/' \
    --exclude='sessions/' \
    --exclude='crashes/' \
    --exclude='snapshots/' \
    --exclude='*.db' \
    -e "ssh -p $PHONE_PORT" \
    "$LOCAL_DIR/" \
    "$PHONE_USER@$PHONE_IP:$REMOTE_DIR/"

echo ""
echo "✓ Harness deployed."
echo ""
echo "On the phone:"
echo "  cd $REMOTE_DIR"
echo "  bash setup_termux.sh"
echo "  # then add your API keys to .env"
echo "  sol"
echo ""
echo "NOTE: .env was NOT synced — copy keys manually (security)."
echo "  On phone: nano $REMOTE_DIR/.env"
