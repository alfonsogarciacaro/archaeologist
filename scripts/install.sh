#!/bin/bash

if ! command -v uv &> /dev/null; then
    echo "❌ uv not found. Please install uv first:"
    echo "   pip install uv"
    echo "   or visit: https://github.com/astral-sh/uv"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ npm not found. Please install Node.js and npm first."
    exit 1
fi

echo "📦 Installing dependencies..."
cd api && uv sync --locked && cd ..
cd scanner && uv sync --locked && cd ..
cd ui && npm ci && cd ..