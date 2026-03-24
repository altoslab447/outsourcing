import httpx
import hashlib
import re
import json
from datetime import datetime
from typing import List
from bs4 import BeautifulSoup
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from models import Job

FREELANCERMAP_URLS = [
    "https://www.freelancermap.com/remote-jobs",
    "https://www.freelancermap.com/remote-jobs/programming",
    "https://www.freelancermap.com/remote-jobs/design",
    "https://www.freelancermap.com/remote-jobs/marketing",
]

TECH_KEYWORDS = [
    "developer", "engineer", "software", "backend", "frontend", "fullstack",
    "devops", "cloud", "api", "mobile", "web", "react", "python", "node",
    "javascript", "typescript", "php", "java", "flutter", "django", "sap",
    "aws", "azure", "gcp", "database", "data", "ai", "ml", "security",
]
DESIGN_KEYWORDS = [
    "design", "designer", "ux", "ui", "figma", "graphic", "creative", "visual",
]
MARKETING_KEYWORDS = [
    "marketing", "seo", "content", "copywriting", "social media", "ads",
]
TRANSLATION_KEYWORDS = [
    "translation", "translator", "localization", "writing",
]
JOB_KEYWORDS = [
    "full-time", "permanent", "benefits", "401k", "health insurance",
    "paid vacation", "salaried", "annual salary", "we are hiring",
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


def parse_rate_from_text(text: str):
    """Extract daily/hourly rate and convert to monthly estimate."""
    clean = re.sub(r"<[^>]+>", " ", text)

    # Daily rate: €500/day or 500-600/day
    daily = re.search(r"(\d[\d,]*)\s*[-–]\s*(\d[\d,]*)\s*[€$]?\s*(?:per\s+)?day|[€$]?\s*(\d[\d,]*)\s*[-–]\s*[€$]?\s*(\d[\d,]*)\s*/\s*day", clean, re.IGNORECASE)
    if daily:
        groups = [g for g in daily.groups() if g]
        if len(groups) >= 2:
            lo = float(groups[0].replace(",", ""))
            hi = float(groups[1].replace(",", ""))
            return lo * 20, hi * 20  # ~20 working days/month

    # Hourly rate
    hourly = re.search(r"(\d+)\s*[-–]\s*(\d+)\s*[€$]?\s*/\s*h(?:our|r)?", clean, re.IGNORECASE)
    if hourly:
        lo = float(hourly.group(1))
        hi = float(hourly.group(2))
        return lo * 160, hi * 160  # ~160 hrs/month

    # Single daily rate
    single_day = re.search(r"[€$]\s*(\d[\d,]+)\s*/\s*day|(\d[\d,]+)\s*[€$]?\s*/\s*day", clean, re.IGNORECASE)
    if single_day:
        val = float((single_day.group(1) or single_day.group(2)).replace(",", ""))
        return val * 16, val * 20

    return None, None


def extract_skills_from_project(skills_dict, title: str) -> List[str]:
    """Extract skills from freelancermap's skills object."""
    skill_list = [
        "React", "Vue.js", "Angular", "Node.js", "Python", "JavaScript",
        "TypeScript", "PHP", "Java", "Swift", "Go", "Rust", "Flutter",
        "Django", "Docker", "AWS", "Azure", "GCP", "SAP", "PostgreSQL",
        "MongoDB", "Kubernetes", "Terraform", "Figma", "SEO", "C++", "C#",
        ".NET", "Spring", "Rails", "Linux", "Security",
    ]
    found = []

    # From skills dict
    if isinstance(skills_dict, dict):
        for v in skills_dict.values():
            if isinstance(v, dict):
                name = v.get("en") or v.get("de") or ""
                if name:
                    found.append(name)
    elif isinstance(skills_dict, list):
        for item in skills_dict:
            if isinstance(item, dict):
                name = item.get("en") or item.get("name") or ""
                if name:
                    found.append(name)

    # Also extract from title
    title_lower = title.lower()
    for skill in skill_list:
        if skill.lower() in title_lower and skill not in found:
            found.append(skill)

    return found[:8]


def extract_projects_from_json(data) -> list:
    """Recursively find project arrays in nested JSON."""
    projects = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and "title" in item and "slug" in item:
                projects.append(item)
            else:
                projects.extend(extract_projects_from_json(item))
    elif isinstance(data, dict):
        for v in data.values():
            projects.extend(extract_projects_from_json(v))
    return projects


async def fetch_freelancermap_jobs() -> List[Job]:
    """Scrape freelance projects from FreelancerMap."""
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
        for url in FREELANCERMAP_URLS[:2]:
            try:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "lxml")

                # Find JSON data in script tags
                projects = []
                for script in soup.find_all("script"):
                    content = script.string or ""
                    if not content or "title" not in content:
                        continue
                    # Try to extract JSON objects containing project data
                    matches = re.findall(r'\{[^{}]*"title"\s*:\s*"[^"]{5,}"[^{}]*\}', content)
                    for match in matches:
                        try:
                            obj = json.loads(match)
                            if obj.get("title") and obj.get("slug"):
                                projects.append(obj)
                        except Exception:
                            continue

                    # Also try full JSON parse of script content
                    if not projects:
                        try:
                            # Look for window.__INITIAL_STATE__ or similar
                            state_match = re.search(r'(?:__INITIAL_STATE__|initialData|pageData)\s*=\s*(\{.+\})', content, re.DOTALL)
                            if state_match:
                                data = json.loads(state_match.group(1))
                                projects.extend(extract_projects_from_json(data))
                        except Exception:
                            pass

                # Fallback: parse HTML cards directly
                if not projects:
                    cards = soup.select(".project-card, .job-card, article.project, [class*='projectCard']")
                    for card in cards[:20]:
                        title_el = card.find(["h2", "h3", "h4", "a"])
                        if not title_el:
                            continue
                        title = title_el.get_text(strip=True)
                        link_el = card.find("a", href=True)
                        link = link_el["href"] if link_el else ""
                        if link.startswith("/"):
                            link = f"https://www.freelancermap.com{link}"
                        desc_el = card.find(class_=re.compile(r"desc|summary|body"))
                        description = desc_el.get_text(strip=True) if desc_el else title
                        rate_el = card.find(class_=re.compile(r"rate|budget|price"))
                        rate_text = rate_el.get_text(strip=True) if rate_el else ""
                        budget_min, budget_max = parse_rate_from_text(rate_text)
                        projects.append({
                            "title": title,
                            "slug": hashlib.md5(title.encode()).hexdigest()[:8],
                            "description": description,
                            "links": {"project": link.replace("https://www.freelancermap.com", "")},
                            "budget_min": budget_min,
                            "budget_max": budget_max,
                        })

                for proj in projects[:25]:
                    try:
                        title = proj.get("title", "").strip()
                        if not title or len(title) < 5:
                            continue

                        slug = proj.get("slug", "")
                        link_path = (proj.get("links") or {}).get("project", f"/project/{slug}")
                        job_url = f"https://www.freelancermap.com{link_path}" if link_path.startswith("/") else link_path

                        description = proj.get("description", title)
                        if isinstance(description, str):
                            description = re.sub(r"<[^>]+>", " ", description).strip()
                            description = re.sub(r"\s+", " ", description)

                        if is_job_listing(title, description):
                            continue

                        job_hash = hashlib.md5(f"flm-{slug}-{title}".encode()).hexdigest()[:12]
                        if job_hash in seen_ids:
                            continue
                        seen_ids.add(job_hash)

                        # Budget
                        budget_min = proj.get("budget_min")
                        budget_max = proj.get("budget_max")
                        if not budget_min:
                            budget_min, budget_max = parse_rate_from_text(description)

                        # Convert EUR to USD (rough estimate)
                        if budget_min:
                            budget_min = round(budget_min * 1.08, 0)
                        if budget_max:
                            budget_max = round(budget_max * 1.08, 0)

                        # Date
                        created = proj.get("created", "")
                        try:
                            posted_at = datetime.fromisoformat(created.replace("Z", "+00:00")).replace(tzinfo=None)
                        except Exception:
                            posted_at = datetime.utcnow()

                        skills = extract_skills_from_project(proj.get("skills"), title)
                        category = categorize(title, description)

                        job = Job(
                            id=f"flm-{job_hash}",
                            title=title,
                            description=description[:700],
                            source="freelancermap",
                            source_url=job_url,
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
                print(f"[FreelancerMap] Error fetching {url}: {e}")
                continue

    print(f"[FreelancerMap] 抓取到 {len(jobs)} 筆接案任務")
    return jobs
