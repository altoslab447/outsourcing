import React, { useState, useRef } from 'react'
import clsx from 'clsx'

const SUGGESTED_SKILLS = [
  'React', 'Vue.js', 'Angular', 'Node.js', 'Python', 'JavaScript',
  'TypeScript', 'PHP', 'Java', 'Ruby', 'Go', 'Rust', 'Flutter',
  'Django', 'FastAPI', 'Laravel', 'WordPress', 'Shopify',
  'Docker', 'Kubernetes', 'AWS', 'GCP', 'Azure',
  'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'GraphQL',
  'Figma', 'Photoshop', 'Illustrator', 'UI/UX',
  'SEO', 'Google Ads', 'Content Marketing', 'Copywriting',
  'Translation', 'Chinese', 'Japanese',
]

const SOURCE_OPTIONS = [
  { value: 'remoteok', label: 'RemoteOK', color: 'text-emerald-400' },
  { value: 'freelancer', label: 'Freelancer', color: 'text-blue-400' },
  { value: 'weworkremotely', label: 'WeWorkRemotely', color: 'text-red-400' },
  { value: '104', label: '104人力銀行', color: 'text-orange-400' },
]

const TIME_OPTIONS = [
  { value: 'all', label: '全部' },
  { value: '24h', label: '24小時內' },
  { value: '7d', label: '7天內' },
  { value: '30d', label: '30天內' },
]

