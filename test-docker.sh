#!/bin/bash

echo "🐳 Testing Docker build for backend with Playwright..."

cd backend

echo "📦 Building Docker image..."
docker build -t pinterest-backend-test .

if [ $? -eq 0 ]; then
    echo "✅ Docker build successful!"
    echo "🧪 Testing Playwright installation..."
    
    # Test if playwright browsers are installed
    docker run --rm pinterest-backend-test playwright --version
    
    if [ $? -eq 0 ]; then
        echo "✅ Playwright is properly installed in Docker!"
    else
        echo "❌ Playwright installation failed"
    fi
else
    echo "❌ Docker build failed"
fi

echo "🧹 Cleaning up test image..."
docker rmi pinterest-backend-test 2>/dev/null || true

echo "Done!"
