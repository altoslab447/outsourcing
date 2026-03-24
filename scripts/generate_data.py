#!/usr/bin/env python3
"""
每日資料生成腳本
執行所有爬蟲 + AI 評分，輸出 frontend/public/data.json
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from scrapers import (
    fetch_upwork_jobs,
    fetch_freelancer_jobs,
    fetch_peopleperhour_jobs,
)
from ai_scorer import score_jobs_batch
from models import UserPreferences

DEFAULT_PREFERENCES = UserPreferences(
    skills=["React", "Python", "Node.js", "TypeScript", "Vue.js", "Django",
            "FastAPI", "Flutter", "Docker", "AWS", "PHP", "WordPress"],
    min_budget=100,
    max_budget=50000,
    preferred_categories=["技術開發", "設計創意", "行銷文案", "翻譯文字", "其他"],
    languages=["English", "Chinese"],
)

OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'frontend', 'public', 'data.json'
)


async def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 開始抓取外包資料...")

    # 並行抓取所有來源
    results = await asyncio.gather(
        fetch_upwork_jobs(),
        fetch_freelancer_jobs(),
        fetch_peopleperhour_jobs(),
        return_exceptions=True,
    )

    all_jobs = []
    source_names = ["Upwork", "Freelancer", "PeoplePerHour"]

    for name, result in zip(source_names, results):
        if isinstance(result, Exception):
            print(f"[{name}] 抓取失敗: {result}")
        else:
            print(f"[{name}] 抓取到 {len(result)} 筆")
            all_jobs.extend(result)

    print(f"\n總共抓取到 {len(all_jobs)} 筆外包任務")

    # AI 評分
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if api_key:
        print("開始 AI 評分...")
        all_jobs = await score_jobs_batch(
            all_jobs,
            DEFAULT_PREFERENCES,
            api_key=api_key,
            max_jobs=60,
        )
        print("AI 評分完成")
    else:
        print("⚠️  未設定 ANTHROPIC_API_KEY，跳過 AI 評分")

    # 依 AI 評分排序（高分優先），沒有評分的排後面
    all_jobs.sort(
        key=lambda j: (j.ai_score is not None, j.ai_score or 0),
        reverse=True
    )

    # 統計
    by_source = {}
    by_category = {}
    for job in all_jobs:
        by_source[job.source] = by_source.get(job.source, 0) + 1
        by_category[job.category] = by_category.get(job.category, 0) + 1

    # 輸出 JSON
    output = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total": len(all_jobs),
        "by_source": by_source,
        "by_category": by_category,
        "jobs": [
            {
                "id": job.id,
                "title": job.title,
                "title_zh": job.title_zh,
                "description": job.description,
                "description_zh": job.description_zh,
                "source": job.source,
                "source_url": job.source_url,
                "budget_min": job.budget_min,
                "budget_max": job.budget_max,
                "currency": job.currency,
                "skills": job.skills,
                "category": job.category,
                "posted_at": job.posted_at.isoformat(),
                "ai_score": job.ai_score,
                "ai_reason": job.ai_reason,
                "is_remote": job.is_remote,
            }
            for job in all_jobs
        ],
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 完成！輸出至 {OUTPUT_PATH}")
    print(f"   總筆數: {len(all_jobs)}")
    print(f"   各來源: {by_source}")
    print(f"   各分類: {by_category}")


if __name__ == "__main__":
    asyncio.run(main())
