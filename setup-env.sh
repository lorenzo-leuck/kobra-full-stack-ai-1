#!/bin/bash

echo "🔧 Environment Setup for Pinterest Scraper"
echo "==========================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ Created .env file"
else
    echo "📄 .env file already exists"
fi

echo ""
echo "🔑 Required Environment Variables:"
echo "=================================="
echo "1. PINTEREST_USERNAME (or PINTEREST_EMAIL) - Your Pinterest login email"
echo "2. PINTEREST_PASSWORD - Your Pinterest password"
echo "3. OPENAI_API_KEY - Your OpenAI API key for AI validation"
echo "4. MONGODB_URI - MongoDB connection string (optional, defaults to localhost)"

echo ""
echo "📋 Current Environment Status:"
echo "=============================="

# Check Pinterest credentials
if [ -n "$PINTEREST_USERNAME" ] || [ -n "$PINTEREST_EMAIL" ]; then
    echo "✅ Pinterest username/email: SET"
else
    echo "❌ Pinterest username/email: NOT SET"
fi

if [ -n "$PINTEREST_PASSWORD" ]; then
    echo "✅ Pinterest password: SET"
else
    echo "❌ Pinterest password: NOT SET"
fi

if [ -n "$OPENAI_API_KEY" ]; then
    echo "✅ OpenAI API key: SET"
else
    echo "❌ OpenAI API key: NOT SET"
fi

if [ -n "$MONGODB_URI" ]; then
    echo "✅ MongoDB URI: SET ($MONGODB_URI)"
else
    echo "⚠️  MongoDB URI: Using default (mongodb://localhost:27017/pinterest_scraper)"
fi

echo ""
echo "📝 To set environment variables:"
echo "==============================="
echo "1. Edit the .env file:"
echo "   nano .env"
echo ""
echo "2. Or export them directly:"
echo "   export PINTEREST_USERNAME='your_email@example.com'"
echo "   export PINTEREST_PASSWORD='your_password'"
echo "   export OPENAI_API_KEY='your_openai_key'"
echo ""
echo "3. Then restart Docker containers:"
echo "   docker-compose down"
echo "   docker-compose up --build"

echo ""
echo "🧪 Test the setup:"
echo "=================="
echo "Local test: cd backend && python3 scripts/workflow.py"
echo "Docker test: curl -X POST http://localhost:8000/api/prompts -H 'Content-Type: application/json' -d '{\"text\": \"test prompt\"}'"
