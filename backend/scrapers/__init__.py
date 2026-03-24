# Scrapers package - freelance project platforms only
from .upwork import fetch_upwork_jobs
from .freelancer import fetch_freelancer_jobs
from .peopleperhour import fetch_peopleperhour_jobs
from .freelancermap import fetch_freelancermap_jobs

__all__ = [
    "fetch_upwork_jobs",
    "fetch_freelancer_jobs",
    "fetch_peopleperhour_jobs",
    "fetch_freelancermap_jobs",
]
