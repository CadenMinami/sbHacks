#!/bin/bash

# YAPBATTLE Startup Script
# Make sure to set your API keys as environment variables before running:
#   export ANTHROPIC_API_KEY='your-anthropic-key'
#   export DEEPGRAM_API_KEY='your-deepgram-key'

echo "🎤 Starting YAPBATTLE..."

# Check if API keys are set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ ERROR: ANTHROPIC_API_KEY environment variable not set"
    echo "Please run: export ANTHROPIC_API_KEY='your-key-here'"
    exit 1
fi

if [ -z "$DEEPGRAM_API_KEY" ]; then
    echo "❌ ERROR: DEEPGRAM_API_KEY environment variable not set"
    echo "Please run: export DEEPGRAM_API_KEY='your-key-here'"
    exit 1
fi

echo "✅ API keys configured"
echo "🚀 Starting server on http://localhost:5001"
echo ""

# Kill any existing process on port 5001
lsof -ti:5001 | xargs kill -9 2>/dev/null || true

# Start the Flask server
python3 app.py
