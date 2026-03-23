import { useState, useEffect, useCallback, useRef } from 'react'
import axios from 'axios'

const API_BASE = '/api'

export function useJobs(filters = {}) {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [stats, setStats] = useState(null)
  const [categories, setCategories] = useState([])
  const [lastUpdated, setLastUpdated] = useState(null)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const abortControllerRef = useRef(null)

  const fetchJobs = useCallback(async (currentFilters = {}) => {
    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    abortControllerRef.current = new AbortController()

    setLoading(true)
    setError(null)

    try {
      const params = new URLSearchParams()

      if (currentFilters.skills?.length) {
        params.set('skills', currentFilters.skills.join(','))
      }
      if (currentFilters.budget_min != null && currentFilters.budget_min > 0) {
        params.set('budget_min', currentFilters.budget_min)
      }
      if (currentFilters.budget_max != null && currentFilters.budget_max < 20000) {
        params.set('budget_max', currentFilters.budget_max)
      }
      if (currentFilters.hours && currentFilters.hours !== 'all') {
        params.set('hours', currentFilters.hours)
      }
      if (currentFilters.category && currentFilters.category !== '全部') {
        params.set('category', currentFilters.category)
      }
      if (currentFilters.sources?.length) {
        params.set('source', currentFilters.sources.join(','))
      }
      if (currentFilters.min_ai_score != null && currentFilters.min_ai_score > 0) {
        params.set('min_ai_score', currentFilters.min_ai_score)
      }

      const response = await axios.get(`${API_BASE}/jobs?${params.toString()}`, {
        signal: abortControllerRef.current.signal,
      })
      setJobs(response.data)
    } catch (err) {
      if (err.name !== 'CanceledError' && err.code !== 'ERR_CANCELED') {
        console.error('Failed to fetch jobs:', err)
        setError('無法載入工作資料，請稍後再試')
      }
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchStats = useCallback(async () => {
    try {
      const [statsRes, catsRes] = await Promise.all([
        axios.get(`${API_BASE}/stats`),
        axios.get(`${API_BASE}/categories`),
      ])
      setStats(statsRes.data)
      setCategories(catsRes.data)
      if (statsRes.data.last_updated) {
        setLastUpdated(new Date(statsRes.data.last_updated))
      }
    } catch (err) {
      console.error('Failed to fetch stats:', err)
    }
  }, [])

  const refresh = useCallback(async () => {
    setIsRefreshing(true)
    try {
      await axios.post(`${API_BASE}/refresh`)
      // Wait a moment for the background task to start
      await new Promise(resolve => setTimeout(resolve, 1500))
      await fetchJobs(filters)
      await fetchStats()
    } catch (err) {
      console.error('Failed to refresh:', err)
    } finally {
      setIsRefreshing(false)
    }
  }, [fetchJobs, fetchStats, filters])

  // Initial load
  useEffect(() => {
    fetchJobs(filters)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    fetchStats()
  }, [fetchStats])

  // Poll for stats every 2 minutes
  useEffect(() => {
    const interval = setInterval(fetchStats, 120000)
    return () => clearInterval(interval)
  }, [fetchStats])

  return {
    jobs,
    loading,
    error,
    stats,
    categories,
    lastUpdated,
    isRefreshing,
    fetchJobs,
    refresh,
    fetchStats,
  }
}

export function useSettings() {
  const [settings, setSettings] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  const fetchSettings = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE}/settings`)
      setSettings(res.data)
    } catch (err) {
      console.error('Failed to fetch settings:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  const saveSettings = useCallback(async (newSettings) => {
    setSaving(true)
    try {
      const res = await axios.post(`${API_BASE}/settings`, newSettings)
      setSettings(newSettings)
      return res.data
    } catch (err) {
      console.error('Failed to save settings:', err)
      throw err
    } finally {
      setSaving(false)
    }
  }, [])

  useEffect(() => {
    fetchSettings()
  }, [fetchSettings])

  return { settings, loading, saving, saveSettings, fetchSettings }
}
