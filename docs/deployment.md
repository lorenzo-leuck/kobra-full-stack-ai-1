# Docker Production Setup

This application is designed for production deployment using Docker and Docker Compose, which provides the ideal containerized environment for consistent, scalable, and maintainable deployments. The Docker setup includes:

**Backend Container (FastAPI + Playwright):**
```dockerfile
# Multi-stage build for optimized production image
FROM python:3.11-slim-bullseye as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage with Playwright dependencies
FROM python:3.11-slim-bullseye
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates wget gnupg curl libnss3 libnspr4 \
    libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxrandr2 libgbm1 libxss1 libasound2 \
    libatspi2.0-0 libgtk-3-0 && rm -rf /var/lib/apt/lists/*

# Install Playwright browsers for Pinterest scraping
RUN playwright install chromium
RUN playwright install-deps chromium

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

**Frontend Container (React + Node.js):**
```dockerfile
# Node.js container serving built React app
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
RUN npm install -g serve

# Serve static React build instead of nginx
CMD ["serve", "-s", "dist", "-l", "3000"]
```

**Docker Compose Configuration:**
```yaml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    networks:
      - app-network

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - MONGODB_URL=${MONGODB_URL}
      - PINTEREST_USERNAME=${PINTEREST_USERNAME}
      - PINTEREST_PASSWORD=${PINTEREST_PASSWORD}
    networks:
      - app-network
    restart: unless-stopped

networks:
  app-network:
    driver: bridge
```

This containerized approach ensures consistent environments across development and production, handles all Playwright dependencies for web scraping, and uses Node.js to serve the React build directly instead of requiring nginx configuration.

# AWS Deployment Guide

This guide covers deploying the Full-Stack AI Pinterest Scraper to AWS EC2 using Docker.

## Prerequisites

- AWS EC2 instance (Ubuntu 24.04 LTS)
- Security Group configured for ports 22, 3000, 8000
- SSH key pair for EC2 access
- Domain name or public IP access

## Deployment Steps

### 1. Initial EC2 Setup

```bash
# Connect to EC2 instance
ssh -i your-key.pem ubuntu@YOUR-AWS-IP

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
sudo apt install docker.io -y
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose -y

# Verify installations
docker --version
docker-compose --version
```

### 2. Set Up Git Repository

```bash
# Create bare Git repository
sudo mkdir -p /var/www/kobra-full-stack-ai-1.git
sudo git init --bare /var/www/kobra-full-stack-ai-1.git
sudo chown -R ubuntu:ubuntu /var/www/kobra-full-stack-ai-1.git

# Create deployment directory
sudo mkdir -p /var/www/kobra-full-stack-ai-1
sudo chown -R ubuntu:ubuntu /var/www/kobra-full-stack-ai-1
```

### 3. Create Git Post-Receive Hook

```bash
# Create the hook file
sudo nano /var/www/kobra-full-stack-ai-1.git/hooks/post-receive
```

**Hook Content:**
```bash
#!/bin/bash
echo "🚀 Starting deployment for kobra-full-stack-ai-1..."

DEPLOY_DIR="/var/www/kobra-full-stack-ai-1"
GIT_DIR="/var/www/kobra-full-stack-ai-1.git"

mkdir -p "$DEPLOY_DIR"
cd "$DEPLOY_DIR"
git --git-dir="$GIT_DIR" --work-tree="$DEPLOY_DIR" checkout -f main
echo "📁 Files checked out to $DEPLOY_DIR"

if [ ! -f "$DEPLOY_DIR/.env" ]; then
    cp "$DEPLOY_DIR/.env.template" "$DEPLOY_DIR/.env" 2>/dev/null || echo "⚠️  Please create .env file manually"
fi

echo "🛑 Stopping existing containers..."
cd "$DEPLOY_DIR"
docker-compose down 2>/dev/null || true

echo "🔨 Building and starting containers..."
docker-compose up --build -d

echo "📊 Container status:"
docker-compose ps

echo "✅ Deployment complete!"
echo "🌐 Frontend: http://YOUR-AWS-IP:3000"
echo "🔧 Backend API: http://YOUR-AWS-IP:8000/docs"
```

```bash
# Make hook executable
sudo chmod +x /var/www/kobra-full-stack-ai-1.git/hooks/post-receive
```

### 4. Local Git Setup

```bash
# Add AWS remote (from local machine)
cd /path/to/full-stack-ai
git remote add aws ubuntu@YOUR-AWS-IP:/var/www/kobra-full-stack-ai-1.git

# Push to AWS
git push aws main
```

### 5. Environment Configuration

```bash
# SSH to AWS and create .env file
ssh -i your-key.pem ubuntu@YOUR-AWS-IP
cd /var/www/kobra-full-stack-ai-1
nano .env
```

**Environment Variables (.env):**
```bash
MONGODB_URL=your_mongodb_connection_string
MONGODB_DB_NAME=your_database_name
OPENAI_API_KEY=your_openai_api_key
PINTEREST_USERNAME=your_pinterest_email
PINTEREST_PASSWORD=your_pinterest_password
```

### 6. Manual Deployment (if needed)

```bash
# Manual checkout and build
cd /var/www/kobra-full-stack-ai-1
git --git-dir=/var/www/kobra-full-stack-ai-1.git --work-tree=/var/www/kobra-full-stack-ai-1 checkout -f main

# Build and start containers
docker-compose up --build -d

# Check status
docker-compose ps
docker-compose logs -f
```

## AWS Security Group Configuration

**Required Inbound Rules:**
- Port 22 (SSH): Source = Your IP
- Port 3000 (Frontend): Source = 0.0.0.0/0
- Port 8000 (Backend API): Source = 0.0.0.0/0

## Access URLs

- **Frontend**: `http://YOUR-AWS-IP:3000`
- **Backend API**: `http://YOUR-AWS-IP:8000/docs`
- **Health Check**: `http://YOUR-AWS-IP:8000/health`

