# Full-Stack AI Software Engineer Platform

AI-driven platform for fetching, evaluating, and displaying images that match user-provided prompts

<img src="https://img.shields.io/badge/React-v19.1.0-61DAFB?style=for-the-badge&logo=react&logoColor=white" alt="React v19.1.0" />
<img src="https://img.shields.io/badge/TypeScript-v5.2.2-007ACC?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript v5.2.2" />
<img src="https://img.shields.io/badge/FastAPI-v0.116.1-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI v0.116.1" />
<img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11+" />
<img src="https://img.shields.io/badge/MongoDB-v4.13.2-47A248?style=for-the-badge&logo=mongodb&logoColor=white" alt="MongoDB v4.13.2" />
<img src="https://img.shields.io/badge/Tailwind_CSS-v3.4.3-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind CSS v3.4.3" />
<img src="https://img.shields.io/badge/Vite-v5.2.0-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite v5.2.0" />
<img src="https://img.shields.io/badge/Playwright-v1.54.0-2EAD33?style=for-the-badge&logo=playwright&logoColor=white" alt="Playwright v1.54.0" />
<img src="https://img.shields.io/badge/OpenAI-GPT--4o-412991?style=for-the-badge&logo=openai&logoColor=white" alt="OpenAI GPT-4o" />
<img src="https://img.shields.io/badge/Docker-latest-2CA5E0?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />

# Setup

## Requirements

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)
- MongoDB instance (local or cloud)
- OpenAI API key

## Docker Compose

The project is containerized using Docker with separate services for the frontend and backend:

1. **Backend (FastAPI)**: Runs on port 8000, includes Google Chrome for Playwright
2. **Frontend (React + Vite)**: Served via Node.js on port 3000

```bash
docker-compose up --build
```

Access the application at http://localhost:3000
Access the API swagger at http://localhost:8000/docs

### Environment Variables

Create a `.env` file in the project root with:

```
OPENAI_API_KEY=your_openai_api_key
MONGODB_URL=your_mongodb_connection_string
MONGODB_DBNAME=your_mongodb_dbname
PINTEREST_USERNAME=your_pinterest_username
PINTEREST_PASSWORD=your_pinterest_password
```

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

## Scripts

The backend includes specialized scripts for Pinterest data collection:

### Workflow Script (Recommended)

```bash
cd backend
# Setup agent configurations (run once)
python3 scripts/database.py --setup-agents

# Clear database before new workflow (optional)
python3 scripts/database.py --clear

# Run complete workflow: Pinterest scraping + AI validation + export
python3 scripts/workflow.py
```

**Configuration:**
```python
# In scripts/workflow.py
PINTEREST_PROMPT = "your visual prompt here"
NUM_IMAGES = 20
```

### Pinterest Script

```bash
cd backend
python3 scripts/pinterest.py "visual prompt" [num_images] [options]
```

**Examples:**
```bash
# Basic usage - scrape 10 images for "boho minimalist bedroom"
python3 scripts/pinterest.py "boho minimalist bedroom" 10

# Headless mode with custom output name
python3 scripts/pinterest.py "cozy interior" 15 --headless --output-name cozy_interior
```

**Options:**
- `--headless`: Run browser in headless mode
- `--output-name`: Custom folder name for exports
- `--no-download`: Skip image downloads, export only JSON metadata
- `--username`: Pinterest username (overrides env variable)
- `--password`: Pinterest password (overrides env variable)

**Output:**
- JSON metadata: `exports/warmup_prompt/warmup_prompt_metadata.json`
- Downloaded images: `exports/warmup_prompt/warmup_prompt_N.jpg`

### Database Management Script

```bash
cd backend
# Interactive database management
python3 scripts/database.py

# Or use command line options
python3 scripts/database.py --clear          # Clear all collections
python3 scripts/database.py --setup-agents   # Setup AI agent configurations
python3 scripts/database.py --status         # Show database status
```

**Features:**
- **Setup AI Agents**: Configure GPT-4o with optimized prompts and temperature settings
- **Clear Database**: Remove all data from collections (prompts, sessions, pins, status, agents)
- **Database Status**: View collection counts and sample documents
- **Interactive Menu**: User-friendly interface for database operations

# Architecture

## Backend

The backend is a FastAPI-based system that orchestrates Pinterest scraping, AI validation, and real-time progress tracking. It implements a three-phase workflow: warmup, scraping, and validation.

### Key Technologies

