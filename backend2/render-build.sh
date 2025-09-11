#!/bin/bash

# Render Start Script for FastAPI NewsByte AI Application
set -e  # Exit on any error

echo "Starting FastAPI NewsByte AI Application..."

# Set environment variables for production
export PYTHONUNBUFFERED=1
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Set FastAPI/Uvicorn specific settings
export HOST=${HOST:-"0.0.0.0"}
export PORT=${PORT:-"10000"}
export WORKERS=${WORKERS:-"1"}

# Log environment info
echo "Environment Configuration:"
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  Workers: $WORKERS"
echo "  Python Path: $PYTHONPATH"

# Verify critical environment variables
if [ -z "$MONGO_URI" ]; then
    echo "WARNING: MONGO_URI environment variable not set"
    echo "Please set it in your Render environment variables"
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Check if main application file exists
if [ ! -f "main.py" ]; then
    echo "ERROR: main.py not found in $(pwd)"
    echo "Contents of current directory:"
    ls -la
    exit 1
fi

# Test imports before starting server
echo "Testing critical imports..."
python -c "
import sys
import traceback

def test_import(module_name):
    try:
        __import__(module_name)
        print(f'✅ {module_name}: OK')
        return True
    except ImportError as e:
        print(f'❌ {module_name}: FAILED - {e}')
        return False
    except Exception as e:
        print(f'⚠️  {module_name}: ERROR - {e}')
        return False

critical_modules = [
    'fastapi',
    'uvicorn',
    'motor.motor_asyncio',
    'pymongo',
    'transformers',
    'torch',
    'jose',
    'passlib',
    'python_dotenv'
]

failed = []
for module in critical_modules:
    if not test_import(module):
        failed.append(module)

if failed:
    print(f'❌ Failed to import: {failed}')
    sys.exit(1)
else:
    print('✅ All critical modules imported successfully')
"

# Start the FastAPI application with Uvicorn
echo "Starting Uvicorn server..."
echo "Command: uvicorn main:app --host $HOST --port $PORT --workers $WORKERS"

# Use exec to replace the shell process with uvicorn
exec uvicorn main:app \
    --host "$HOST" \
    --port "$PORT" \
    --workers "$WORKERS" \
    --timeout-keep-alive 30 \
    --access-log \
    --log-level info \
    --loop uvloop