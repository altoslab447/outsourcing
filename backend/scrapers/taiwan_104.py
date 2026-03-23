import httpx
import hashlib
import json
import re
from datetime import datetime, timedelta
from typing import List
from bs4 import BeautifulSoup
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from models import Job

TAIWAN_104_API = "https://www.104.com.tw/jobs/search/api/jobs"
TAIWAN_104_SEARCH_URL = "https://www.104.com.tw/jobs/search/"


def categorize_104_job(job_name: str, description: str) -> str:
    combined = (job_name + " " + description).lower()
    tech_kw = [
        "工程師", "開發", "程式", "軟體", "後端", "前端", "全端", "app",
        "系統", "資料庫", "雲端", "網站", "web", "react", "python", "java",
        "javascript", "typescript", "php", "node", "devops", "api", "技術",
    ]
    design_kw = [
        "設計師", "ui", "ux", "視覺", "美術", "平面", "插畫", "動畫",
        "影片", "figma", "photoshop", "illustrator", "品牌", "廣告設計",
    ]
    marketing_kw = [
        "行銷", "文案", "seo", "社群", "廣告", "內容", "公關", "品牌行銷",
        "數位行銷", "email", "成長", "電商",
    ]
    translation_kw = [
        "翻譯", "口譯", "筆譯", "英文", "日文", "韓文", "本地化",
        "中英", "校稿", "編輯",
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


def extract_skills_104(text: str) -> List[str]:
    skills = []
    skill_map = {
        "react": "React",
        "vue": "Vue.js",
        "angular": "Angular",
        "python": "Python",
        "java ": "Java",
        "javascript": "JavaScript",
        "typescript": "TypeScript",
        "php": "PHP",
        "node.js": "Node.js",
        "mysql": "MySQL",
        "postgresql": "PostgreSQL",
        "mongodb": "MongoDB",
        "docker": "Docker",
        "aws": "AWS",
        "figma": "Figma",
        "photoshop": "Photoshop",
        "illustrator": "Illustrator",
        "wordpress": "WordPress",
        "shopify": "Shopify",
        "sketch": "Sketch",
    }
    text_lower = text.lower()
    for kw, skill_name in skill_map.items():
        if kw in text_lower:
            skills.append(skill_name)
    return skills[:6]


async def fetch_104_jobs() -> List[Job]:
    """Scrape freelance/outsourcing jobs from 104.com.tw."""
    jobs = []
    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
                "Referer": "https://www.104.com.tw/",
            }

            # Search for freelance/outsource positions
            search_queries = ["外包", "接案", "兼職"]
            for query in search_queries[:2]:
                try:
                    params = {
                        "keyword": query,
                        "jobsource": "2018indexpoc",
                        "ro": "0",
                        "jobtype": "3",  # part-time/freelance
                        "order": "15",   # newest first
                        "asc": "0",
                        "s9": "1",       # remote work
                        "page": "1",
                        "mode": "s",
                        "langFlag": "0",
                        "langStatus": "0",
                        "recommendJob": "1",
                        "hotJob": "1",
                    }

                    resp = await client.get(
                        TAIWAN_104_API,
                        params=params,
                        headers=headers,
                    )

                    if resp.status_code != 200:
                        continue

                    data = resp.json()
                    raw_data = data.get("data", [])
                    # API returns data as a list directly, or as a dict with a 'list' key
                    if isinstance(raw_data, list):
                        job_list = raw_data
                    elif isinstance(raw_data, dict):
                        job_list = raw_data.get("list", [])
                    else:
                        job_list = []

                    for item in job_list[:10]:
                        try:
                            job_no = item.get("jobNo", "")
                            if not job_no:
                                continue

                            title = item.get("jobName", "")
                            if not title:
                                continue

                            company = item.get("custName", "")
                            description_parts = [
                                item.get("jobAddrNoDesc", ""),
                                item.get("optionEdu", ""),
                                f"公司: {company}" if company else "",
                            ]
                            description = " | ".join(p for p in description_parts if p)
                            if not description:
                                description = title

                            # Salary info
                            salary_low = item.get("salaryLow", 0)
                            salary_high = item.get("salaryHigh", 0)
                            budget_min = float(salary_low) if salary_low else None
                            budget_max = float(salary_high) if salary_high else None

                            # Job URL
                            job_url = f"https://www.104.com.tw/job/{job_no}"

                            # Date - 104 API returns relative time strings
                            appear_date = item.get("appearDate", "")
                            posted_at = datetime.utcnow()
                            if appear_date:
                                try:
                                    # Format: "YYYY/MM/DD"
                                    posted_at = datetime.strptime(appear_date, "%Y/%m/%d")
                                except Exception:
                                    pass

                            category = categorize_104_job(title, description)
                            skills = extract_skills_104(title + " " + description)

                            # Add common skills from job tags
                            tags = item.get("tags", {})
                            if isinstance(tags, dict):
                                for tag_list in tags.values():
                                    if isinstance(tag_list, list):
                                        for tag in tag_list:
                                            if isinstance(tag, dict):
                                                skill_name = tag.get("name", "")
                                            else:
                                                skill_name = str(tag)
                                            if skill_name and len(skill_name) <= 20:
                                                skills.append(skill_name)

                            job_hash = hashlib.md5(f"104-{job_no}".encode()).hexdigest()[:12]

                            job = Job(
                                id=f"104-{job_hash}",
                                title=title,
                                description=description[:600],
                                source="104",
                                source_url=job_url,
                                budget_min=budget_min,
                                budget_max=budget_max,
                                currency="TWD",
                                skills=list(dict.fromkeys(skills))[:6],
                                category=category,
                                posted_at=posted_at,
                                is_remote=True,
                            )
                            jobs.append(job)
                        except Exception:
                            continue

                except Exception as e:
                    print(f"[104] Error searching '{query}': {e}")
                    continue

    except Exception as e:
        print(f"[104] General error: {e}")

    # Deduplicate by ID
    seen = set()
    unique_jobs = []
    for job in jobs:
        if job.id not in seen:
            seen.add(job.id)
            unique_jobs.append(job)

    return unique_jobs
