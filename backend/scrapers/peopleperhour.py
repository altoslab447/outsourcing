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

PPH_URLS = [
    "https://www.peopleperhour.com/freelance-jobs",
    "https://www.peopleperhour.com/freelance-web-mobile-tech-jobs",
    "https://www.peopleperhour.com/freelance-design-art-multimedia-jobs",
    "https://www.peopleperhour.com/freelance-writing-translation-jobs",
    "https://www.peopleperhour.com/freelance-marketing-branding-jobs",
]

TECH_KEYWORDS = [
    "developer", "engineer", "software", "backend", "frontend", "fullstack",
    "api", "mobile", "web", "react", "python", "node", "javascript",
    "typescript", "php", "java", "flutter", "django", "wordpress", "shopify",
]
DESIGN_KEYWORDS = [
    "design", "designer", "ux", "ui", "figma", "photoshop", "illustrator",
    "graphic", "logo", "branding", "video", "animation", "3d",
]
MARKETING_KEYWORDS = [
    "marketing", "content", "copywriting", "seo", "social media", "ads",
    "email", "campaign", "growth",
]
TRANSLATION_KEYWORDS = [
    "translation", "translator", "localization", "writing", "editor",
    "proofreading", "subtitles",
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
    numbers = re.findall(r"[\d,]+(?:\.\d+)?", text.replace(",", ""))
    numbers = [float(n) for n in numbers if float(n) > 0]
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
        "Next.js", "MySQL", "MongoDB", "Tailwind",
    ]
    found = []
    text_lower = text.lower()
    for skill in skill_list:
        if skill.lower() in text_lower:
            found.append(skill)
    return found[:8]


async def fetch_peopleperhour_jobs() -> List[Job]:
    """Scrape freelance projects from PeoplePerHour."""
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
        for url in PPH_URLS[:3]:  # limit to avoid rate limiting
            try:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "lxml")

                # PeoplePerHour job cards
                cards = soup.select("[data-test='job-list-item'], .job-list-item, article.card")
                if not cards:
                    cards = soup.select("li.hourlie-item, div.job-item, .listing-item")
                if not cards:
                    # Generic fallback: find links that look like job pages
                    cards = soup.find_all("a", href=re.compile(r"/job/|/project/"))

                for card in cards[:20]:
                    try:
                        if card.name == "a":
                            title = card.get_text(strip=True)
                            link = card.get("href", "")
                        else:
                            title_el = card.find(["h2", "h3", "h4", "a"])
                            if not title_el:
                                continue
                            title = title_el.get_text(strip=True)
                            link_el = card.find("a", href=True)
                            link = link_el["href"] if link_el else ""

                        if not title or len(title) < 5:
                            continue
                        if link and link.startswith("/"):
                            link = f"https://www.peopleperhour.com{link}"

                        desc_el = card.find(class_=re.compile(r"desc|summary|body|preview"))
                        description = desc_el.get_text(strip=True) if desc_el else title

                        if is_job_listing(title, description):
                            continue

                        job_hash = hashlib.md5(f"pph-{title}-{link}".encode()).hexdigest()[:12]
                        if job_hash in seen_ids:
                            continue
                        seen_ids.add(job_hash)

                        budget_el = card.find(class_=re.compile(r"budget|price|amount|rate"))
                        budget_min, budget_max = parse_budget(
                            budget_el.get_text(strip=True) if budget_el else ""
                        )

                        category = categorize(title, description)
                        skills = extract_skills(title + " " + description)

                        job = Job(
                            id=f"pph-{job_hash}",
                            title=title,
                            description=description[:600],
                            source="peopleperhour",
                            source_url=link or url,
                            budget_min=budget_min,
                            budget_max=budget_max,
                            currency="USD",
                            skills=skills,
                            category=category,
                            posted_at=datetime.utcnow() - timedelta(hours=4),
                            is_remote=True,
                        )
                        jobs.append(job)

                    except Exception:
                        continue

            except Exception as e:
                print(f"[PeoplePerHour] Error fetching {url}: {e}")
                continue

    print(f"[PeoplePerHour] 抓取到 {len(jobs)} 筆接案任務")
    return jobs