- **FastAPI + Python**: High-performance async framework with automatic OpenAPI documentation
- **MongoDB + pymongo**: Document database for storing prompts, sessions, pins, and progress
- **Playwright**: Headless browser automation for Pinterest interaction
- **OpenAI GPT-4o**: Multimodal AI for image evaluation with structured responses
- **Pydantic**: Type-safe data validation and AI response parsing

### Backend Structure

```
backend/
├── app/
│   ├── config.py            # Environment configuration
│   ├── main.py              # FastAPI application entry point
│   ├── database/            # MongoDB data layer
│   │   ├── base.py          # BaseDB class with CRUD operations
│   │   ├── prompts.py       # PromptDB for user prompts
│   │   ├── sessions.py      # SessionDB for workflow stages
│   │   ├── pins.py          # PinDB for Pinterest images
│   │   ├── status.py        # StatusDB for progress tracking
│   │   └── agents.py        # AgentDB for AI configurations
│   ├── routes/              # API endpoints
│   │   └── main.py          # All REST endpoints
│   └── services/            # Business logic
│       ├── pinterest/       # Pinterest automation
│       │   ├── auth.py      # Pinterest login/session
│       │   ├── warmup.py    # Algorithm training
│       │   └── scraper.py   # Image collection
│       ├── ai/              # AI validation
│       │   └── evaluator.py # GPT-4o image analysis
│       ├── workflow/        # Orchestration
│       │   └── main.py      # WorkflowOrchestrator

└── scripts/                 # Standalone utilities
    ├── workflow.py          # Complete workflow runner
    ├── database.py          # DB management
    └── pinterest.py         # Direct Pinterest CLI
```

### Three-Phase Workflow

1. **Pinterest Warmup (0-33%)**: Train algorithm by engaging with 5 relevant pins
2. **Image Scraping (33-66%)**: Collect 20+ images from homepage and search
3. **AI Validation (66-100%)**: Evaluate images with GPT-4o for relevance

### Real-Time Progress

- **StatusDB**: Central progress tracking (0-100% with timestamped messages)
- **Polling Architecture**: Frontend polls `/api/prompts/{id}/status` every 2 seconds
- **Session Tracking**: Individual progress for warmup, scraping, validation phases

### Database Collections

- **prompts**: User visual prompts and overall status
- **sessions**: Phase-specific progress (warmup/scraping/validation)
- **pins**: Pinterest images with AI scores and classifications
- **status**: Real-time workflow progress tracking
- **agents**: AI model configurations and prompts

> **📖 Detailed Documentation**: See [docs/backend.md](docs/backend.md) for complete API reference, database schemas, service architecture, and configuration details.

## Frontend

Modern React + TypeScript frontend with three-phase user experience:

### Technologies
- **React 19** + **TypeScript** - Modern React with type safety
- **Tailwind CSS** - Utility-first styling with custom design system
- **Lucide React** - Beautiful icon library
- **Vite** - Fast build tool and development server

### Architecture
```
frontend/
├── src/
│   ├── components/
│   │   ├── AgentProgress.tsx      # Real-time workflow progress with polling
│   │   ├── ErrorBoundary.tsx      # Error handling wrapper component
│   │   ├── HistorySidebar.tsx     # Hamburger menu with prompt history
│   │   ├── ImageReview.tsx        # Pin gallery with filtering and validation results
│   │   ├── LoadingSpinner.tsx     # Reusable loading animation component
│   │   ├── PromptSubmission.tsx   # Initial prompt input form
│   │   ├── ScoreBar.tsx           # AI match score visualization
│   │   ├── StatusBadge.tsx        # Status indicator badges
│   │   └── ThemeToggle.tsx        # Dark/light mode toggle
│   ├── services/
│   │   ├── api.ts                 # REST API service layer
│   │   └── polling.ts             # Polling service for real-time updates
│   ├── hooks/
│   │   └── useTheme.ts            # Custom hook for theme management
│   ├── types/
│   │   └── index.ts               # TypeScript interfaces and types
│   ├── assets/
│   │   └── react.svg              # Static assets
│   ├── App.tsx                    # Main application router and state
│   ├── App.css                    # Global application styles
│   ├── main.tsx                   # React application entry point
│   ├── index.css                  # Global CSS with Tailwind imports
│   └── vite-env.d.ts              # Vite environment type definitions
├── public/
│   └── vite.svg                   # Public static assets
├── components.json                # shadcn/ui component configuration
├── eslint.config.js               # ESLint configuration
├── postcss.config.js              # PostCSS configuration
├── tailwind.config.js             # Tailwind CSS configuration
├── tsconfig.json                  # TypeScript configuration
├── tsconfig.node.json             # Node-specific TypeScript config
├── vite.config.ts                 # Vite build configuration
├── package.json                   # Dependencies and scripts
├── Dockerfile                     # Docker container configuration
└── index.html                     # HTML entry point
```

