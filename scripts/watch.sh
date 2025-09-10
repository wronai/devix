#!/bin/bash
# Watch mode - continuous development monitoring
# Monitors file changes and runs Devix analysis automatically

set -e

echo "👀 Watch mode - monitoring file changes..."
echo "Press Ctrl+C to stop watching..."
echo ""

SRC_DIR="src"
PYTHON="python3"

# Function to run analysis
run_analysis() {
    echo "🔄 Changes detected at $(date)"
    echo "Running Devix analysis..."
    
    cd .. 2>/dev/null || true
    PYTHONPATH="$(pwd)/devix/${SRC_DIR}" ${PYTHON} -m devix analyze
    
    echo "✅ Analysis completed"
    echo "---"
}

# Initial analysis
run_analysis

# Watch for changes
while true; do
    echo "Waiting for changes in ${SRC_DIR}/..."
    
    # Try inotifywait first (Linux), then fswatch (macOS), then fallback to polling
    if command -v inotifywait >/dev/null 2>&1; then
        # Linux - use inotifywait
        inotifywait -r -e modify,create,delete "${SRC_DIR}" 2>/dev/null || {
            echo "⚠️  inotifywait failed, falling back to polling..."
            sleep 5
        }
    elif command -v fswatch >/dev/null 2>&1; then
        # macOS - use fswatch  
        fswatch -o "${SRC_DIR}" >/dev/null 2>&1 || {
            echo "⚠️  fswatch failed, falling back to polling..."
            sleep 5
        }
    else
        # Fallback - polling mode
        echo "No file watcher found (inotifywait/fswatch), using polling mode..."
        echo "Install inotify-tools (Linux) or fswatch (macOS) for better performance."
        sleep 5
    fi
    
    run_analysis
    sleep 2  # Brief pause between runs
done
