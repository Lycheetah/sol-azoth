#!/data/data/com.termux/files/usr/bin/bash
# ☿ AZOTH — Termux setup for Samsung S20FE (or any Android)
# Run this ONCE after copying the harness to your phone.
# Mac + Sol · June 27 2026

set -e

echo "☿ AZOTH — Termux setup"
echo "─────────────────────────────────"

# 1 — Core packages
echo "[1/5] Installing packages..."
pkg update -y -q
pkg install -y python git termux-api 2>/dev/null

# 2 — Python deps
echo "[2/5] Installing Python deps..."
pip install --quiet openai rich

# 3 — .env check
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "[3/5] Creating .env — you need to fill in your keys"
    cat > "$ENV_FILE" << 'EOF'
# AZOTH keys — fill these in
DEEPSEEK_KEY=sk-your-deepseek-key-here
NVIDIA_KEY=nvapi-your-nvidia-key-here
GEMINI_KEY=your-gemini-key-here
EOF
    echo "      ⚠  Edit $ENV_FILE and add your API keys, then re-run."
    echo "      Keys are in ~/.env on your Linux machine."
else
    echo "[3/5] .env found ✓"
fi

# 4 — Termux notification permission
echo "[4/5] Requesting notification permission..."
termux-notification --title "☿ AZOTH" --content "Setup complete. Sol is here." 2>/dev/null || \
    echo "      (Install Termux:API from F-Droid for notifications)"

# 5 — sol alias in Termux .bashrc
BASHRC="$HOME/.bashrc"
if ! grep -q "AZOTH" "$BASHRC" 2>/dev/null; then
    echo "" >> "$BASHRC"
    echo "# ☿ AZOTH — Sol in your pocket" >> "$BASHRC"
    echo "alias sol=\"bash $SCRIPT_DIR/launch_vael.sh\"" >> "$BASHRC"
    echo "[5/5] Added 'sol' alias to ~/.bashrc ✓"
    echo "      Run: source ~/.bashrc"
else
    echo "[5/5] sol alias already present ✓"
fi

echo ""
echo "─────────────────────────────────"
echo "☿ Setup complete."
echo ""
echo "Next:"
echo "  1. Edit .env with your API keys (copy from Linux machine)"
echo "  2. source ~/.bashrc"
echo "  3. sol"
echo ""
echo "Sol speaks. VAEL builds. Mac holds the heat."
