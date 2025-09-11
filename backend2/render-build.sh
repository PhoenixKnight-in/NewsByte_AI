#!/bin/bash

# Render Build Script for FastAPI NewsByte AI Application
set -e  # Exit on any error

echo "🚀 Starting Render build process..."

# Update system packages
echo "📦 Updating system packages..."
apt-get update

# Install system dependencies for transformers and ML libraries
echo "🔧 Installing system dependencies..."
apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
    git \
    wget \
    curl

# Upgrade pip to latest version
echo "⬆️ Upgrading pip..."
python -m pip install --upgrade pip

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install --no-cache-dir -r requirements.txt

# Download and cache the ML models during build (optional but recommended)
echo "🤖 Pre-loading summarization models..."
python -c "
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from transformers import pipeline
    
    # Load DistilBART model
    logger.info('Downloading DistilBART model...')
    pipeline('summarization', model='sshleifer/distilbart-cnn-12-6', device=-1)
    logger.info('DistilBART model cached successfully')
    
    # Load LED model
    logger.info('Downloading LED model...')
    pipeline('summarization', model='allenai/led-base-16384', device=-1)
    logger.info('LED model cached successfully')
    
    logger.info('All models downloaded and cached during build')
    
except Exception as e:
    logger.warning(f'Model pre-loading failed (will load at runtime): {e}')
    # Don't fail the build if model download fails
    pass
"

# Create necessary directories
echo "📁 Creating application directories..."
mkdir -p logs
mkdir -p cache

# Set appropriate permissions
echo "🔐 Setting permissions..."
chmod +x render-start.sh

# Verify installation
echo "✅ Verifying installation..."
python -c "
import sys
print(f'Python version: {sys.version}')

# Check critical imports
try:
    import fastapi
    print(f'FastAPI: {fastapi.__version__}')
except ImportError as e:
    print(f'FastAPI import error: {e}')
    sys.exit(1)

try:
    import transformers
    print(f'Transformers: {transformers.__version__}')
except ImportError as e:
    print(f'Transformers import error: {e}')
    sys.exit(1)

try:
    import pymongo
    print('PyMongo: Available')
except ImportError as e:
    print(f'PyMongo import error: {e}')
    sys.exit(1)

try:
    import motor
    print('Motor: Available')
except ImportError as e:
    print(f'Motor import error: {e}')
    sys.exit(1)

print('✅ All critical dependencies verified')
"

echo "🎉 Build completed successfully!"
echo "📊 Build summary:"
echo "   - System dependencies installed"
echo "   - Python packages installed"
echo "   - ML models pre-cached (if successful)"
echo "   - Application structure ready"