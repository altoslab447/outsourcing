import httpx
import hashlib
import re
from datetime import datetime, timedelta
from typing import List
from bs4 import BeautifulSoup
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from models import Job

GURU_URLS = [
    "https://www.guru.com/d/jobs/",
    "https://www.guru.com/d/jobs/cat/programming-development/",
    "https://www.guru.com/d/jobs/cat/design-art/",
    "https://www.guru.com/d/jobs/cat/writing-translation/",
    "https://www.guru.com/d/jobs/cat/sales-marketing/",
]

TECH_KEYWORDS = [
    "developer", "engineer", "software", "backend", "frontend", "fullstack",
    "api", "mobile", "web", "react", "python", "node", "javascript",
    "typescript", "php", "java", "flutter", "django", "wordpress", "shopify",
    "devops", "cloud", "database", "app",
]
DESIGN_KEYWORDS = [
    "design", "designer", "ux", "ui", "figma", "photoshop", "illustrator",
    "graphic", "logo", "branding", "video", "animation", "3d", "banner",
]
MARKETING_KEYWORDS = [
    "marketing", "content", "copywriting", "seo", "social media", "ads",
    "email", "campaign", "growth", "ecommerce",
]
TRANSLATION_KEYWORDS = [
    "translation", "translator", "localization", "writing", "editor",
    "proofreading", "subtitles", "chinese", "japanese", "korean",
]
JOB_KEYWORDS = [
    "full-time", "full time", "permanent", "benefits", "401k",
    "health insurance", "paid vacation", "salaried", "w-2",
    "we are hiring", "join our team", "annual salary",
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
    combined = (title + " " + description).lower()
    return any(kw in combined for kw in JOB_KEYWORDS)


def parse_budget(text: str):
    if not text:
        return None, None
    text = text.replace(",", "")
    numbers = re.findall(r"[\d]+(?:\.\d+)?", text)
    numbers = [float(n) for n in numbers if float(n) > 0]
    if "/hr" in text.lower() or "hour" in text.lower():
        if numbers:
            rate = numbers[0]
            return rate * 40, rate * 160
    if len(numbers) >= 2:
        return numbers[0], numbers[1]
    elif len(numbers) == 1:
        return numbers[0] * 0.8, numbers[0]
    return None, None


def extract_skills(text: str) -> List[str]:
    skill_list = [
        "React", "Vue.js", "Angular", "Node.js", "Python", "JavaScript",
        "TypeScript", "PHP", "Java", "Flutter", "Django", "WordPress",
        "Shopify", "Docker", "AWS", "Figma", "Photoshop", "SEO",
        "Next.js", "MySQL", "MongoDB", "Tailwind", "Swift", "Go",
    ]
    found = []
    text_lower = text.lower()
    for skill in skill_list:
        if skill.lower() in text_lower:
            found.append(skill)
    return found[:8]


async def fetch_upwork_jobs() -> List[Job]:
    """Scrape freelance projects from Guru.com (Upwork RSS is discontinued)."""
    jobs = []
    seen_ids = set()

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }

    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        for url in GURU_URLS[:3]:
            try:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "lxml")

                # Guru job cards
                cards = soup.select(".jobRecord, .serviceRecord, [class*='job-record'], [class*='jobRecord']")
                if not cards:
                    cards = soup.select("li.record, div.record")
                if not cards:
                    cards = soup.find_all("div", class_=re.compile(r"job|project|listing", re.I))

                for card in cards[:20]:
                    try:
                        title_el = card.find(["h2", "h3", "h4", "a"], class_=re.compile(r"title|heading|name", re.I))
                        if not title_el:
                            title_el = card.find("a", href=re.compile(r"/d/jobs/id/"))
                        if not title_el:
                            continue

                        title = title_el.get_text(strip=True)
                        if not title or len(title) < 5:
                            continue

                        link_el = card.find("a", href=re.compile(r"/d/jobs/|/job/"))
                        link = ""
                        if link_el:
                            href = link_el.get("href", "")
                            link = f"https://www.guru.com{href}" if href.startswith("/") else href

                        desc_el = card.find(class_=re.compile(r"desc|summary|body|detail", re.I))
                        description = desc_el.get_text(strip=True) if desc_el else title

                        if is_job_listing(title, description):
                            continue

                        job_hash = hashlib.md5(f"guru-{title}-{link}".encode()).hexdigest()[:12]
                        if job_hash in seen_ids:
                            continue
                        seen_ids.add(job_hash)

                        budget_el = card.find(class_=re.compile(r"budget|price|amount|pay", re.I))
                        budget_min, budget_max = parse_budget(
                            budget_el.get_text(strip=True) if budget_el else ""
                        )

                        category = categorize(title, description)
                        skills = extract_skills(title + " " + description)

                        job = Job(
                            id=f"guru-{job_hash}",
                            title=title,
                            description=description[:600],
                            source="guru",
                            source_url=link or url,
                            budget_min=budget_min,
                            budget_max=budget_max,
                            currency="USD",
                            skills=skills,
                            category=category,
                            posted_at=datetime.utcnow() - timedelta(hours=3),
                            is_remote=True,
                        )
                        jobs.append(job)

                    except Exception:
                        continue

            except Exception as e:
                print(f"[Guru] Error fetching {url}: {e}")
                continue

    print(f"[Guru] 抓取到 {len(jobs)} 筆接案任務")
    return jobs
