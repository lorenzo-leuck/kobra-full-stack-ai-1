# Full-Stack AI Software Engineer (Platform) – Take-Home Assessment

AI-driven platform for fetching, evaluating, and displaying images that match user-provided prompts

# Project Setup

## Requirements

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)
- MongoDB instance (local or cloud)
- OpenAI API key

## Docker Setup

The project is containerized using Docker with separate services for the frontend and backend:

1. **Backend (FastAPI)**: Runs on port 8000, includes Google Chrome for Playwright
2. **Frontend (React + Vite)**: Served via Node.js on port 3000

### Environment Variables

Create a `.env` file in the project root with:

```
OPENAI_API_KEY=your_openai_api_key
MONGODB_URI=your_mongodb_connection_string
```

### Run with Docker

```bash
docker-compose up --build
```

Access the application at http://localhost:3000

## Run App Locally

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

# Docs

## Backend

The backend for the AI-powered Pinterest scraper system uses FastAPI, Pydantic, and Playwright to scrape Pinterest images based on visual prompts and evaluate their relevance using AI.

### Technologies

**FastAPI + Python**: Backend framework chosen for high performance, easy-to-use async capabilities, automatic OpenAPI documentation, and type checking with Pydantic.

**MongoDB with pymongo**: Synchronous MongoDB client for storing prompt sessions, scraped images, and evaluation results. Replaced deprecated Motor library with direct pymongo integration.

**Playwright**: Headless browser automation for Pinterest scraping, simulating user behavior to align with visual prompts.

**OpenAI API**: Used for evaluating image relevance to the original prompt with AI-powered scoring.

### Folder Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration settings
│   ├── database.py          # MongoDB connection
│   ├── models/              # Pydantic models
│   │   ├── __init__.py
│   │   ├── prompt.py
│   │   └── image.py
│   ├── routers/             # API endpoints
│   │   ├── __init__.py
│   │   ├── prompts.py
│   │   └── images.py
│   └── services/            # Business logic
│       ├── __init__.py
│       ├── pinterest_scraper.py
│       └── image_evaluator.py
├── requirements.txt         # Project dependencies
└── .env.example             # Example environment variables
```

### API Endpoints

- `POST /api/v1/prompts` - Create a new visual prompt
- `GET /api/v1/prompts` - List all prompts
- `GET /api/v1/prompts/{prompt_id}` - Get a specific prompt
- `GET /api/v1/images/prompt/{prompt_id}` - Get images for a specific prompt
- `PUT /api/v1/images/{image_id}/approve` - Approve or reject an image

## Frontend

The frontend for the AI-powered Pinterest scraper system uses Vite, TypeScript, and React to provide a modern, responsive, and user-friendly interface for interacting with the backend API.

### Technologies

**Vite + TypeScript + React**: Chosen for fast development experience with hot module replacement, excellent TypeScript support, and modern build tooling. Vite provides lightning-fast dev server startup and optimized production builds.

**Shadcn/ui**: Modern component library built on Radix UI primitives with Tailwind CSS styling. Provides accessible, customizable components with consistent design system and excellent developer experience.

**Tailwind CSS**: Utility-first CSS framework for rapid UI development with consistent spacing, colors, and responsive design patterns.

### Folder Structure

```
frontend/
├── public/                 # Static assets served directly
│   └── vite.svg           # Vite logo
├── src/                   # Source code
│   ├── assets/            # Static assets (images, fonts, etc.)
│   ├── App.tsx            # Main application component
│   ├── App.css            # Application-specific styles
│   ├── main.tsx           # Application entry point
│   ├── index.css          # Global styles with Tailwind imports
│   └── vite-env.d.ts      # Vite environment type definitions
├── components.json        # Shadcn/ui configuration
├── tailwind.config.js     # Tailwind CSS configuration
├── postcss.config.js      # PostCSS configuration for Tailwind
├── vite.config.ts         # Vite build configuration
├── tsconfig.json          # TypeScript configuration
├── tsconfig.app.json      # App-specific TypeScript config
├── tsconfig.node.json     # Node-specific TypeScript config
└── package.json           # Dependencies and scripts
```

# Release History
* 0.1 - First commit
* 0.2 - Frontend setup
* 0.3 - Backend setup


# License

<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1">