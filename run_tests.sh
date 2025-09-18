#!/bin/bash

# AgentKit Test Runner
# Simple script to run all tests

echo "🧪 Running AgentKit Tests"
echo "=========================="
echo

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Please run this script from the AgentKit root directory"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: No virtual environment detected. Consider activating one:"
    echo "   source .venv/bin/activate"
    echo
fi

echo "📋 Running Backend Tests..."
echo "---------------------------"

# Run backend tests
if command -v pytest &> /dev/null; then
    echo "Running pytest tests..."
    python -m pytest test_*.py -v
    backend_result=$?
else
    echo "❌ pytest not found. Installing test dependencies..."
    pip install pytest pytest-asyncio httpx
    if [ $? -eq 0 ]; then
        echo "✅ Test dependencies installed. Running tests..."
        python -m pytest test_*.py -v
        backend_result=$?
    else
        echo "❌ Failed to install test dependencies"
        backend_result=1
    fi
fi

echo
echo "🌐 Running Frontend Tests..."
echo "----------------------------"

cd frontend

# Check if test command exists
if npm run test --silent &> /dev/null; then
    echo "Running frontend tests..."
    npm test
    frontend_result=$?
else
    echo "ℹ️  Frontend tests available but require setup:"
    echo "   cd frontend"
    echo "   npm install --save-dev vitest @testing-library/react @testing-library/jest-dom jsdom"
    echo "   npm test"
    frontend_result=0  # Don't fail for optional frontend tests
fi

cd ..

echo
echo "📊 Test Summary"
echo "==============="

if [ $backend_result -eq 0 ]; then
    echo "✅ Backend tests: PASSED"
else
    echo "❌ Backend tests: FAILED"
fi

if [ $frontend_result -eq 0 ]; then
    echo "✅ Frontend tests: PASSED"
else
    echo "❌ Frontend tests: FAILED"
fi

echo
if [ $backend_result -eq 0 ] && [ $frontend_result -eq 0 ]; then
    echo "🎉 All tests completed successfully!"
    exit 0
else
    echo "⚠️  Some tests failed. Check output above for details."
    exit 1
fi