# Full-Stack AI Software Engineer (Platform) – Take-Home Assessment

AI-driven platform for fetching, evaluating, and displaying images that match user-provided prompts

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
MONGODB_URI=your_mongodb_connection_string
PIN_USERNAME=your_pinterest_username
PIN_PASSWORD=your_pinterest_password
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
python3 scripts/pinterest.py "80s rappers" 15 --headless --output-name vintage_hip_hop
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

# Architecture

## Backend

The backend for the AI-powered Pinterest scraper system uses FastAPI, Pydantic, and Playwright to scrape Pinterest images based on visual prompts and evaluate their relevance using AI.

### Technologies

**FastAPI + Python**: Backend framework chosen for high performance, easy-to-use async capabilities, automatic OpenAPI documentation, and type checking with Pydantic.

**MongoDB with pymongo**: Synchronous MongoDB client for storing prompts, sessions, pins, and agent configurations in dedicated collections with specific schemas. Uses MongoDB ObjectId for document references and relationship management.

**Playwright**: Headless browser automation for Pinterest scraping, simulating user behavior to align with visual prompts.

**Pydantic AI**: Chosen over LangChain and LlamaIndex for AI integration due to its **actual structured output** rather than "wishful thinking" approaches. Provides:
- **Type-safe AI responses**: Guaranteed structured output with Pydantic models
- **Multimodal support**: Native image analysis with GPT-4o vision capabilities
- **Reliable validation**: Built-in validation and error handling for AI responses
- **Configurable settings**: Temperature, model selection, and prompt management
- **Production-ready**: No complex chains or unreliable parsing - just clean, predictable AI integration

**OpenAI GPT-4o**: Multimodal model for evaluating image-prompt matching with both visual analysis and textual context understanding.

### MongoDB Collections

The application uses four MongoDB collections with the following schemas:

1. **prompts**:
   - `_id`: ObjectId - Unique identifier
   - `text`: string - The visual prompt text
   - `created_at`: ISODate - When the prompt was created
   - `status`: enum("pending", "completed", "error") - Current status

2. **sessions**:
   - `_id`: ObjectId - Unique identifier
   - `prompt_id`: ObjectId - Reference to the prompt
   - `stage`: enum("warmup", "scraping", "validation") - Processing stage
   - `status`: enum("pending", "completed", "failed") - Current status
   - `timestamp`: ISODate - When the session was created/updated
   - `log`: array of strings - Processing logs

3. **pins**:
   - `_id`: ObjectId - Unique identifier
   - `prompt_id`: ObjectId - Reference to the prompt
   - `image_url`: string - URL to the image
   - `pin_url`: string - URL to the Pinterest pin
   - `title`: string - Pin title
   - `description`: string - Pin description
   - `match_score`: float - AI evaluation score (0.0-1.0)
   - `status`: enum("ready", "approved", "disqualified") - Processing/evaluation status
   - `ai_explanation`: string - AI reasoning for the score
   - `metadata`: object - Collection metadata with timestamps

4. **agents**:
   - `_id`: ObjectId - Unique identifier
   - `title`: string - Agent identifier (e.g., "pin-evaluator")
   - `model`: string - AI model name (e.g., "gpt-4o")
   - `system_prompt`: string - System prompt for the AI agent
   - `user_prompt_template`: string - Template for user prompts with placeholders
   - `temperature`: float - AI response temperature (0.0-2.0)
   - `metadata`: object - Creation/update timestamps and version info

### Folder Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration settings (MongoDB, Pinterest, OpenAI)
│   ├── database/            # Database layer with MongoDB integration
│   │   ├── __init__.py      # Exports all database classes
│   │   ├── base.py          # BaseDB with common CRUD operations
│   │   ├── prompts.py       # PromptDB + PromptSchema
│   │   ├── sessions.py      # SessionDB + SessionSchema
│   │   └── pins.py          # PinDB + PinSchema + PinMetadata
│   ├── models/              # Pydantic models (legacy)
│   │   ├── __init__.py
│   │   ├── prompt.py        # Prompt model with MongoDB ObjectId
│   │   ├── session.py       # Session model for tracking processing stages
│   │   └── pin.py           # Pin model with expanded fields
│   ├── routers/             # API endpoints
│   │   ├── __init__.py
│   │   ├── prompts.py       # Prompt management endpoints
│   │   ├── sessions.py      # Session tracking endpoints
│   │   └── pins.py          # Pin management with filtering
│   └── services/            # Business logic
│       ├── __init__.py
│       ├── workflow/        # Workflow orchestration
│       │   ├── __init__.py
│       │   └── main.py      # WorkflowOrchestrator + PinterestWorkflowHandler
│       ├── pinterest/       # Pinterest scraping services
│       │   ├── __init__.py
│       │   ├── session.py   # Browser session management
│       │   ├── warmup.py    # Pinterest algorithm warm-up
│       │   └── pins.py      # Pin data extraction & enrichment
│       └── ai/              # AI evaluation services
│           ├── __init__.py
│           └── evaluator.py # Image-prompt matching with explanations
├── scripts/                 # Standalone scripts
│   ├── workflow.py          # NEW: Workflow orchestrator script (recommended)
│   ├── pinterest.py         # Legacy Pinterest scraping CLI
│   └── download.py          # Image download utilities
├── exports/                 # Generated data exports
│   └── warmup_*/            # Per-prompt export folders
├── requirements.txt         # Project dependencies
└── .env.example             # Example environment variables
```

### Workflow Orchestrator Architecture

The system now uses a modular workflow orchestrator that separates concerns and enables future expansion:

**WorkflowOrchestrator**:
- Generic orchestration class that coordinates different services
- Manages prompt creation and database persistence
- Provides clean interfaces: `run_pinterest_workflow()`, `run_ai_agent_workflow()` (future)
- Handles error recovery and status tracking

**PinterestWorkflowHandler**:
- Pinterest-specific implementation
- Manages browser sessions, warmup, scraping, and title enrichment
- Integrates with database layer for data persistence
- Handles Pinterest authentication and session management

## Frontend

Modern React + TypeScript frontend with three-phase user experience:

### Technologies
- **React 19** + **TypeScript** - Modern React with type safety
- **Tailwind CSS** - Utility-first styling with custom design system
- **Lucide React** - Beautiful icon library
- **Vite** - Fast build tool and development server

### Architecture
```
frontend/src/
├── components/
│   ├── PromptSubmission.tsx    # Landing page with prompt input
│   ├── AgentProgress.tsx       # Real-time workflow progress
│   ├── ImageReview.tsx         # Results gallery with filtering
│   ├── LoadingSpinner.tsx      # Reusable loading component
│   ├── StatusBadge.tsx         # Pin approval status
│   ├── ScoreBar.tsx           # AI match score visualization
│   └── ErrorBoundary.tsx      # Error handling
├── types/index.ts             # TypeScript interfaces
└── App.tsx                    # Main application router
```

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


# License

<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1">