# Backend Architecture Documentation

## Overview

The backend is a FastAPI-based system that orchestrates Pinterest scraping, AI validation, and real-time progress tracking. It uses MongoDB for data persistence and implements a three-phase workflow: warmup, scraping, and validation.

## Architecture

```
backend/
├── app/
│   ├── config.py              # Environment configuration
│   ├── main.py                # FastAPI application entry point
│   ├── database/              # MongoDB data layer
│   │   ├── base.py           # BaseDB class with CRUD operations
│   │   ├── prompts.py        # PromptDB for user prompts
│   │   ├── sessions.py       # SessionDB for workflow stages
│   │   ├── pins.py           # PinDB for Pinterest images
│   │   ├── status.py         # StatusDB for progress tracking
│   │   └── agents.py         # AgentDB for AI configurations
│   ├── routes/               # API endpoints
│   │   └── main.py          # All REST endpoints
│   └── services/             # Business logic
│       ├── pinterest/        # Pinterest automation
│       │   ├── auth.py      # Pinterest login/session
│       │   ├── warmup.py    # Algorithm training
│       │   └── scraper.py   # Image collection
│       ├── ai/              # AI validation
│       │   └── evaluator.py # GPT-4o image analysis
│       ├── workflow/        # Orchestration
│       │   └── main.py     # WorkflowOrchestrator

└── scripts/                 # Standalone utilities
    ├── workflow.py         # Complete workflow runner
    ├── database.py         # DB management
    └── pinterest.py        # Direct Pinterest CLI
```

## Database Layer

### BaseDB Class

All database operations inherit from `BaseDB` which provides:

- **CRUD Operations**: `create_one()`, `get_one()`, `update_one()`, `delete_one()`
- **Batch Operations**: `create_many()`, `get_many()`
- **ID Operations**: `get_by_id()`, `update_by_id()`, `delete_by_id()`
- **Utilities**: `count()`, `get_collection()`

### Collections

#### 1. Prompts Collection
```python
{
    "_id": ObjectId,
    "text": str,                    # User visual prompt
    "status": str,                  # "pending", "completed", "error"
    "created_at": datetime,
    "updated_at": datetime
}
```

#### 2. Sessions Collection
```python
{
    "_id": ObjectId,
    "prompt_id": ObjectId,          # Reference to prompt
    "stage": str,                   # "warmup", "scraping", "validation"
    "status": str,                  # "pending", "running", "completed", "failed"
    "timestamp": datetime,
    "logs": [str]                   # Timestamped messages
}
```

#### 3. Pins Collection
```python
{
    "_id": ObjectId,
    "prompt_id": ObjectId,          # Reference to prompt
    "image_url": str,               # Pinterest CDN URL
    "pin_url": str,                 # Original Pinterest URL
    "title": str,                   # Pin title
    "description": str,             # Alt text/description
    "match_score": float,           # AI evaluation (0.0-1.0)
    "status": str,                  # "approved", "disqualified"
    "ai_explanation": str,          # AI reasoning
    "metadata": {
        "collected_at": datetime
    }
}
```

#### 4. Status Collection
```python
{
    "_id": ObjectId,
    "prompt_id": ObjectId,          # Reference to prompt
    "overall_status": str,          # "pending", "running", "completed", "error"
    "current_step": int,            # Current step number
    "total_steps": int,             # Total steps (dynamic)
    "progress": float,              # Percentage (0.0-100.0)
    "messages": [str],              # Progress messages
    "started_at": datetime,
    "completed_at": datetime
}
```

#### 5. Agents Collection
```python
{
    "_id": ObjectId,
    "title": str,                   # "pin-evaluator"
    "model": str,                   # "gpt-4o"
    "system_prompt": str,           # AI instructions
    "temperature": float,           # 0.3 for consistency
    "max_tokens": int,              # Response limit
    "created_at": datetime,
    "updated_at": datetime
}
```

## Services Layer

### Pinterest Services

#### PinterestAuth (`pinterest/auth.py`)
- **Purpose**: Handle Pinterest login and session management
- **Methods**:
  - `login()`: Authenticate with Pinterest
  - `is_logged_in()`: Check session status
  - `get_page()`: Return authenticated Playwright page

#### PinterestWarmup (`pinterest/warmup.py`)
- **Purpose**: Train Pinterest algorithm for target prompt
- **Strategy**: Search prompt → engage with 5 pins (view + heart + save)
- **Methods**:
  - `feed_algorithm()`: Main warmup process
  - **Progress Tracking**: 10% → 33% during warmup

#### PinterestScraper (`pinterest/scraper.py`)
- **Purpose**: Collect Pinterest images after warmup
- **Strategy**: Scrape homepage feed + search results
- **Methods**:
  - `scrape_pins()`: Collect pin data
  - `enrich_with_titles()`: Extract detailed titles
  - **Progress Tracking**: 33% → 66% during scraping

### AI Services

