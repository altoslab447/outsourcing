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

FREELANCER_JOBS_URL = "https://www.freelancer.com/jobs/"

CATEGORY_MAP = {
    "web-development": "技術開發",
    "software-development": "技術開發",
    "mobile-development": "技術開發",
    "design": "設計創意",
    "graphic-design": "設計創意",
    "writing": "行銷文案",
    "content-writing": "行銷文案",
    "marketing": "行銷文案",
    "translation": "翻譯文字",
    "data-entry": "其他",
    "admin-support": "其他",
}


def parse_budget(budget_text: str):
    """Parse budget string like '$500 - $1000' or '$25/hr'."""
    budget_text = budget_text.strip()
    budget_min = None
    budget_max = None

    numbers = re.findall(r"\d+(?:,\d+)?(?:\.\d+)?", budget_text.replace(",", ""))
    numbers = [float(n) for n in numbers]

    if len(numbers) >= 2:
        budget_min = numbers[0]
        budget_max = numbers[1]
    elif len(numbers) == 1:
        if "/hr" in budget_text.lower() or "hour" in budget_text.lower():
            budget_min = numbers[0] * 40  # approx weekly
            budget_max = numbers[0] * 160  # approx monthly
        else:
            budget_min = numbers[0] * 0.8
            budget_max = numbers[0]

    return budget_min, budget_max


def extract_skills_from_text(text: str) -> List[str]:
    """Extract known skill names from text."""
    skill_patterns = [
        "React", "Vue", "Angular", "Node.js", "Python", "JavaScript",
        "TypeScript", "PHP", "Java", "Ruby", "Swift", "Kotlin", "Flutter",
        "Django", "Laravel", "WordPress", "Shopify", "HTML", "CSS",
        "MySQL", "PostgreSQL", "MongoDB", "AWS", "Docker", "Figma",
        "Photoshop", "Illustrator", "SEO", "Google Ads", "Facebook Ads",
        "Content Writing", "Copywriting", "Translation", "Data Entry",
        "Excel", "PowerBI", "Tableau",
    ]
    found = []
    text_lower = text.lower()
    for skill in skill_patterns:
        if skill.lower() in text_lower:
            found.append(skill)
    return found[:6]


def categorize_from_text(title: str, description: str) -> str:
    combined = (title + " " + description).lower()
    tech_kw = ["developer", "engineer", "programming", "software", "backend",
               "frontend", "fullstack", "react", "python", "node", "javascript",
               "typescript", "php", "java", "mobile", "app", "web development",
               "wordpress", "shopify", "django", "api", "database", "cloud"]
    design_kw = ["design", "designer", "ui", "ux", "figma", "photoshop",
                 "illustrator", "graphic", "logo", "branding", "creative",
                 "visual", "animation", "video editing"]
    marketing_kw = ["marketing", "content", "copywriting", "seo", "social media",
                    "ads", "campaign", "email marketing", "growth", "analytics"]
    translation_kw = ["translation", "translator", "localization", "proofreading",
                      "writing", "editor", "chinese", "english", "japanese"]

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


async def fetch_freelancer_jobs() -> List[Job]:
    """Scrape job listings from Freelancer.com."""
    jobs = []
    seen_ids = set()
    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
            }

            # Try multiple category pages
            urls = [
                FREELANCER_JOBS_URL,
                "https://www.freelancer.com/jobs/website-design/",
                "https://www.freelancer.com/jobs/python/",
            ]

            for url in urls[:1]:  # Start with main jobs page
                try:
                    resp = await client.get(url, headers=headers)
                    if resp.status_code != 200:
                        continue

                    soup = BeautifulSoup(resp.text, "lxml")

                    # Find job listing items
                    job_items = soup.find_all("div", class_=re.compile(r"JobSearchCard-item|job-card|JobCard"))
                    if not job_items:
                        job_items = soup.find_all("div", attrs={"data-job-id": True})
                    if not job_items:
                        # Try finding by common Freelancer HTML patterns
                        job_items = soup.select(".JobSearchCard-item, [data-component='JobSearchCard']")

                    for item in job_items[:20]:
                        try:
                            # Title
                            title_el = item.find(["h2", "h3", "a"], class_=re.compile(r"title|heading|JobSearchCard-primary-heading"))
                            if not title_el:
                                title_el = item.find("a", href=re.compile(r"/projects/"))
                            if not title_el:
                                continue
                            title = title_el.get_text(strip=True)
                            if not title or len(title) < 5:
                                continue

                            # URL
                            link_el = item.find("a", href=re.compile(r"/projects/"))
                            job_url = ""
                            if link_el:
                                href = link_el.get("href", "")
                                if href.startswith("/"):
                                    job_url = f"https://www.freelancer.com{href}"
                                else:
                                    job_url = href

                            # Description
                            desc_el = item.find(class_=re.compile(r"description|summary|JobSearchCard-primary-description"))
                            description = desc_el.get_text(strip=True) if desc_el else title

                            # Budget
                            budget_el = item.find(class_=re.compile(r"budget|price|amount|JobSearchCard-secondary-price"))
                            budget_text = budget_el.get_text(strip=True) if budget_el else ""
                            budget_min, budget_max = parse_budget(budget_text)

                            # Skills/Tags
                            skill_els = item.find_all(class_=re.compile(r"tag|skill|badge|JobSearchCard-secondary-tag"))
                            skills = [el.get_text(strip=True) for el in skill_els if el.get_text(strip=True)]
                            if not skills:
                                skills = extract_skills_from_text(title + " " + description)

                            category = categorize_from_text(title, description)

                            job_hash = hashlib.md5(f"freelancer-{title}-{job_url}".encode()).hexdigest()[:12]
                            if job_hash in seen_ids:
                                continue
                            seen_ids.add(job_hash)

                            job = Job(
                                id=f"freelancer-{job_hash}",
                                title=title,
                                description=description[:600],
                                source="freelancer",
                                source_url=job_url or FREELANCER_JOBS_URL,
                                budget_min=budget_min,
                                budget_max=budget_max,
                                currency="USD",
                                skills=skills[:6],
                                category=category,
                                posted_at=datetime.utcnow() - timedelta(hours=2),
                                is_remote=True,
                            )
                            jobs.append(job)
                        except Exception:
                            continue
                except Exception as e:
                    print(f"[Freelancer] Error fetching {url}: {e}")
                    continue

    except Exception as e:
        print(f"[Freelancer] General error: {e}")

    return jobs
