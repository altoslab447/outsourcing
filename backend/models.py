from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class Job(BaseModel):
    id: str
    title: str
    title_zh: Optional[str] = None
    description: str
    description_zh: Optional[str] = None
    source: str  # 'remoteok', 'freelancer', 'weworkremotely', '104'
    source_url: str
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    currency: str = "USD"
    skills: List[str] = []
    category: str  # '技術開發', '設計創意', '行銷文案', '翻譯文字', '其他'
    posted_at: datetime
    ai_score: Optional[float] = None
    ai_reason: Optional[str] = None
    is_remote: bool = True


class UserPreferences(BaseModel):
    skills: List[str] = ["React", "Python", "Node.js", "TypeScript"]
    min_budget: float = 500
    max_budget: float = 10000
    preferred_categories: List[str] = ["技術開發", "設計創意"]
    languages: List[str] = ["English", "Chinese"]
    anthropic_api_key: Optional[str] = None


class JobFilter(BaseModel):
    skills: Optional[List[str]] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    hours: Optional[str] = None  # '24h', '7d', '30d'
    category: Optional[str] = None
    source: Optional[List[str]] = None
    min_ai_score: Optional[float] = None


class StatsResponse(BaseModel):
    total_jobs: int
    by_source: dict
    by_category: dict
    last_updated: Optional[datetime] = None


class CategoryCount(BaseModel):
    category: str
    count: int
