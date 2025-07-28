# Features

- **Beautiful UI**: Modern gradient backgrounds, glass-morphism effects, and smooth animations
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile devices
- **Real-time Progress**: Live updates during AI agent workflow execution
- **Advanced Filtering**: Filter by approval status, match score threshold, and view modes
- **Component Architecture**: Modular, reusable components with TypeScript support

# Architecture

```
src/
├── components/           # React components
│   ├── PromptSubmission.tsx    # Initial prompt input form
│   ├── AgentProgress.tsx       # Real-time workflow progress
│   ├── ImageReview.tsx         # Results gallery with filtering
│   ├── LoadingSpinner.tsx      # Reusable loading component
│   ├── StatusBadge.tsx         # Pin approval status badge
│   └── ScoreBar.tsx           # AI match score visualization
├── services/            # API service layer
│   └── api.ts          # Backend API integration
├── types/              # TypeScript type definitions
│   └── index.ts        # Shared interfaces and types
├── App.tsx             # Main application component
└── index.css           # Global styles and utilities
```

# UI Components

## PromptSubmission
- Gradient background with glass-morphism card
- Auto-complete suggestions with example prompts
- Loading states with animated spinner
- Form validation and error handling

### AgentProgress
- Three-stage progress visualization (Warmup → Scraping → Validation)
- Real-time activity logs for each stage
- Overall progress bar with percentage
- Stage-specific icons and status indicators

### ImageReview
- Grid and list view modes
- Advanced filtering (status, score threshold)
- Statistics dashboard (approved, disqualified, avg score)
- Pin cards with images, titles, scores, and AI explanations
- External link integration to original Pinterest pins

# API Integration

The frontend expects the following backend endpoints:

## POST `/api/prompts`
Submit a new prompt for processing
```json
{
  "text": "cozy industrial home office"
}
```
**Response:**
```json
{
  "prompt_id": "prompt_123",
  "success": true
}
```

## GET `/api/prompts/{prompt_id}/status`
Get real-time workflow status
**Response:**
```json
{
  "prompt": {
    "_id": "prompt_123",
    "text": "cozy industrial home office",
    "status": "pending|completed|error",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "sessions": [
    {
      "_id": "session_123",
      "prompt_id": "prompt_123",
      "stage": "warmup|scraping|validation",
      "status": "pending|completed|failed",
      "timestamp": "2024-01-01T00:00:00Z",
      "log": ["Initializing...", "Processing..."]
    }
  ],
  "overall_progress": 75,
  "current_stage": "validation"
}
```

## GET `/api/prompts/{prompt_id}/pins`
Get validated pins with optional filtering
**Query Parameters:**
- `status`: "approved" | "disqualified" (optional)
- `min_score`: number 0.0-1.0 (optional)

**Response:**
```json
{
  "pins": [
    {
      "_id": "pin_123",
      "image_url": "https://pinterest-cdn.com/image.jpg",
      "pin_url": "https://pinterest.com/pin/123",
      "title": "Modern Industrial Office",
      "description": "Clean workspace with industrial elements",
      "match_score": 0.92,
      "status": "approved",
      "ai_explanation": "Excellent match with industrial elements...",
      "metadata": {
        "collected_at": "2024-01-01T00:00:00Z"
      }
    }
  ],
  "total_count": 25,
  "approved_count": 18,
  "disqualified_count": 7,
  "avg_score": 0.73
}
```

## GET `/api/prompts`
Get prompt history (bonus feature)
**Response:**
```json
[
  {
    "_id": "prompt_123",
    "text": "cozy industrial home office",
    "status": "completed",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

# User Flow

1. **Prompt Submission**: User enters visual prompt (e.g., "boho minimalist bedroom")
2. **Agent Progress**: Real-time updates as AI agent:
   - Warms up Pinterest account
   - Scrapes 20-30 images from feed
   - Validates each image with AI model
3. **Results Review**: Interactive gallery showing:
   - Approved vs disqualified pins
   - AI match scores and explanations
   - Filtering and view options


# 📦 Dependencies

- **React 19** - Modern React with concurrent features
- **TypeScript** - Type safety and developer experience
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide React** - Beautiful icon library
- **Vite** - Fast build tool and dev server

# 🎨 Design System

- **Colors**: Purple/pink gradients for primary actions, emerald for success states
- **Typography**: Inter font family for modern, clean text
- **Spacing**: Consistent 4px grid system
- **Animations**: Smooth transitions and micro-interactions
- **Glass-morphism**: Semi-transparent backgrounds with blur effects

# 🔧 Development Notes

- All components are fully typed with TypeScript
- API calls are centralized in the `services/api.ts` file
- Mock data is provided for development without backend
- Responsive design tested on mobile, tablet, and desktop
- Accessibility features included (focus states, ARIA labels)