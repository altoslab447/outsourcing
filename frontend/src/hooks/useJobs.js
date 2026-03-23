import { useState, useEffect, useCallback, useMemo } from 'react'

const DEFAULT_SETTINGS = {
  skills: ["React", "Python", "Node.js", "TypeScript"],
  min_budget: 0,
  max_budget: 50000,
  preferred_categories: ["技術開發", "設計創意"],
  languages: ["English", "Chinese"],
}

// 讀取 / 儲存設定到 localStorage
function loadSettings() {
  try {
    const saved = localStorage.getItem('freelance_settings')
    return saved ? { ...DEFAULT_SETTINGS, ...JSON.parse(saved) } : DEFAULT_SETTINGS
  } catch {
    return DEFAULT_SETTINGS
  }
}

function saveSettingsToStorage(settings) {
  try {
    localStorage.setItem('freelance_settings', JSON.stringify(settings))
  } catch {}
}

// 篩選邏輯（全在瀏覽器端執行）
function filterJobs(allJobs, filters) {
  return allJobs.filter(job => {
    // 分類篩選
    if (filters.category && filters.category !== '全部') {
      if (job.category !== filters.category) return false
    }

    // 來源篩選
    if (filters.sources?.length) {
      if (!filters.sources.includes(job.source)) return false
    }

    // 預算篩選（只有有標示預算的才篩選）
    if (filters.budget_min != null && filters.budget_min > 0) {
      if (job.budget_max != null && job.budget_max < filters.budget_min) return false
    }
    if (filters.budget_max != null && filters.budget_max < 50000) {
      if (job.budget_min != null && job.budget_min > filters.budget_max) return false
    }

    // 技能篩選
    if (filters.skills?.length) {
      const jobSkills = (job.skills || []).map(s => s.toLowerCase())
      const match = filters.skills.some(s => jobSkills.includes(s.toLowerCase()))
      if (!match) return false
    }

    // AI 評分篩選
    if (filters.min_ai_score != null && filters.min_ai_score > 0) {
      if ((job.ai_score ?? 0) < filters.min_ai_score) return false
    }

    // 時間篩選
    if (filters.hours && filters.hours !== 'all') {
      const hoursMap = { '24h': 24, '7d': 168, '30d': 720 }
      const hours = hoursMap[filters.hours]
      if (hours) {
        const postedAt = new Date(job.posted_at)
        const diffHours = (Date.now() - postedAt.getTime()) / 3600000
        if (diffHours > hours) return false
      }
    }

    return true
  })
}

export function useJobs(filters = {}) {
  const [allJobs, setAllJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [generatedAt, setGeneratedAt] = useState(null)
  const [rawStats, setRawStats] = useState(null)

  // 載入靜態 data.json
  useEffect(() => {
    setLoading(true)
    setError(null)
    fetch('/data.json')
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then(data => {
        setAllJobs(data.jobs || [])
        setGeneratedAt(data.generated_at ? new Date(data.generated_at) : null)
        setRawStats({ by_source: data.by_source, by_category: data.by_category, total: data.total })
      })
      .catch(err => {
        console.error('Failed to load data.json:', err)
        setError('無法載入資料，請稍後再試')
      })
      .finally(() => setLoading(false))
  }, [])

  // 瀏覽器端篩選
  const jobs = useMemo(() => filterJobs(allJobs, filters), [allJobs, filters])

  // 計算目前篩選後的統計
  const stats = useMemo(() => {
    if (!rawStats) return null
    const by_source = {}
    const by_category = {}
    jobs.forEach(j => {
      by_source[j.source] = (by_source[j.source] || 0) + 1
      by_category[j.category] = (by_category[j.category] || 0) + 1
    })
    return {
      total_jobs: jobs.length,
      by_source,
      by_category,
      last_updated: generatedAt?.toISOString(),
    }
  }, [jobs, rawStats, generatedAt])

  // 分類列表（從資料自動產生）
  const categories = useMemo(() => {
    const cats = {}
    allJobs.forEach(j => { cats[j.category] = (cats[j.category] || 0) + 1 })
    return Object.entries(cats).map(([category, count]) => ({ category, count }))
  }, [allJobs])

  return {
    jobs,
    loading,
    error,
    stats,
    categories,
    lastUpdated: generatedAt,
    isRefreshing: false,
    fetchJobs: () => {},   // 靜態版本不需要
    refresh: () => {},     // 靜態版本不需要
    fetchStats: () => {},
  }
}

export function useSettings() {
  const [settings, setSettings] = useState(loadSettings)
  const [loading] = useState(false)
  const [saving, setSaving] = useState(false)

  const saveSettings = useCallback(async (newSettings) => {
    setSaving(true)
    try {
      const merged = { ...newSettings }
      delete merged.anthropic_api_key  // 靜態版本不需要 API key
      saveSettingsToStorage(merged)
      setSettings(merged)
      return merged
    } finally {
      setSaving(false)
    }
  }, [])

  return { settings, loading, saving, saveSettings, fetchSettings: () => {} }
}
