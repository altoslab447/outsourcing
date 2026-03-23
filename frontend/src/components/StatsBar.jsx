import React from 'react'
import { formatDistanceToNow } from 'date-fns'
import { zhTW } from 'date-fns/locale'
import clsx from 'clsx'

const SOURCE_COLORS = {
  remoteok: 'bg-emerald-500',
  freelancer: 'bg-blue-500',
  weworkremotely: 'bg-red-500',
  '104': 'bg-orange-500',
}

const SOURCE_LABELS = {
  remoteok: 'RemoteOK',
  freelancer: 'Freelancer',
  weworkremotely: 'WeWork',
  '104': '104人力銀行',
}

function RefreshIcon({ spinning }) {
  return (
    <svg
      className={clsx('w-4 h-4', spinning && 'animate-spin')}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
      />
    </svg>
  )
}

export default function StatsBar({ stats, lastUpdated, isRefreshing, onRefresh }) {
  const formattedTime = lastUpdated
    ? formatDistanceToNow(lastUpdated, { addSuffix: true, locale: zhTW })
    : '從未更新'

  return (
    <div className="card px-4 py-3 flex flex-wrap items-center gap-4">
      {/* Total */}
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
        <span className="text-sm text-gray-400">共找到</span>
        <span className="text-lg font-bold text-white">
          {stats?.total_jobs ?? '—'}
        </span>
        <span className="text-sm text-gray-400">個職缺</span>
      </div>

      <div className="h-4 w-px bg-gray-700 hidden sm:block" />

      {/* Per source breakdown */}
      <div className="flex flex-wrap items-center gap-3">
        {Object.entries(SOURCE_LABELS).map(([key, label]) => {
          const count = stats?.by_source?.[key] ?? 0
          return (
            <div key={key} className="flex items-center gap-1.5">
              <div className={clsx('w-2 h-2 rounded-full', SOURCE_COLORS[key])} />
              <span className="text-xs text-gray-400">{label}</span>
              <span className="text-xs font-semibold text-gray-200">{count}</span>
            </div>
          )
        })}
      </div>

      <div className="flex-1" />

      {/* Last updated */}
      <div className="flex items-center gap-2 text-xs text-gray-500">
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>
          {isRefreshing ? '更新中...' : `上次更新：${formattedTime}`}
        </span>
      </div>

      {/* Refresh button */}
      <button
        onClick={onRefresh}
        disabled={isRefreshing}
        className={clsx(
          'flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg transition-colors duration-200',
          isRefreshing
            ? 'bg-gray-800 text-gray-500 cursor-not-allowed'
            : 'bg-gray-800 hover:bg-gray-700 text-gray-300 hover:text-white border border-gray-700'
        )}
      >
        <RefreshIcon spinning={isRefreshing} />
        <span>{isRefreshing ? '更新中' : '立即更新'}</span>
      </button>
    </div>
  )
}
