import os
import json
import asyncio
from typing import List, Optional
import anthropic
from models import Job, UserPreferences

MODEL_ID = "claude-haiku-4-5-20251001"

CATEGORIES = ["技術開發", "設計創意", "行銷文案", "翻譯文字", "其他"]


async def score_job(
    job: Job,
    preferences: UserPreferences,
    api_key: str,
) -> Job:
    """Score a single job using Claude AI."""
    client = anthropic.Anthropic(api_key=api_key)

    skills_str = ", ".join(preferences.skills) if preferences.skills else "general"
    categories_str = ", ".join(preferences.preferred_categories)

    prompt = f"""你是一個自由接案工作評分助手。請根據用戶偏好對以下工作機會進行評分。

用戶偏好：
- 技能：{skills_str}
- 預算範圍：${preferences.min_budget} - ${preferences.max_budget} USD
- 偏好分類：{categories_str}

工作資訊：
- 標題：{job.title}
- 描述：{job.description[:400]}
- 技能標籤：{', '.join(job.skills) if job.skills else '無'}
- 預算：{f"${job.budget_min} - ${job.budget_max} {job.currency}" if job.budget_min else "未指定"}
- 分類：{job.category}
- 來源：{job.source}

請用以下 JSON 格式回覆（不要添加任何其他文字）：
{{
  "score": <0-10的數字，10為最適合>,
  "reason": "<一句話中文說明評分原因，不超過30字>",
  "category": "<從以下選擇最合適的分類：技術開發、設計創意、行銷文案、翻譯文字、其他>",
  "title_zh": "<工作標題的中文翻譯，如果已是中文則保持原文>"
}}"""

    try:
        response = client.messages.create(
            model=MODEL_ID,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.content[0].text.strip()

        # Clean up response - remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        result = json.loads(content)

        job.ai_score = float(result.get("score", 5.0))
        job.ai_reason = result.get("reason", "")
        if result.get("category") in CATEGORIES:
            job.category = result["category"]
        if result.get("title_zh"):
            job.title_zh = result["title_zh"]

    except json.JSONDecodeError:
        job.ai_score = 5.0
        job.ai_reason = "AI評分暫時不可用"
    except Exception as e:
        print(f"[AI Scorer] Error scoring job {job.id}: {e}")
        job.ai_score = None
        job.ai_reason = None

    return job


async def score_jobs_batch(
    jobs: List[Job],
    preferences: UserPreferences,
    api_key: Optional[str] = None,
    max_jobs: int = 30,
) -> List[Job]:
    """Score a batch of jobs using Claude AI with rate limiting."""
    if not api_key:
        api_key = os.getenv("ANTHROPIC_API_KEY", "")

    if not api_key:
        print("[AI Scorer] No API key available, skipping scoring")
        return jobs

    # Only score jobs that don't have scores yet
    jobs_to_score = [j for j in jobs if j.ai_score is None][:max_jobs]
    already_scored = [j for j in jobs if j.ai_score is not None]

    if not jobs_to_score:
        return jobs

    print(f"[AI Scorer] Scoring {len(jobs_to_score)} jobs...")

    # Process in small batches to avoid rate limits
    batch_size = 5
    scored_jobs = []

    for i in range(0, len(jobs_to_score), batch_size):
        batch = jobs_to_score[i:i + batch_size]
        tasks = [score_job(job, preferences, api_key) for job in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for j, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"[AI Scorer] Error in batch: {result}")
                scored_jobs.append(batch[j])  # Keep unscored
            else:
                scored_jobs.append(result)

        # Rate limiting: short pause between batches
        if i + batch_size < len(jobs_to_score):
            await asyncio.sleep(0.5)

    return already_scored + scored_jobs


async def categorize_and_translate_job(
    job: Job,
    api_key: str,
) -> Job:
    """Categorize job and translate title to Chinese if needed."""
    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""請對以下工作進行分類並翻譯標題。

工作標題：{job.title}
工作描述：{job.description[:300]}

請用以下 JSON 格式回覆：
{{
  "category": "<從以下選擇：技術開發、設計創意、行銷文案、翻譯文字、其他>",
  "title_zh": "<中文標題翻譯，如果已是中文則保持原文>"
}}"""

    try:
        response = client.messages.create(
            model=MODEL_ID,
            max_tokens=128,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0].text.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        result = json.loads(content)
        if result.get("category") in CATEGORIES:
            job.category = result["category"]
        if result.get("title_zh"):
            job.title_zh = result["title_zh"]
    except Exception:
        pass

    return job
