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

### Pinterest Warmup & Scraping

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

# Just get URLs without downloading images
python3 scripts/pinterest.py "modern kitchen" 20 --no-download
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

### Download Images from JSON

```bash
# Download images from existing JSON metadata
python3 scripts/download.py path/to/metadata.json
```

# Architecture

## Backend

The backend for the AI-powered Pinterest scraper system uses FastAPI, Pydantic, and Playwright to scrape Pinterest images based on visual prompts and evaluate their relevance using AI.

### Technologies

**FastAPI + Python**: Backend framework chosen for high performance, easy-to-use async capabilities, automatic OpenAPI documentation, and type checking with Pydantic.

**MongoDB with pymongo**: Synchronous MongoDB client for storing prompts, sessions, and pins in dedicated collections with specific schemas. Uses MongoDB ObjectId for document references and relationship management.

**Playwright**: Headless browser automation for Pinterest scraping, simulating user behavior to align with visual prompts.

**OpenAI API**: Used for evaluating image relevance to the original prompt with AI-powered scoring.

### MongoDB Collections

The application uses three MongoDB collections with the following schemas:

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
   - `match_score`: number - AI-evaluated relevance score
   - `status`: enum("approved", "disqualified") - Approval status
   - `ai_explanation`: string - AI-generated explanation of match score
   - `metadata`: object - Contains `collected_at` timestamp

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
│       ├── pinterest/       # Pinterest scraping services
│       │   ├── __init__.py
│       │   ├── session.py   # Browser session management
│       │   ├── warmup.py    # Pinterest algorithm warm-up
│       │   └── pins.py      # Pin data extraction & enrichment
│       └── ai/              # AI evaluation services
│           ├── __init__.py
│           └── evaluator.py # Image-prompt matching with explanations
├── scripts/                 # Standalone scripts
│   ├── pinterest.py         # Main Pinterest scraping CLI
│   └── download.py          # Image download utilities
├── exports/                 # Generated data exports
│   └── warmup_*/            # Per-prompt export folders
├── requirements.txt         # Project dependencies
└── .env.example             # Example environment variables
```

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


# Release History
* 0.1 - First commit
* 0.2 - Frontend setup
* 0.3 - Backend setup
* 0.4 - Docker compose setup
* 0.5 - MongoDB schema implementation with collections for prompts, sessions, and pins


# License

<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1">