export default function FilterPanel({ filters, onFiltersChange, onApply, onReset }) {
  const [localFilters, setLocalFilters] = useState(filters)
  const [skillInput, setSkillInput] = useState('')
  const [showSuggestions, setShowSuggestions] = useState(false)
  const skillInputRef = useRef(null)

  const filteredSuggestions = SUGGESTED_SKILLS.filter(
    s =>
      s.toLowerCase().includes(skillInput.toLowerCase()) &&
      !localFilters.skills.includes(s)
  ).slice(0, 8)

  const addSkill = (skill) => {
    if (!localFilters.skills.includes(skill)) {
      setLocalFilters(prev => ({ ...prev, skills: [...prev.skills, skill] }))
    }
    setSkillInput('')
    setShowSuggestions(false)
  }

  const removeSkill = (skill) => {
    setLocalFilters(prev => ({
      ...prev,
      skills: prev.skills.filter(s => s !== skill),
    }))
  }

  const handleSkillKeyDown = (e) => {
    if (e.key === 'Enter' && skillInput.trim()) {
      e.preventDefault()
      addSkill(skillInput.trim())
    }
    if (e.key === 'Escape') {
      setShowSuggestions(false)
    }
  }

  const toggleSource = (source) => {
    setLocalFilters(prev => {
      const sources = prev.sources.includes(source)
        ? prev.sources.filter(s => s !== source)
        : [...prev.sources, source]
      return { ...prev, sources }
    })
  }

  const handleApply = () => {
    onFiltersChange(localFilters)
    onApply(localFilters)
  }

  const handleReset = () => {
    const defaultFilters = {
      skills: [],
      budget_min: 0,
      budget_max: 20000,
      hours: 'all',
      sources: ['remoteok', 'freelancer', 'weworkremotely', '104'],
      min_ai_score: 0,
    }
    setLocalFilters(defaultFilters)
    onFiltersChange(defaultFilters)
    onReset(defaultFilters)
  }

  return (
    <div className="card p-5 space-y-5">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-200 flex items-center gap-2">
          <svg className="w-4 h-4 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2a1 1 0 01-.293.707L13 13.414V19a1 1 0 01-.553.894l-4 2A1 1 0 017 21v-7.586L3.293 6.707A1 1 0 013 6V4z" />
          </svg>
          篩選條件
        </h3>
        <button
          onClick={handleReset}
          className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
        >
          重置
        </button>
      </div>

      {/* Skills */}
      <div className="space-y-2">
        <label className="text-xs font-medium text-gray-400 uppercase tracking-wide">
          技能篩選
        </label>
        <div className="relative">
          <input
            ref={skillInputRef}
            type="text"
            value={skillInput}
            onChange={e => {
              setSkillInput(e.target.value)
              setShowSuggestions(true)
            }}
            onFocus={() => setShowSuggestions(true)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
            onKeyDown={handleSkillKeyDown}
            placeholder="輸入技能並按 Enter..."
            className="input-field w-full text-sm"
          />
          {showSuggestions && skillInput && filteredSuggestions.length > 0 && (
            <div className="absolute z-20 w-full mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-xl overflow-hidden">
              {filteredSuggestions.map(skill => (
                <button
                  key={skill}
                  onMouseDown={() => addSkill(skill)}
                  className="w-full text-left px-3 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
                >
                  {skill}
                </button>
              ))}
            </div>
          )}
        </div>
        {localFilters.skills.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {localFilters.skills.map(skill => (
              <span key={skill} className="tag">
                {skill}
                <button
                  onClick={() => removeSkill(skill)}
                  className="ml-1 text-gray-500 hover:text-red-400 transition-colors"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Budget Range */}
      <div className="space-y-2">
        <label className="text-xs font-medium text-gray-400 uppercase tracking-wide">
          預算範圍 (USD)
        </label>
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-500 w-6">最低</span>
            <input
              type="range"
              min="0"
              max="20000"
              step="500"
              value={localFilters.budget_min}
              onChange={e => setLocalFilters(prev => ({ ...prev, budget_min: Number(e.target.value) }))}
              className="flex-1"
            />
            <span className="text-xs text-blue-400 font-mono w-16 text-right">
              ${localFilters.budget_min.toLocaleString()}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-500 w-6">最高</span>
            <input
              type="range"
              min="0"
              max="20000"
              step="500"
              value={localFilters.budget_max}
              onChange={e => setLocalFilters(prev => ({ ...prev, budget_max: Number(e.target.value) }))}
              className="flex-1"
            />
            <span className="text-xs text-blue-400 font-mono w-16 text-right">
              {localFilters.budget_max >= 20000 ? '不限' : `$${localFilters.budget_max.toLocaleString()}`}
            </span>
          </div>
        </div>
      </div>

      {/* Time Filter */}
      <div className="space-y-2">
        <label className="text-xs font-medium text-gray-400 uppercase tracking-wide">
          發布時間
        </label>
        <div className="grid grid-cols-2 gap-1.5">
          {TIME_OPTIONS.map(opt => (
            <button
              key={opt.value}
              onClick={() => setLocalFilters(prev => ({ ...prev, hours: opt.value }))}
              className={clsx(
                'text-xs px-3 py-1.5 rounded-lg border transition-colors duration-150',
                localFilters.hours === opt.value
                  ? 'bg-blue-600 border-blue-600 text-white'
                  : 'bg-gray-800 border-gray-700 text-gray-400 hover:text-gray-200 hover:border-gray-600'
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Sources */}
      <div className="space-y-2">
        <label className="text-xs font-medium text-gray-400 uppercase tracking-wide">
          資料來源
        </label>
        <div className="space-y-1.5">
          {SOURCE_OPTIONS.map(opt => {
            const isChecked = localFilters.sources.includes(opt.value)
            return (
              <label
                key={opt.value}
                className="flex items-center gap-2.5 cursor-pointer group"
              >
                <div
                  onClick={() => toggleSource(opt.value)}
                  className={clsx(
                    'w-4 h-4 rounded border-2 flex items-center justify-center transition-colors',
                    isChecked
                      ? 'bg-blue-600 border-blue-600'
                      : 'border-gray-600 bg-gray-800 group-hover:border-gray-500'
                  )}
                >
                  {isChecked && (
                    <svg className="w-2.5 h-2.5 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd" />
                    </svg>
                  )}
                </div>
                <span className={clsx('text-sm', opt.color)}>{opt.label}</span>
              </label>
            )
          })}
        </div>
      </div>

      {/* Min AI Score */}
      <div className="space-y-2">
        <label className="text-xs font-medium text-gray-400 uppercase tracking-wide">
          最低 AI 評分
        </label>
        <div className="flex items-center gap-3">
          <input
            type="range"
            min="0"
            max="10"
            step="0.5"
            value={localFilters.min_ai_score}
            onChange={e => setLocalFilters(prev => ({ ...prev, min_ai_score: Number(e.target.value) }))}
            className="flex-1"
          />
          <span className={clsx(
            'text-sm font-bold font-mono w-8 text-right',
            localFilters.min_ai_score >= 8 ? 'text-green-400' :
            localFilters.min_ai_score >= 5 ? 'text-yellow-400' : 'text-gray-400'
          )}>
            {localFilters.min_ai_score > 0 ? localFilters.min_ai_score : '不限'}
          </span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2 pt-1">
        <button
          onClick={handleApply}
          className="flex-1 btn-primary text-sm py-2"
        >
          套用篩選
        </button>
        <button
          onClick={handleReset}
          className="btn-secondary text-sm py-2 px-3"
        >
          重置
        </button>
      </div>
    </div>
  )
}
