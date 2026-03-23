import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from models import Job, UserPreferences, StatsResponse
from cache import (
    save_jobs, get_cached_jobs, get_all_cached_jobs,
    get_last_refresh_time, is_cache_fresh, clear_all_cache
)
from ai_scorer import score_jobs_batch
from mock_data import get_mock_jobs
from scrapers import (
    fetch_remoteok_jobs,
    fetch_freelancer_jobs,
    fetch_weworkremotely_jobs,
    fetch_104_jobs,
)

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PREFERENCES_FILE = os.path.join(os.path.dirname(__file__), "user_preferences.json")
_refresh_lock = asyncio.Lock()
_is_refreshing = False


def load_preferences() -> UserPreferences:
    """Load user preferences from file."""
    if os.path.exists(PREFERENCES_FILE):
        try:
            with open(PREFERENCES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return UserPreferences(**data)
        except Exception as e:
            logger.warning(f"Failed to load preferences: {e}")
    return UserPreferences()


def save_preferences(prefs: UserPreferences) -> None:
    """Save user preferences to file."""
    try:
        with open(PREFERENCES_FILE, "w", encoding="utf-8") as f:
            json.dump(prefs.model_dump(), f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to save preferences: {e}")


EMPLOYMENT_SIGNALS = [
    "full-time", "full time", "part-time", "part time",
    "permanent", "annual salary", "yearly salary", "compensation package",
    "health insurance", "dental", "401k", "pto ", "paid time off",
    "paid vacation", "equity", "stock options", "employee benefits",
    "we are hiring", "we're hiring", "join our team as", "join us as",
    "looking to hire", "seeking a full", "seeking a part",
    "employment contract", "permanent position", "permanent role",
    "salaried", "w2", "full time employee",
]

def is_freelance_task(title: str, description: str) -> bool:
    """Return True if this looks like a freelance/outsource task, not an employment listing."""
    combined = (title + " " + description).lower()
    for signal in EMPLOYMENT_SIGNALS:
        if signal in combined:
            return False
    return True


async def fetch_all_jobs() -> List[Job]:
    """Fetch jobs from all sources concurrently."""
    logger.info("Fetching jobs from all sources...")

    tasks = [
        fetch_remoteok_jobs(),
        fetch_freelancer_jobs(),
        fetch_weworkremotely_jobs(),
        fetch_104_jobs(),
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_jobs = []
    source_names = ["RemoteOK", "Freelancer", "WeWorkRemotely", "104"]
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Error fetching from {source_names[i]}: {result}")
        elif isinstance(result, list):
            logger.info(f"Fetched {len(result)} jobs from {source_names[i]}")
            all_jobs.extend(result)

    # If no real jobs fetched, use mock data
    if not all_jobs:
        logger.warning("No jobs fetched from any source, using mock data")
        all_jobs = get_mock_jobs()
    else:
        # Supplement with some mock data to ensure a good demo
        mock_jobs = get_mock_jobs()
        existing_ids = {j.id for j in all_jobs}
        for mock_job in mock_jobs:
            if mock_job.id not in existing_ids:
                all_jobs.append(mock_job)

    # Filter out employment listings (applied after mock data merge)
    before = len(all_jobs)
    all_jobs = [j for j in all_jobs if is_freelance_task(j.title, j.description)]
    logger.info(f"Filtered out {before - len(all_jobs)} employment listings, {len(all_jobs)} freelance tasks remain")

    # Deduplicate
    seen_ids = set()
    unique_jobs = []
    for job in all_jobs:
        if job.id not in seen_ids:
            seen_ids.add(job.id)
            unique_jobs.append(job)

    logger.info(f"Total unique jobs: {len(unique_jobs)}")
    return unique_jobs


async def refresh_jobs_task():
    """Background task to refresh and score jobs."""
    global _is_refreshing

    async with _refresh_lock:
        if _is_refreshing:
            return
        _is_refreshing = True

    try:
        jobs = await fetch_all_jobs()
        prefs = load_preferences()

        # Get API key from preferences or environment
        api_key = prefs.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY", "")

        if api_key:
            jobs = await score_jobs_batch(jobs, prefs, api_key)
        else:
            # Keep mock scores for mock data, set None for real jobs
            for job in jobs:
                if not job.id.startswith("mock-") and job.ai_score is None:
                    job.ai_score = None

        save_jobs(jobs)
        logger.info(f"Refresh complete. Cached {len(jobs)} jobs.")
    except Exception as e:
        logger.error(f"Error in refresh task: {e}")
    finally:
        _is_refreshing = False


async def periodic_refresh():
    """Run refresh every 30 minutes."""
    while True:
        try:
            await refresh_jobs_task()
        except Exception as e:
            logger.error(f"Periodic refresh error: {e}")
        await asyncio.sleep(1800)  # 30 minutes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Initial load
    if not is_cache_fresh():
        asyncio.create_task(refresh_jobs_task())
    # Start periodic refresh
    task = asyncio.create_task(periodic_refresh())
    yield
    task.cancel()


app = FastAPI(
    title="Freelance Finder API",
    description="Internal tool for finding and filtering freelance tasks",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/jobs", response_model=List[Job])
async def get_jobs(
    skills: Optional[str] = Query(None, description="Comma-separated skills filter"),
    budget_min: Optional[float] = Query(None),
    budget_max: Optional[float] = Query(None),
    hours: Optional[str] = Query(None, description="Time filter: 24h, 7d, 30d"),
    category: Optional[str] = Query(None),
    source: Optional[str] = Query(None, description="Comma-separated sources"),
    min_ai_score: Optional[float] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
):
    """Fetch jobs with optional filters."""
    # Try cache first
    jobs = get_cached_jobs()
    if not jobs:
        jobs = get_all_cached_jobs()
    if not jobs:
        # Trigger a fresh fetch if nothing cached
        await refresh_jobs_task()
        jobs = get_all_cached_jobs()
    if not jobs:
        jobs = get_mock_jobs()

    # Apply filters
    if skills:
        skill_list = [s.strip().lower() for s in skills.split(",") if s.strip()]
        if skill_list:
            jobs = [
                j for j in jobs
                if any(
                    any(sk in s.lower() for s in j.skills)
                    for sk in skill_list
                )
            ]

    if budget_min is not None:
        jobs = [
            j for j in jobs
            if j.budget_max is None or j.budget_max >= budget_min
        ]

    if budget_max is not None:
        jobs = [
            j for j in jobs
            if j.budget_min is None or j.budget_min <= budget_max
        ]

    if hours:
        now = datetime.utcnow()
        if hours == "24h":
            cutoff = now - timedelta(hours=24)
        elif hours == "7d":
            cutoff = now - timedelta(days=7)
        elif hours == "30d":
            cutoff = now - timedelta(days=30)
        else:
            cutoff = None
        if cutoff:
            jobs = [j for j in jobs if j.posted_at >= cutoff]

    if category and category != "全部":
        jobs = [j for j in jobs if j.category == category]

    if source:
        source_list = [s.strip().lower() for s in source.split(",") if s.strip()]
        if source_list:
            jobs = [j for j in jobs if j.source.lower() in source_list]

    if min_ai_score is not None:
        jobs = [
            j for j in jobs
            if j.ai_score is not None and j.ai_score >= min_ai_score
        ]

    # Sort by AI score (desc) then posted_at (desc)
    jobs.sort(
        key=lambda j: (
            j.ai_score if j.ai_score is not None else -1,
            j.posted_at,
        ),
        reverse=True,
    )

    # Pagination
    start = (page - 1) * limit
    return jobs[start:start + limit]


@app.get("/api/categories")
async def get_categories():
    """Return job categories with counts."""
    jobs = get_all_cached_jobs()
    if not jobs:
        jobs = get_mock_jobs()

    categories = ["技術開發", "設計創意", "行銷文案", "翻譯文字", "其他"]
    counts = {cat: 0 for cat in categories}
    for job in jobs:
        if job.category in counts:
            counts[job.category] += 1
        else:
            counts["其他"] += 1

    result = [{"category": "全部", "count": len(jobs)}]
    for cat in categories:
        result.append({"category": cat, "count": counts[cat]})
    return result


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Return statistics about fetched jobs."""
    jobs = get_all_cached_jobs()
    if not jobs:
        jobs = get_mock_jobs()

    by_source = {}
    by_category = {}
    for job in jobs:
        by_source[job.source] = by_source.get(job.source, 0) + 1
        by_category[job.category] = by_category.get(job.category, 0) + 1

    return StatsResponse(
        total_jobs=len(jobs),
        by_source=by_source,
        by_category=by_category,
        last_updated=get_last_refresh_time(),
    )


@app.post("/api/refresh")
async def force_refresh(background_tasks: BackgroundTasks):
    """Force refresh all job sources."""
    clear_all_cache()
    background_tasks.add_task(refresh_jobs_task)
    return {"message": "Refresh started", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/settings")
async def get_settings():
    """Get user preferences."""
    prefs = load_preferences()
    # Don't expose the API key
    data = prefs.model_dump()
    if data.get("anthropic_api_key"):
        data["anthropic_api_key"] = "***"
    return data


@app.post("/api/settings")
async def save_settings(prefs: UserPreferences, background_tasks: BackgroundTasks):
    """Save user preferences and trigger re-scoring."""
    save_preferences(prefs)
    # Trigger re-scoring in background
    api_key = prefs.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY", "")
    if api_key:
        background_tasks.add_task(refresh_jobs_task)
    return {"message": "Settings saved", "rescoring": bool(api_key)}


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "cache_fresh": is_cache_fresh(),
        "last_updated": get_last_refresh_time(),
        "is_refreshing": _is_refreshing,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
