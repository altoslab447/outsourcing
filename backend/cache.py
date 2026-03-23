import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import List, Optional
from models import Job

DB_PATH = os.path.join(os.path.dirname(__file__), "jobs_cache.db")
CACHE_TTL_MINUTES = 30


def init_db():
    """Initialize the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            source TEXT NOT NULL,
            cached_at TIMESTAMP NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cache_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_jobs(jobs: List[Job]) -> None:
    """Save jobs to the cache, replacing all previous entries."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    # Clear all existing jobs so filtered-out entries don't linger
    cursor.execute("DELETE FROM jobs")
    for job in jobs:
        job_dict = job.model_dump()
        # Convert datetime to string for JSON serialization
        if isinstance(job_dict.get("posted_at"), datetime):
            job_dict["posted_at"] = job_dict["posted_at"].isoformat()
        cursor.execute(
            "INSERT INTO jobs (id, data, source, cached_at) VALUES (?, ?, ?, ?)",
            (job.id, json.dumps(job_dict), job.source, now),
        )
    # Update last refresh time
    cursor.execute(
        "INSERT OR REPLACE INTO cache_meta (key, value, updated_at) VALUES (?, ?, ?)",
        ("last_refresh", now, now),
    )
    conn.commit()
    conn.close()


def get_cached_jobs(max_age_minutes: int = CACHE_TTL_MINUTES) -> Optional[List[Job]]:
    """Get jobs from cache if they're recent enough."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cutoff = (datetime.utcnow() - timedelta(minutes=max_age_minutes)).isoformat()
    cursor.execute(
        "SELECT data FROM jobs WHERE cached_at > ? ORDER BY cached_at DESC",
        (cutoff,),
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return None

    jobs = []
    for row in rows:
        try:
            job_dict = json.loads(row[0])
            # Convert string back to datetime
            if isinstance(job_dict.get("posted_at"), str):
                job_dict["posted_at"] = datetime.fromisoformat(job_dict["posted_at"])
            jobs.append(Job(**job_dict))
        except Exception:
            continue
    return jobs if jobs else None


def get_all_cached_jobs() -> List[Job]:
    """Get all jobs from cache regardless of age."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT data FROM jobs ORDER BY cached_at DESC")
    rows = cursor.fetchall()
    conn.close()

    jobs = []
    for row in rows:
        try:
            job_dict = json.loads(row[0])
            if isinstance(job_dict.get("posted_at"), str):
                job_dict["posted_at"] = datetime.fromisoformat(job_dict["posted_at"])
            jobs.append(Job(**job_dict))
        except Exception:
            continue
    return jobs


def get_last_refresh_time() -> Optional[datetime]:
    """Get the timestamp of the last cache refresh."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM cache_meta WHERE key = 'last_refresh'")
    row = cursor.fetchone()
    conn.close()
    if row:
        try:
            return datetime.fromisoformat(row[0])
        except Exception:
            return None
    return None


def clear_old_cache(older_than_hours: int = 24) -> None:
    """Remove cache entries older than specified hours."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cutoff = (datetime.utcnow() - timedelta(hours=older_than_hours)).isoformat()
    cursor.execute("DELETE FROM jobs WHERE cached_at < ?", (cutoff,))
    conn.commit()
    conn.close()


def clear_all_cache() -> None:
    """Clear all cached jobs."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jobs")
    conn.commit()
    conn.close()


def is_cache_fresh(max_age_minutes: int = CACHE_TTL_MINUTES) -> bool:
    """Check if cache is fresh (less than max_age_minutes old)."""
    last_refresh = get_last_refresh_time()
    if not last_refresh:
        return False
    age = datetime.utcnow() - last_refresh
    return age.total_seconds() < (max_age_minutes * 60)