### Real-Time Updates with Polling

The frontend uses polling-based architecture for real-time workflow progress updates:

**Polling Service** (`/services/polling.ts`):
- Polls `/api/prompts/{prompt_id}/status` endpoint every 2 seconds
- Converts API responses to message format compatible with UI components
- Handles automatic cleanup when workflow completes or fails
- Exponential backoff on errors for robust error handling

**Message Types**:
```typescript

**AgentProgress Component**:
- Starts polling service on component mount
- Updates progress bars, stage status, and activity logs in real-time
- Handles workflow completion and automatic redirect to results
- Proper cleanup and polling termination on component unmount

**Workflow**:
1. User submits prompt via PromptSubmission component
2. Frontend starts polling `/api/prompts/{prompt_id}/status` every 2 seconds
3. Backend updates database with real-time progress during workflow execution
4. Frontend receives status updates and updates progress bars, status messages, and stage indicators
5. Workflow completion triggers automatic transition to results view

**Benefits**:
- ✅ **Reliable**: No connection drops or complex connection management
- ✅ **Simple**: Standard HTTP requests, easier to debug and maintain
- ✅ **Stateless**: Each poll gets complete current state from database
- ✅ **Robust**: Automatic error handling and retry logic
- ✅ **Type-safe**: Full TypeScript support for message handling

### User Flow
1. **Prompt Submission**: User enters visual prompt with example suggestions
2. **Agent Progress**: Real-time updates showing warmup → scraping → validation
3. **Image Review**: Interactive gallery with filtering, statistics, and AI explanations

### Design System
- **Glass-morphism effects** with backdrop blur and semi-transparent backgrounds
- **Gradient themes**: Purple/pink for prompts, blue/indigo for progress, emerald for results
- **Smooth animations** and micro-interactions throughout
- **Responsive design** optimized for desktop, tablet, and mobile
- Manages Pinterest credentials and browser sessions
- Orchestrates: warmup → scraping → enrichment phases
- Logs all activities with timestamps to MongoDB

**Database Layer**:
- **BaseDB**: Common CRUD operations (create_one, get_many, update_by_id, etc.)
- **Collection-specific classes**: PromptDB, SessionDB, PinDB with Pydantic schemas
- **Proper separation**: Each method imports only what it needs
- **Status tracking**: "pending" → "ready" (ready for AI validation)

**Benefits**:
- ✅ **Separation of concerns**: Orchestrator vs service-specific handlers
- ✅ **Future-proof**: Easy to add AI agents and other services
- ✅ **Database-driven**: All workflow state persisted in MongoDB
- ✅ **Clean interfaces**: Simple method calls, complex logic hidden
- ✅ **Modular imports**: No global dependencies, imports where needed

### API Endpoints

- `POST /api/prompts` - Create a new visual prompt
- `GET /api/prompts` - List all prompts
- `GET /api/prompts/{prompt_id}` - Get a specific prompt
- `GET /api/pins/prompt/{prompt_id}` - Get pins for a specific prompt with optional filtering
- `PUT /api/pins/{pin_id}/status` - Update pin status (approved/disqualified)
- `GET /api/sessions/prompt/{prompt_id}` - Get processing sessions for a prompt
- `GET /api/sessions/{session_id}` - Get a specific processing session

# Warm-up Logic

The Pinterest scraping system implements a sophisticated warm-up strategy to align the Pinterest algorithm with the target visual prompt before collecting data.

## Three-Phase Process

### 1. **Warm-up Phase** (`PinterestWarmup.feed_algorithm()`)
- **Purpose**: Train Pinterest's recommendation algorithm to show relevant content
- **Strategy**: Search for the target prompt and engage with exactly 5 pins
- **Engagement Types**:
  - **Pin viewing**: Navigate to individual pin pages
  - **Heart reactions**: Click the heart/react button when available
  - **Hover engagement**: Simulate user interest through mouse interactions

```python
# Example warm-up for "boho minimalist bedroom"
1. Search: https://pinterest.com/search/pins/?q=boho+minimalist+bedroom
2. Engage with 5 pins: view → react with heart → return to search
3. Algorithm learns user preference for this aesthetic
```

### 2. **Scraping Phase** (`PinterestPins.scrape_feed()`)
- **Purpose**: Collect pins from the now-personalized Pinterest feed
- **Strategy**: Navigate to homepage feed (algorithm-curated content)
- **Data Extraction**:
  - **Image URLs**: High-resolution Pinterest CDN links (736x preferred)
  - **Pin URLs**: Direct links to Pinterest pin pages
  - **Descriptions**: Cleaned alt text (removes "This may contain:" prefix)
  - **Metadata**: Collection timestamps

### 3. **Title Enrichment Phase** (`PinterestPins.enrich_with_titles()`)
- **Purpose**: Extract detailed titles by visiting individual pin pages
- **Strategy**: Navigate to each pin URL to access rich metadata
- **Target**: `<h1>` elements within `div[data-test-id="rich-pin-information"]`
- **Fallback**: Graceful handling when titles aren't available

## Algorithm Effectiveness

**Why Warm-up Works:**
- Pinterest's algorithm personalizes the homepage feed based on recent interactions
- Heart reactions signal strong positive engagement
- Multiple pin views in the same category reinforce the preference
- The 5-pin limit avoids triggering spam detection

**Expected Results:**
- **Before warm-up**: Generic/mixed content on homepage
- **After warm-up**: Feed shows pins matching the target aesthetic
- **Validation**: Higher match scores from AI evaluation

## Data Structure Output

```json
{
  "image_url": "https://i.pinimg.com/736x/abc123/image.jpg",
  "pin_url": "https://pinterest.com/pin/123456789/",
  "title": "Boho Minimalist Bedroom Ideas",
  "description": "cozy bedroom with natural textures and neutral colors",
  "metadata": {
    "collected_at": "2025-01-27T22:30:15.123456"
  }
}
```

# Model Choice

## OpenAI GPT-4o (Multimodal)

**Selected Model**: `gpt-4o` with multimodal capabilities for Pinterest image evaluation.

### Why GPT-4o?

**Multimodal Analysis**: GPT-4o can analyze both visual content and textual metadata simultaneously, making it ideal for Pinterest pin evaluation where both image aesthetics and descriptive text matter.

**Visual Understanding**: Advanced computer vision capabilities for analyzing:
- **Style and mood**: Recognizes aesthetic patterns like "boho minimalist" or "industrial modern"
- **Color schemes**: Understands color harmony and palette matching
- **Composition**: Evaluates layout, balance, and visual hierarchy
- **Objects and settings**: Identifies specific elements mentioned in prompts

**Structured Output**: When combined with Pydantic AI, provides guaranteed structured responses with:
- **Match scores**: Precise 0.0-1.0 scoring for quantitative evaluation
- **Status classification**: Reliable "approved"/"disqualified" categorization
- **Explanations**: Clear reasoning for evaluation decisions

**Cost-Effective**: GPT-4o offers the best balance of:
- **Performance**: High-quality multimodal analysis
- **Speed**: Fast response times for batch processing
- **Cost**: Reasonable pricing for image + text analysis

### Configuration

**Temperature**: Set to `0.3` for consistent, deterministic evaluations rather than creative responses.

**System Prompt**: Optimized for Pinterest image evaluation with specific scoring guidelines:
- 0.8-1.0: Excellent match
- 0.6-0.79: Good match  
- 0.4-0.59: Partial match
- 0.2-0.39: Poor match
- 0.0-0.19: No match

**Alternative Models Considered**:
- **GPT-4o-mini**: Lower cost but reduced visual analysis quality
- **Claude 3.5 Sonnet**: Good multimodal but less Pinterest-specific training
- **Gemini Pro Vision**: Competitive but more complex safety filtering

**Result**: GPT-4o provides the most reliable and accurate Pinterest image evaluation for this use case.


# Release History
* 0.1 - First commit
* 0.2 - Frontend setup
* 0.3 - Backend setup
* 0.4 - Docker compose setup
* 0.5 - MongoDB schema implementation with collections for prompts, sessions, and pins
* 0.6 - Pinterest workflow orchestrator with warmup and scraping phases
* 0.7 - AI validation system with GPT-4o multimodal analysis
* 0.8 - Status tracking and session management for real-time progress
* 0.9 - Comprehensive workflow integration with real-time progress tracking
* 1.0 - Polling-based architecture for improved reliability and simplified deployment

# License

<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1">