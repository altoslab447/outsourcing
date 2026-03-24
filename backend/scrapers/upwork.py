import feedparser
import hashlib
import re
from datetime import datetime
from typing import List
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from models import Job

# Upwork RSS feeds by category
UPWORK_RSS_FEEDS = [
    "https://www.upwork.com/ab/feed/jobs/rss?q=&sort=recency&paging=0%3B50&api_params=1&securityToken=&userUid=&orgUid=",
    "https://www.upwork.com/ab/feed/jobs/rss?q=web+development&sort=recency&paging=0%3B25",
    "https://www.upwork.com/ab/feed/jobs/rss?q=python+developer&sort=recency&paging=0%3B25",
    "https://www.upwork.com/ab/feed/jobs/rss?q=react+developer&sort=recency&paging=0%3B25",
    "https://www.upwork.com/ab/feed/jobs/rss?q=mobile+app&sort=recency&paging=0%3B25",
    "https://www.upwork.com/ab/feed/jobs/rss?q=graphic+design&sort=recency&paging=0%3B25",
    "https://www.upwork.com/ab/feed/jobs/rss?q=translation+chinese&sort=recency&paging=0%3B20",
    "https://www.upwork.com/ab/feed/jobs/rss?q=content+writing&sort=recency&paging=0%3B20",
]

TECH_KEYWORDS = [
    "developer", "engineer", "software", "backend", "frontend", "fullstack",
    "devops", "cloud", "api", "mobile", "web", "react", "python", "node",
    "javascript", "typescript", "go", "java", "php", "flutter", "django",
    "fastapi", "docker", "aws", "database", "wordpress", "shopify", "app",
]
DESIGN_KEYWORDS = [
    "design", "designer", "ux", "ui", "figma", "photoshop", "illustrator",
    "graphic", "visual", "branding", "logo", "creative", "motion", "video",
    "animation", "3d", "banner", "mockup",
]
MARKETING_KEYWORDS = [
    "marketing", "content", "copywriting", "seo", "social media", "ads",
    "growth", "analytics", "email", "campaign", "brand", "pr", "ecommerce",
]
TRANSLATION_KEYWORDS = [
    "translation", "translator", "localization", "writing", "editor",
    "proofreading", "chinese", "english", "japanese", "korean", "subtitles",
]

# Keywords that indicate a full-time job (職缺), not a freelance project
JOB_KEYWORDS = [
    "full-time", "full time", "permanent", "benefits", "401k", "health insurance",
    "paid vacation", "pto", "w-2", "salaried", "we are hiring", "join our team",
    "employee", "employment", "annual salary",
]


def categorize(title: str, description: str) -> str:
    combined = (title + " " + description).lower()
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


def is_job_listing(title: str, description: str) -> bool:
    """Return True if this looks like a full-time job, not a freelance project."""
    combined = (title + " " + description).lower()
    return any(kw in combined for kw in JOB_KEYWORDS)


def parse_budget_from_text(text: str):
    """Extract budget range from Upwork description text."""
    budget_min, budget_max = None, None

    # Hourly: "$X.xx-$Y.yy" or "Hourly: $X"
    hourly = re.search(r'[Hh]ourly[:\s]+\$?([\d,]+\.?\d*)\s*[-–]\s*\$?([\d,]+\.?\d*)', text)
    if hourly:
        low = float(hourly.group(1).replace(",", ""))
        high = float(hourly.group(2).replace(",", ""))
        budget_min = low * 160   # ~1 month
        budget_max = high * 160
        return budget_min, budget_max

    # Fixed: "Budget: $X" or "Fixed-Price: $X"
    fixed = re.search(r'(?:[Bb]udget|[Ff]ixed)[:\s]+\$?([\d,]+)', text)
    if fixed:
        val = float(fixed.group(1).replace(",", ""))
        budget_min = val * 0.8
        budget_max = val
        return budget_min, budget_max

    return budget_min, budget_max


def extract_skills(text: str) -> List[str]:
    skill_list = [
        "React", "Vue.js", "Angular", "Node.js", "Python", "JavaScript",
        "TypeScript", "PHP", "Java", "Swift", "Kotlin", "Flutter", "Django",
        "FastAPI", "WordPress", "Shopify", "Docker", "AWS", "PostgreSQL",
        "MongoDB", "Figma", "Photoshop", "Illustrator", "SEO", "Go", "Rust",
        "Ruby", "Rails", "GraphQL", "MySQL", "Redis", "Tailwind", "Next.js",
    ]
    found = []
    text_lower = text.lower()
    for skill in skill_list:
        if skill.lower() in text_lower:
            found.append(skill)
    return found[:8]


async def fetch_upwork_jobs() -> List[Job]:
    """Fetch freelance projects from Upwork RSS feeds."""
    jobs = []
    seen_ids = set()

    for feed_url in UPWORK_RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)

            for entry in feed.entries[:30]:
                try:
                    title = entry.get("title", "").strip()
                    if not title or len(title) < 5:
                        continue

                    link = entry.get("link", "")
                    description = entry.get("summary", entry.get("description", ""))

                    # Clean HTML tags from description
                    clean_desc = re.sub(r"<[^>]+>", " ", description).strip()
                    clean_desc = re.sub(r"\s+", " ", clean_desc)

                    # Skip full-time job listings
                    if is_job_listing(title, clean_desc):
                        continue

                    # Dedup
                    job_hash = hashlib.md5(f"upwork-{link}".encode()).hexdigest()[:12]
                    if job_hash in seen_ids:
                        continue
                    seen_ids.add(job_hash)

                    # Parse date
                    published = entry.get("published_parsed")
                    if published:
                        posted_at = datetime(*published[:6])
                    else:
                        posted_at = datetime.utcnow()

                    budget_min, budget_max = parse_budget_from_text(clean_desc)
                    category = categorize(title, clean_desc)
                    skills = extract_skills(title + " " + clean_desc)

                    job = Job(
                        id=f"upwork-{job_hash}",
                        title=title,
                        description=clean_desc[:800],
                        source="upwork",
                        source_url=link,
                        budget_min=budget_min,
                        budget_max=budget_max,
                        currency="USD",
                        skills=skills,
                        category=category,
                        posted_at=posted_at,
                        is_remote=True,
                    )
                    jobs.append(job)

                except Exception:
                    continue

        except Exception as e:
            print(f"[Upwork] Error fetching feed {feed_url}: {e}")
            continue

    print(f"[Upwork] 抓取到 {len(jobs)} 筆接案任務")
    return jobs
