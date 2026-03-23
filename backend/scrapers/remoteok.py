import httpx
import hashlib
from datetime import datetime
from typing import List
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from models import Job

REMOTEOK_API = "https://remoteok.com/api"

TECH_KEYWORDS = [
    "developer", "engineer", "programming", "software", "backend", "frontend",
    "fullstack", "devops", "cloud", "database", "api", "mobile", "web", "react",
    "python", "node", "javascript", "typescript", "go", "rust", "java", "php",
    "ruby", "swift", "kotlin", "flutter", "django", "fastapi", "rails",
]
DESIGN_KEYWORDS = [
    "design", "designer", "ux", "ui", "figma", "sketch", "photoshop",
    "illustrator", "graphic", "visual", "branding", "logo", "creative",
    "motion", "animation", "3d", "video",
]
MARKETING_KEYWORDS = [
    "marketing", "content", "copywriting", "seo", "social media", "ads",
    "growth", "analytics", "email", "campaign", "brand", "pr", "communications",
]
TRANSLATION_KEYWORDS = [
    "translation", "translator", "localization", "writing", "editor",
    "proofreading", "chinese", "english", "japanese", "korean",
]


def categorize_job(title: str, tags: List[str]) -> str:
    combined = (title + " " + " ".join(tags)).lower()
    for kw in TECH_KEYWORDS:
        if kw in combined:
            return "技術開發"
    for kw in DESIGN_KEYWORDS:
        if kw in combined:
            return "設計創意"
    for kw in MARKETING_KEYWORDS:
        if kw in combined:
            return "行銷文案"
    for kw in TRANSLATION_KEYWORDS:
        if kw in combined:
            return "翻譯文字"
    return "其他"


def normalize_tags(tags: List[str]) -> List[str]:
    """Normalize and capitalize tag names."""
    tag_map = {
        "react": "React",
        "vue": "Vue.js",
        "angular": "Angular",
        "node": "Node.js",
        "nodejs": "Node.js",
        "python": "Python",
        "javascript": "JavaScript",
        "typescript": "TypeScript",
        "go": "Go",
        "rust": "Rust",
        "java": "Java",
        "php": "PHP",
        "ruby": "Ruby",
        "swift": "Swift",
        "kotlin": "Kotlin",
        "flutter": "Flutter",
        "django": "Django",
        "fastapi": "FastAPI",
        "docker": "Docker",
        "kubernetes": "Kubernetes",
        "aws": "AWS",
        "gcp": "GCP",
        "azure": "Azure",
        "postgres": "PostgreSQL",
        "mysql": "MySQL",
        "mongodb": "MongoDB",
        "redis": "Redis",
        "graphql": "GraphQL",
        "figma": "Figma",
        "css": "CSS",
        "html": "HTML",
        "devops": "DevOps",
        "linux": "Linux",
        "git": "Git",
    }
    result = []
    for tag in tags:
        normalized = tag_map.get(tag.lower(), tag.capitalize())
        if normalized and len(normalized) <= 30:
            result.append(normalized)
    return list(dict.fromkeys(result))  # deduplicate preserving order


async def fetch_remoteok_jobs() -> List[Job]:
    """Fetch jobs from RemoteOK free API."""
    jobs = []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; FreelanceFinder/1.0)",
                "Accept": "application/json",
            }
            resp = await client.get(REMOTEOK_API, headers=headers)
            resp.raise_for_status()
            data = resp.json()

            # First item is a legal notice, skip it
            for item in data[1:51]:  # Limit to 50 jobs
                try:
                    if not isinstance(item, dict):
                        continue

                    job_id = item.get("id", "")
                    if not job_id:
                        continue

                    title = item.get("position", item.get("title", ""))
                    if not title:
                        continue

                    description = item.get("description", "")
                    tags = item.get("tags", [])
                    if isinstance(tags, str):
                        tags = [tags]
                    tags = [t for t in tags if isinstance(t, str)]

                    slug = item.get("slug", "")
                    url = f"https://remoteok.com/remote-jobs/{slug}" if slug else item.get("url", "")
                    if not url:
                        url = f"https://remoteok.com/l/{job_id}"

                    # Parse date
                    date_str = item.get("date", "")
                    try:
                        posted_at = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        posted_at = posted_at.replace(tzinfo=None)
                    except Exception:
                        posted_at = datetime.utcnow()

                    # Salary info
                    salary_min = item.get("salary_min")
                    salary_max = item.get("salary_max")
                    budget_min = float(salary_min) / 12 if salary_min else None
                    budget_max = float(salary_max) / 12 if salary_max else None

                    skills = normalize_tags(tags)
                    category = categorize_job(title, tags)

                    job_hash = hashlib.md5(f"remoteok-{job_id}".encode()).hexdigest()[:12]

                    job = Job(
                        id=f"remoteok-{job_hash}",
                        title=title,
                        description=description[:800] if description else f"Remote position for {title}",
                        source="remoteok",
                        source_url=url,
                        budget_min=budget_min,
                        budget_max=budget_max,
                        currency="USD",
                        skills=skills[:8],
                        category=category,
                        posted_at=posted_at,
                        is_remote=True,
                    )
                    jobs.append(job)
                except Exception:
                    continue

    except Exception as e:
        print(f"[RemoteOK] Error fetching jobs: {e}")

    return jobs
