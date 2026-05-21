# Freelance Opportunity Radar

A full-stack internal tool for finding, filtering, and prioritizing freelance
and remote contract opportunities.

The goal is simple: reduce noisy job searching into a smaller review queue with
clear filters, source context, and practical fit signals.

## Features

- Multi-source job aggregation: RemoteOK API, Freelancer.com,
  WeWorkRemotely RSS, 104.com.tw.
- Fit scoring for ranking opportunities against preferred skills and
  constraints.
- Chinese/English bilingual interface.
- Filtering by skills, budget, time, source, category, and score.
- SQLite cache for repeated scans.
- Mock data fallback when external sources are unavailable.

## Tech Stack

- Backend: Python FastAPI + SQLite
- Frontend: React 18 + Vite + Tailwind CSS
- Optional scoring provider: Anthropic Claude

## Setup

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy and configure environment
cp ../.env.example .env
# Edit .env and add your ANTHROPIC_API_KEY if scoring is enabled.

# Start server
python main.py
# OR
uvicorn main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Optional | Enables fit scoring |

Without an API key, scores show as "N/A". The tool still works for browsing
and filtering.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/jobs` | GET | Fetch jobs with filters |
| `/api/categories` | GET | Category counts |
| `/api/stats` | GET | Overall statistics |
| `/api/settings` | GET/POST | User preferences |
| `/api/refresh` | POST | Force refresh all sources |
| `/api/health` | GET | Health check |

### Filter Parameters for `/api/jobs`

- `skills` - comma-separated skill names
- `budget_min` / `budget_max` - budget range in USD
- `hours` - `24h`, `7d`, `30d`
- `category` - job category in Chinese
- `source` - comma-separated sources (`remoteok`, `freelancer`, `weworkremotely`, `104`)
- `min_ai_score` - minimum AI score (0-10)
- `page` / `limit` - pagination

## Job Categories

| Category | Description |
|----------|-------------|
| 技術開發 | Software development, engineering |
| 設計創意 | Design, UI/UX, creative work |
| 行銷文案 | Marketing, content, copywriting |
| 翻譯文字 | Translation, localization, writing |
| 其他 | Other categories |

## Color Scheme

- Background: `bg-gray-950` (#0a0f1e)
- Cards: `bg-gray-900` with `border-gray-800`
- RemoteOK: Green
- Freelancer: Blue
- WeWorkRemotely: Red
- 104人力銀行: Orange

## Notes

This is an internal operations tool, not a promise of job placement. Each
opportunity still needs manual review before applying.
