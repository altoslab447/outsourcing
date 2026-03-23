import React from 'react'
import clsx from 'clsx'

const CATEGORY_STYLES = {
  '全部': {
    active: 'bg-blue-600 text-white border-blue-600',
    inactive: 'text-gray-400 border-transparent hover:text-gray-200 hover:border-gray-600',
    dot: 'bg-blue-400',
  },
  '技術開發': {
    active: 'bg-blue-600 text-white border-blue-600',
    inactive: 'text-gray-400 border-transparent hover:text-blue-400 hover:border-blue-700',
    dot: 'bg-blue-400',
  },
  '設計創意': {
    active: 'bg-purple-600 text-white border-purple-600',
    inactive: 'text-gray-400 border-transparent hover:text-purple-400 hover:border-purple-700',
    dot: 'bg-purple-400',
  },
  '行銷文案': {
    active: 'bg-green-600 text-white border-green-600',
    inactive: 'text-gray-400 border-transparent hover:text-green-400 hover:border-green-700',
    dot: 'bg-green-400',
  },
  '翻譯文字': {
    active: 'bg-yellow-600 text-white border-yellow-600',
    inactive: 'text-gray-400 border-transparent hover:text-yellow-400 hover:border-yellow-700',
    dot: 'bg-yellow-400',
  },
  '其他': {
    active: 'bg-gray-600 text-white border-gray-600',
    inactive: 'text-gray-400 border-transparent hover:text-gray-300 hover:border-gray-600',
    dot: 'bg-gray-400',
  },
}

export default function CategoryTabs({ categories, activeCategory, onCategoryChange }) {
  const getCategoryCount = (name) => {
    const cat = categories.find(c => c.category === name)
    return cat?.count ?? 0
  }

  const tabNames = ['全部', '技術開發', '設計創意', '行銷文案', '翻譯文字', '其他']

  return (
    <div className="relative">
      <div className="flex items-center gap-1 overflow-x-auto scrollbar-hide pb-1">
        {tabNames.map((name) => {
          const isActive = activeCategory === name
          const style = CATEGORY_STYLES[name] || CATEGORY_STYLES['其他']
          const count = getCategoryCount(name)

          return (
            <button
              key={name}
              onClick={() => onCategoryChange(name)}
              className={clsx(
                'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium',
                'border transition-all duration-200 whitespace-nowrap flex-shrink-0',
                isActive ? style.active : style.inactive
              )}
            >
              {!isActive && (
                <span className={clsx('w-1.5 h-1.5 rounded-full', style.dot)} />
              )}
              <span>{name}</span>
              <span
                className={clsx(
                  'text-xs px-1.5 py-0.5 rounded-full font-mono',
                  isActive
                    ? 'bg-white/20 text-white'
                    : 'bg-gray-800 text-gray-500'
                )}
              >
                {count}
              </span>
            </button>
          )
        })}
      </div>
      {/* Fade edge */}
      <div className="absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-l from-gray-950 to-transparent pointer-events-none" />
    </div>
  )
}
