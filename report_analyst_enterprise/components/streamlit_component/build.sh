#!/bin/bash
# Build script for Streamlit JSON Schema Form component

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

echo "Building Streamlit JSON Schema Form component..."
echo "Frontend directory: $FRONTEND_DIR"

cd "$FRONTEND_DIR"

# Check if node_modules exists, if not install
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Build the component
echo "Building component..."
npm run build

if [ -d "build" ]; then
    echo "✓ Component built successfully!"
    echo "Build directory: $FRONTEND_DIR/build"
else
    echo "✗ Build failed - build directory not found"
    exit 1
fi


