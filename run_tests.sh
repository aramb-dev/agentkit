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

# Run backend tests with coverage
if command -v pytest &> /dev/null; then
    echo "Running pytest tests with coverage..."
    python -m pytest test_*.py -v --cov=agent --cov=app --cov=rag --cov-report=term-missing --cov-report=html
    backend_result=$?
else
    echo "❌ pytest not found. Installing test dependencies..."
    pip install pytest pytest-asyncio pytest-cov httpx
    if [ $? -eq 0 ]; then
        echo "✅ Test dependencies installed. Running tests..."
        python -m pytest test_*.py -v --cov=agent --cov=app --cov=rag --cov-report=term-missing --cov-report=html
        backend_result=$?
    else
        echo "❌ Failed to install test dependencies"
        backend_result=1
    fi
fi

if [ $backend_result -eq 0 ]; then
    echo ""
    echo "📊 Coverage report generated in htmlcov/index.html"
fi

echo
echo "🌐 Running Frontend Tests..."
echo "----------------------------"

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Check if vitest is installed
if command -v npx &> /dev/null && npx vitest --version &> /dev/null; then
    echo "Running frontend tests..."
    npm test -- --run
    frontend_result=$?
    
    if [ $frontend_result -eq 0 ]; then
        echo ""
        echo "📊 Running frontend tests with coverage..."
        npm run test:coverage -- --run
    fi
else
    echo "ℹ️  Frontend tests not configured. To set up:"
    echo "   cd frontend"
    echo "   npm install"
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