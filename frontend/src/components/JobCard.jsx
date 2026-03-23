import React, { useState } from 'react'
import { formatDistanceToNow } from 'date-fns'
import { zhTW } from 'date-fns/locale'
import clsx from 'clsx'

const SOURCE_STYLES = {
  remoteok: {
    bg: 'bg-emerald-900/50',
    text: 'text-emerald-400',
    border: 'border-emerald-800',
    label: 'RemoteOK',
  },
  freelancer: {
    bg: 'bg-blue-900/50',
    text: 'text-blue-400',
    border: 'border-blue-800',
    label: 'Freelancer',
  },
  weworkremotely: {
    bg: 'bg-red-900/50',
    text: 'text-red-400',
    border: 'border-red-800',
    label: 'WeWork',
  },
  '104': {
    bg: 'bg-orange-900/50',
    text: 'text-orange-400',
    border: 'border-orange-800',
    label: '104',
  },
}

const CATEGORY_STYLES = {
  '技術開發': { bg: 'bg-blue-900/40', text: 'text-blue-300', border: 'border-blue-800/50' },
  '設計創意': { bg: 'bg-purple-900/40', text: 'text-purple-300', border: 'border-purple-800/50' },
  '行銷文案': { bg: 'bg-green-900/40', text: 'text-green-300', border: 'border-green-800/50' },
  '翻譯文字': { bg: 'bg-yellow-900/40', text: 'text-yellow-300', border: 'border-yellow-800/50' },
  '其他': { bg: 'bg-gray-800/40', text: 'text-gray-300', border: 'border-gray-700/50' },
}

function ScoreBadge({ score, reason }) {
  const [showTooltip, setShowTooltip] = useState(false)

  if (score === null || score === undefined) {
    return (
      <span className="badge bg-gray-800 text-gray-500 border border-gray-700">
        AI N/A
      </span>
    )
  }

  const scoreColor =
    score >= 8 ? 'bg-green-900/60 text-green-400 border-green-700/50' :
    score >= 5 ? 'bg-yellow-900/60 text-yellow-400 border-yellow-700/50' :
    'bg-red-900/60 text-red-400 border-red-700/50'

  return (
    <div className="relative">
      <button
        className={clsx('badge border font-mono cursor-help', scoreColor)}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        AI {score.toFixed(1)}
      </button>
      {showTooltip && reason && (
        <div className="absolute bottom-full right-0 mb-2 z-30 w-52">
          <div className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 shadow-xl">
            <p className="text-xs text-gray-300 leading-relaxed">{reason}</p>
          </div>
          <div className="absolute -bottom-1 right-3 w-2 h-2 bg-gray-800 border-r border-b border-gray-700 rotate-45" />
        </div>
      )}
    </div>
  )
}

function formatBudget(min, max, currency) {
  if (!min && !max) return null

  const formatNum = (n) => {
    if (currency === 'TWD') {
      return `NT$${Math.round(n / 1000)}K`
    }
    if (n >= 1000) return `$${(n / 1000).toFixed(1)}K`
    return `$${Math.round(n)}`
  }

  const suffix = currency === 'TWD' ? '' : ' USD'
  if (min && max) return `${formatNum(min)} – ${formatNum(max)}${suffix}`
  if (min) return `${formatNum(min)}+${suffix}`
  if (max) return `最高 ${formatNum(max)}${suffix}`
  return null
}

function formatRelativeTime(dateStr) {
  try {
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) return '未知時間'
    return formatDistanceToNow(date, { addSuffix: true, locale: zhTW })
  } catch {
    return '未知時間'
  }
}

export default function JobCard({ job }) {
  const sourceStyle = SOURCE_STYLES[job.source] || SOURCE_STYLES['remoteok']
  const categoryStyle = CATEGORY_STYLES[job.category] || CATEGORY_STYLES['其他']
  const displayTitle = job.title_zh || job.title
  const budget = formatBudget(job.budget_min, job.budget_max, job.currency)
  const visibleSkills = (job.skills || []).slice(0, 4)
  const extraSkillsCount = (job.skills || []).length - 4

  return (
    <div className={clsx(
      'card p-5 flex flex-col gap-4',
      'transition-all duration-200 ease-out',
      'hover:border-gray-700 hover:bg-gray-900/80 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-black/20',
      'group cursor-default',
    )}>
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-100 text-sm leading-snug line-clamp-2 group-hover:text-white transition-colors">
            {displayTitle}
          </h3>
          {job.title_zh && job.title !== job.title_zh && (
            <p className="text-xs text-gray-500 mt-0.5 truncate">{job.title}</p>
          )}
        </div>
        <ScoreBadge score={job.ai_score} reason={job.ai_reason} />
      </div>

      {/* Badges row */}
      <div className="flex flex-wrap items-center gap-2">
        <span className={clsx(
          'badge border text-xs',
          sourceStyle.bg, sourceStyle.text, sourceStyle.border,
        )}>
          {sourceStyle.label}
        </span>
        <span className={clsx(
          'badge border text-xs',
          categoryStyle.bg, categoryStyle.text, categoryStyle.border,
        )}>
          {job.category}
        </span>
        {job.is_remote && (
          <span className="badge bg-gray-800/60 text-gray-400 border border-gray-700/50 text-xs">
            遠端
          </span>
        )}
      </div>

      {/* Description */}
      <p className="text-xs text-gray-500 leading-relaxed line-clamp-2">
        {job.description_zh || job.description}
      </p>

      {/* Skills */}
      {visibleSkills.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {visibleSkills.map(skill => (
            <span key={skill} className="tag text-xs">
              {skill}
            </span>
          ))}
          {extraSkillsCount > 0 && (
            <span className="tag text-xs text-gray-500">
              +{extraSkillsCount}
            </span>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-1 mt-auto border-t border-gray-800">
        <div className="flex items-center gap-3">
          {budget && (
            <span className="text-sm font-semibold text-green-400">
              {budget}
            </span>
          )}
          <span className="text-xs text-gray-600">
            {formatRelativeTime(job.posted_at)}
          </span>
        </div>
        <a
          href={job.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className={clsx(
            'flex items-center gap-1 text-xs font-medium px-3 py-1.5 rounded-lg',
            'bg-gray-800 hover:bg-blue-600 text-gray-400 hover:text-white',
            'border border-gray-700 hover:border-blue-600',
            'transition-all duration-200',
          )}
          onClick={e => e.stopPropagation()}
        >
          查看詳情
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </a>
      </div>
    </div>
  )
}

export function JobCardSkeleton() {
  return (
    <div className="card p-5 flex flex-col gap-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 space-y-2">
          <div className="skeleton h-4 rounded w-3/4" />
          <div className="skeleton h-3 rounded w-1/2" />
        </div>
        <div className="skeleton h-5 w-14 rounded-full" />
      </div>
      <div className="flex gap-2">
        <div className="skeleton h-5 w-20 rounded-full" />
        <div className="skeleton h-5 w-16 rounded-full" />
      </div>
      <div className="space-y-1.5">
        <div className="skeleton h-3 rounded w-full" />
        <div className="skeleton h-3 rounded w-4/5" />
      </div>
      <div className="flex gap-1.5">
        <div className="skeleton h-5 w-12 rounded" />
        <div className="skeleton h-5 w-16 rounded" />
        <div className="skeleton h-5 w-10 rounded" />
      </div>
      <div className="flex items-center justify-between border-t border-gray-800 pt-3">
        <div className="skeleton h-4 w-20 rounded" />
        <div className="skeleton h-7 w-20 rounded-lg" />
      </div>
    </div>
  )
}
