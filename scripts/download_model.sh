#!/bin/bash

# Download BGE Small Embedding Model
# This script downloads the BGE small embedding model in GGUF format

set -e

MODEL_NAME="bge-small-en-v1.5"
MODEL_FILE="${MODEL_NAME}.gguf"
MODEL_URL="https://huggingface.co/Embedding-GGUF/${MODEL_NAME}/resolve/main/${MODEL_FILE}"
MODELS_DIR="./scanner/models"

echo "Downloading BGE Small Embedding Model..."
echo "Model: ${MODEL_NAME}"
echo "URL: ${MODEL_URL}"
echo "Destination: ${MODELS_DIR}/${MODEL_FILE}"

# Create models directory if it doesn't exist
mkdir -p "${MODELS_DIR}"

# Download the model
if command -v wget >/dev/null 2>&1; then
    echo "Using wget to download model..."
    wget -O "${MODELS_DIR}/${MODEL_FILE}" "${MODEL_URL}"
elif command -v curl >/dev/null 2>&1; then
    echo "Using curl to download model..."
    curl -L -o "${MODELS_DIR}/${MODEL_FILE}" "${MODEL_URL}"
else
    echo "Error: Neither wget nor curl is available"
    exit 1
fi

# Verify the model was downloaded
if [ -f "${MODELS_DIR}/${MODEL_FILE}" ]; then
    echo "✅ Model downloaded successfully!"
    echo "File size: $(du -h "${MODELS_DIR}/${MODEL_FILE}" | cut -f1)"
    echo "Location: ${MODELS_DIR}/${MODEL_FILE}"
else
    echo "❌ Failed to download model"
    exit 1
fi

echo ""
echo "Model download completed. The scanner service can now use local embeddings."
echo "Model configuration:"
echo "  - Model: ${MODEL_NAME}"
echo "  - Embedding dimension: 384"
echo "  - File size: ~33MB"
echo "  - Backend: llama.cpp (GGUF)"