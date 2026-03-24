import React, { useState, useCallback } from 'react'
import clsx from 'clsx'
import { useJobs, useSettings } from '../hooks/useJobs'
import StatsBar from './StatsBar'
import CategoryTabs from './CategoryTabs'
import FilterPanel from './FilterPanel'
import JobCard, { JobCardSkeleton } from './JobCard'
import SettingsModal from './SettingsModal'

const DEFAULT_FILTERS = {
  skills: [],
  budget_min: 0,
  budget_max: 20000,
  hours: 'all',
  sources: ['freelancer', 'guru', 'peopleperhour', 'freelancermap'],
  min_ai_score: 0,
}

function EmptyState({ hasFilters }) {
  return (
    <div className="col-span-full flex flex-col items-center justify-center py-24 text-center">
      <div className="w-16 h-16 bg-gray-800 rounded-2xl flex items-center justify-center mb-4">
        <svg className="w-8 h-8 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>
      <h3 className="text-gray-400 font-medium mb-1">
        {hasFilters ? '找不到符合條件的職缺' : '尚無職缺資料'}
      </h3>
      <p className="text-gray-600 text-sm">
        {hasFilters ? '請嘗試放寬篩選條件' : '請點擊「立即更新」載入職缺'}
      </p>
    </div>
  )
}

export default function Dashboard() {
  const [activeCategory, setActiveCategory] = useState('全部')
  const [filters, setFilters] = useState(DEFAULT_FILTERS)
  const [showFilters, setShowFilters] = useState(false)
  const [showSettings, setShowSettings] = useState(false)

  const {
    jobs,
    loading,
    error,
    stats,
    categories,
    lastUpdated,
    isRefreshing,
    fetchJobs,
    refresh,
  } = useJobs(filters)

  const { settings, saving, saveSettings } = useSettings()

  const handleCategoryChange = useCallback((cat) => {
    setActiveCategory(cat)
    const newFilters = { ...filters, category: cat === '全部' ? undefined : cat }
    fetchJobs({ ...newFilters, category: cat })
  }, [filters, fetchJobs])

  const handleApplyFilters = useCallback((newFilters) => {
    const filtersWithCategory = { ...newFilters, category: activeCategory }
    fetchJobs(filtersWithCategory)
  }, [activeCategory, fetchJobs])

  const handleResetFilters = useCallback((defaultFilters) => {
    setActiveCategory('全部')
    fetchJobs({ ...defaultFilters, category: undefined })
  }, [fetchJobs])

  const hasActiveFilters =
    filters.skills.length > 0 ||
    filters.budget_min > 0 ||
    filters.budget_max < 20000 ||
    filters.hours !== 'all' ||
    filters.sources.length < 4 ||
    filters.min_ai_score > 0

  return (
    <div className="min-h-screen bg-gray-950">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-gray-950/95 backdrop-blur-sm border-b border-gray-800/50">
        <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Logo */}
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center flex-shrink-0">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <div>
              <h1 className="text-base font-bold text-gradient leading-none">接案雷達</h1>
              <p className="text-xs text-gray-600">Freelance Finder</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Filter toggle on mobile */}
            <button
              onClick={() => setShowFilters(prev => !prev)}
              className={clsx(
                'lg:hidden flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border transition-colors',
                showFilters
                  ? 'bg-blue-600 border-blue-600 text-white'
                  : 'bg-gray-800 border-gray-700 text-gray-400 hover:text-gray-200'
              )}
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2a1 1 0 01-.293.707L13 13.414V19a1 1 0 01-.553.894l-4 2A1 1 0 017 21v-7.586L3.293 6.707A1 1 0 013 6V4z" />
              </svg>
              篩選
              {hasActiveFilters && (
                <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
              )}
            </button>

            {/* Settings */}
            <button
              onClick={() => setShowSettings(true)}
              className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-gray-800 border border-gray-700 text-gray-400 hover:text-gray-200 hover:bg-gray-700 transition-colors"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              設定
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 py-5 space-y-4">
        {/* Stats Bar */}
        <StatsBar
          stats={stats}
          lastUpdated={lastUpdated}
          isRefreshing={isRefreshing}
          onRefresh={refresh}
        />

        {/* Category Tabs */}
        <CategoryTabs
          categories={categories}
          activeCategory={activeCategory}
          onCategoryChange={handleCategoryChange}
        />

        {/* Main Layout */}
        <div className="flex gap-5">
          {/* Filter Panel - Desktop sidebar */}
          <aside className={clsx(
            'w-64 flex-shrink-0',
            'hidden lg:block',
          )}>
            <div className="sticky top-24">
              <FilterPanel
                filters={filters}
                onFiltersChange={setFilters}
                onApply={handleApplyFilters}
                onReset={handleResetFilters}
              />
            </div>
          </aside>

          {/* Filter Panel - Mobile overlay */}
          {showFilters && (
            <div className="lg:hidden fixed inset-x-0 top-[57px] z-30 bg-gray-950 border-b border-gray-800 p-4 shadow-2xl">
              <FilterPanel
                filters={filters}
                onFiltersChange={setFilters}
                onApply={(f) => { handleApplyFilters(f); setShowFilters(false) }}
                onReset={(f) => { handleResetFilters(f); setShowFilters(false) }}
              />
            </div>
          )}

          {/* Job Grid */}
          <main className="flex-1 min-w-0">
            {/* Job count & sort info */}
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm text-gray-500">
                {loading ? '載入中...' : (
                  <>
                    顯示 <span className="text-gray-300 font-medium">{jobs.length}</span> 個接案任務
                    {activeCategory !== '全部' && (
                      <span className="ml-1 text-blue-400">· {activeCategory}</span>
                    )}
                  </>
                )}
              </p>
              {hasActiveFilters && (
                <button
                  onClick={() => {
                    setFilters(DEFAULT_FILTERS)
                    setActiveCategory('全部')
                    fetchJobs(DEFAULT_FILTERS)
                  }}
                  className="text-xs text-gray-500 hover:text-red-400 transition-colors flex items-center gap-1"
                >
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  清除所有篩選
                </button>
              )}
            </div>

            {error && (
              <div className="card p-4 mb-4 border-red-800 bg-red-900/20 text-red-400 text-sm flex items-center gap-2">
                <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {error}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {loading ? (
                Array.from({ length: 9 }).map((_, i) => (
                  <JobCardSkeleton key={i} />
                ))
              ) : jobs.length === 0 ? (
                <EmptyState hasFilters={hasActiveFilters} />
              ) : (
                jobs.map(job => (
                  <JobCard key={job.id} job={job} />
                ))
              )}
            </div>

            {/* Load more hint */}
            {!loading && jobs.length >= 50 && (
              <div className="text-center mt-8 text-gray-600 text-sm">
                顯示前 50 筆結果，請使用篩選條件縮小範圍
              </div>
            )}
          </main>
        </div>
      </div>

      {/* Settings Modal */}
      <SettingsModal
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
        settings={settings}
        onSave={saveSettings}
        saving={saving}
      />
    </div>
  )
}
