#!/bin/bash
echo "🚀 Starting Nifty Options Dashboard..."
cd "$(dirname "$0")"
source venv/bin/activate
python3 src/web/app.py
