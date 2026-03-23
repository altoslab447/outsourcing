import feedparser
import hashlib
import re
import httpx
from datetime import datetime
from typing import List
from email.utils import parsedate_to_datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from models import Job

WWR_RSS_URLS = [
    "https://weworkremotely.com/remote-jobs.rss",
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-design-jobs.rss",
    "https://weworkremotely.com/categories/remote-marketing-jobs.rss",
]


def clean_html(html_text: str) -> str:
    """Remove HTML tags from text."""
    clean = re.compile(r"<[^>]+>")
    text = re.sub(clean, " ", html_text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def categorize_wwr(title: str, summary: str) -> str:
    combined = (title + " " + summary).lower()
    tech_kw = [
        "developer", "engineer", "programming", "software", "backend",
        "frontend", "fullstack", "devops", "react", "python", "node",
        "javascript", "typescript", "php", "java", "mobile", "sysadmin",
        "security", "data", "machine learning", "ai", "ml",
    ]
    design_kw = [
        "design", "designer", "ux", "ui", "figma", "graphic",
        "visual", "product design", "creative",
    ]
    marketing_kw = [
        "marketing", "content", "copywriting", "seo", "growth",
        "social media", "brand", "communications", "writer",
    ]
    translation_kw = [
        "translation", "translator", "localization", "editor",
        "proofreading", "technical writer",
    ]
    for kw in tech_kw:
        if kw in combined:
            return "技術開發"
    for kw in design_kw:
        if kw in combined:
            return "設計創意"
    for kw in marketing_kw:
        if kw in combined:
            return "行銷文案"
    for kw in translation_kw:
        if kw in combined:
            return "翻譯文字"
    return "其他"


def extract_skills_from_text(text: str) -> List[str]:
    skill_patterns = [
        "React", "Vue", "Angular", "Node.js", "Python", "JavaScript",
        "TypeScript", "PHP", "Java", "Ruby", "Go", "Rust", "Swift",
        "Kotlin", "Flutter", "Django", "Rails", "Laravel", "WordPress",
        "HTML", "CSS", "MySQL", "PostgreSQL", "MongoDB", "AWS", "Docker",
        "Kubernetes", "Figma", "Photoshop", "Illustrator", "Sketch",
        "SEO", "Google Analytics", "Tableau", "PowerBI", "Salesforce",
        "HubSpot", "Mailchimp",
    ]
    found = []
    text_lower = text.lower()
    for skill in skill_patterns:
        if skill.lower() in text_lower:
            found.append(skill)
    return found[:6]


async def fetch_weworkremotely_jobs() -> List[Job]:
    """Fetch jobs from WeWorkRemotely RSS feeds."""
    jobs = []
    seen_ids = set()

    for rss_url in WWR_RSS_URLS:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(rss_url, headers={"User-Agent": "FreelanceFinder/1.0"})
                if resp.status_code != 200:
                    continue
                feed_content = resp.text

            feed = feedparser.parse(feed_content)

            for entry in feed.entries[:15]:
                try:
                    title = entry.get("title", "")
                    if not title:
                        continue

                    # WeWorkRemotely titles often have format "Company: Title"
                    if ": " in title:
                        parts = title.split(": ", 1)
                        if len(parts) == 2:
                            title = parts[1].strip()

                    link = entry.get("link", "")
                    if not link:
                        continue

                    # Generate unique ID
                    entry_id = entry.get("id", link)
                    job_hash = hashlib.md5(f"wwr-{entry_id}".encode()).hexdigest()[:12]
                    if job_hash in seen_ids:
                        continue
                    seen_ids.add(job_hash)

                    # Summary / description
                    summary = entry.get("summary", "")
                    description = clean_html(summary)[:800] if summary else title

                    # Parse date
                    published = entry.get("published", "")
                    try:
                        if published:
                            posted_at = parsedate_to_datetime(published)
                            posted_at = posted_at.replace(tzinfo=None)
                        else:
                            posted_at = datetime.utcnow()
                    except Exception:
                        posted_at = datetime.utcnow()

                    category = categorize_wwr(title, description)
                    skills = extract_skills_from_text(description)

                    job = Job(
                        id=f"wwr-{job_hash}",
                        title=title,
                        description=description[:600],
                        source="weworkremotely",
                        source_url=link,
                        budget_min=None,
                        budget_max=None,
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
            print(f"[WeWorkRemotely] Error fetching {rss_url}: {e}")
            continue

    return jobs