#### ImageEvaluator (`ai/evaluator.py`)
- **Purpose**: Evaluate Pinterest images against user prompt
- **Model**: GPT-4o with multimodal capabilities
- **Configuration**:
  - **Temperature**: 0.3 (consistent evaluation)
  - **System Prompt**: Optimized for Pinterest image analysis
  - **Output**: Structured Pydantic models

**Evaluation Response**:
```python
class EvaluationResponse(BaseModel):
    match_score: float          # 0.0-1.0 relevance score
    status: Literal["approved", "disqualified"]
    explanation: str            # AI reasoning
```

**Scoring Guidelines**:
- **0.8-1.0**: Excellent match (approved)
- **0.6-0.79**: Good match (approved)
- **0.4-0.59**: Partial match (approved)
- **0.2-0.39**: Poor match (disqualified)
- **0.0-0.19**: No match (disqualified)

### Workflow Orchestrator

#### WorkflowOrchestrator (`workflow/main.py`)
- **Purpose**: Coordinate all workflow phases
- **Phases**:
  1. **Initialization**: Setup browser and Pinterest session
  2. **Warmup**: Train algorithm (0% → 33%)
  3. **Scraping**: Collect images (33% → 66%)
  4. **Validation**: AI evaluation (66% → 100%)

**Key Methods**:
- `execute_workflow()`: Main orchestration
- `_initialize_workflow_status()`: Setup progress tracking
- `setStatus()`: Update progress and messages

## API Endpoints

### Prompt Management
- `POST /api/prompts`: Create new prompt and start workflow
- `GET /api/prompts`: List all prompts
- `GET /api/prompts/{id}`: Get specific prompt
- `GET /api/prompts/{id}/status`: Get workflow progress

### Pin Management
- `GET /api/prompts/{id}/pins`: Get pins for prompt
- `PUT /api/pins/{id}/status`: Update pin approval status

### Query Parameters
- `status`: Filter by approval status ("approved", "disqualified")
- `min_score`: Filter by minimum match score
- `limit`: Limit number of results

## Real-Time Progress Tracking

### Status Updates
The system provides real-time progress through:

1. **StatusDB**: Central progress tracking
   - Overall progress percentage (0-100)
   - Current step and total steps
   - Timestamped messages

2. **Polling Architecture**: Frontend polls `/api/prompts/{id}/status`
   - 2-second intervals
   - Automatic cleanup on completion

3. **Progress Phases**:
   - **0-33%**: Pinterest warmup
   - **33-66%**: Image scraping
   - **66-100%**: AI validation

### Message Format
```python
{
    "prompt": {
        "id": str,
        "text": str,
        "status": str
    },
    "overall_progress": float,      # 0.0-100.0
    "current_stage": str,           # "warmup", "scraping", "validation"
    "sessions": [{
        "stage": str,
        "status": str,
        "logs": [str]
    }]
}
```

## Error Handling

### Pinterest Automation
- **Login Failures**: Retry with exponential backoff
- **Rate Limiting**: Respect Pinterest's request limits
- **Element Detection**: Graceful fallbacks for UI changes

### AI Validation
- **API Failures**: Retry with circuit breaker pattern
- **Invalid Responses**: Validation with Pydantic
- **Token Limits**: Chunked processing for large batches

### Database Operations
- **Connection Issues**: Automatic reconnection
- **Duplicate Prevention**: Upsert operations where appropriate
- **Transaction Safety**: Atomic operations for critical updates

## Configuration

### Environment Variables
```bash
OPENAI_API_KEY=sk-...           # Required for AI validation
MONGODB_URL=mongodb://...       # Database connection
PIN_USERNAME=email@domain.com   # Pinterest credentials
PIN_PASSWORD=password           # Pinterest credentials
MONGODB_DB_NAME=pinterest_ai    # Database name
```

### AI Agent Setup
```python
# Automatic setup via scripts/database.py --setup-agents
{
    "title": "pin-evaluator",
    "model": "gpt-4o",
    "temperature": 0.3,
    "max_tokens": 500,
    "system_prompt": "Optimized prompt for Pinterest evaluation..."
}
```

## Performance Considerations

### Database Optimization
- **Indexes**: ObjectId references, prompt_id lookups
- **Batch Operations**: Bulk inserts for pins
- **Connection Pooling**: Efficient MongoDB connections

### Pinterest Automation
- **Headless Mode**: Faster execution without UI
- **Parallel Processing**: Concurrent pin evaluation
- **Smart Delays**: Human-like interaction timing

### AI Validation
- **Batch Processing**: Multiple images per API call
- **Caching**: Avoid re-evaluating identical images
- **Rate Limiting**: Respect OpenAI API limits

## Monitoring and Logging

### Progress Tracking
- Real-time status updates in database
- Detailed step-by-step logging
- Error capture with stack traces

### Performance Metrics
- Workflow execution time
- Pinterest scraping success rate
- AI validation accuracy
- Database operation latency