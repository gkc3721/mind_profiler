#!/bin/bash

echo "🔍 Zenin EEG Packaging - Pre-flight Check"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Run this script from the zenin_mac2 root directory"
    exit 1
fi

echo "✅ Directory structure OK"

# Check if venv exists
if [ ! -d "backend/venv" ]; then
    echo "❌ Error: backend/venv not found. Run: cd backend && python3 -m venv venv && pip install -r requirements.txt"
    exit 1
fi

echo "✅ Virtual environment exists"

# Check if launcher script exists
if [ ! -f "backend/run_zenin_app.py" ]; then
    echo "❌ Error: backend/run_zenin_app.py not found"
    exit 1
fi

echo "✅ Launcher script exists"

# Check if frontend is built
if [ ! -d "frontend/dist" ]; then
    echo "⚠️  Warning: frontend/dist not found"
    echo "   Build it with: cd frontend && npm run build"
    NEED_BUILD=1
else
    echo "✅ Frontend build exists"
fi

# Check if dist has index.html
if [ -f "frontend/dist/index.html" ]; then
    echo "✅ Frontend index.html found"
else
    if [ ! $NEED_BUILD ]; then
        echo "⚠️  Warning: frontend/dist/index.html not found"
        echo "   Build it with: cd frontend && npm run build"
        NEED_BUILD=1
    fi
fi

echo ""
echo "=========================================="

if [ $NEED_BUILD ]; then
    echo "⚠️  Action needed: Build the frontend"
    echo ""
    echo "Run these commands:"
    echo "  cd frontend"
    echo "  npm run build"
    echo "  cd .."
    echo ""
else
    echo "✅ All checks passed!"
    echo ""
    echo "Ready to package! Next steps:"
    echo ""
    echo "1. Test the launcher:"
    echo "   cd backend"
    echo "   source venv/bin/activate"
    echo "   python run_zenin_app.py"
    echo ""
    echo "2. Create .app launcher (see QUICK_START_PACKAGING.md)"
    echo ""
fi
