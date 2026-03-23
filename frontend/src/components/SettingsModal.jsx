import React, { useState, useEffect } from 'react'
import clsx from 'clsx'

const PRESET_SKILLS = [
  'React', 'Vue.js', 'Angular', 'Node.js', 'Python', 'JavaScript',
  'TypeScript', 'PHP', 'Java', 'Ruby', 'Go', 'Flutter', 'Django',
  'FastAPI', 'Docker', 'AWS', 'PostgreSQL', 'MongoDB', 'Figma',
  'Photoshop', 'SEO', 'Content Marketing', 'Translation',
]

const CATEGORIES = ['技術開發', '設計創意', '行銷文案', '翻譯文字', '其他']

export default function SettingsModal({ isOpen, onClose, settings, onSave, saving }) {
  const [form, setForm] = useState({
    skills: [],
    min_budget: 500,
    max_budget: 10000,
    preferred_categories: ['技術開發', '設計創意'],
    languages: ['English', 'Chinese'],
    anthropic_api_key: '',
  })
  const [skillInput, setSkillInput] = useState('')
  const [showSuccess, setShowSuccess] = useState(false)

  useEffect(() => {
    if (settings) {
      setForm({
        ...settings,
        anthropic_api_key: settings.anthropic_api_key === '***' ? '' : (settings.anthropic_api_key || ''),
      })
    }
  }, [settings])

  if (!isOpen) return null

  const addSkill = (skill) => {
    if (skill && !form.skills.includes(skill)) {
      setForm(prev => ({ ...prev, skills: [...prev.skills, skill] }))
    }
    setSkillInput('')
  }

  const removeSkill = (skill) => {
    setForm(prev => ({ ...prev, skills: prev.skills.filter(s => s !== skill) }))
  }

  const toggleCategory = (cat) => {
    setForm(prev => ({
      ...prev,
      preferred_categories: prev.preferred_categories.includes(cat)
        ? prev.preferred_categories.filter(c => c !== cat)
        : [...prev.preferred_categories, cat],
    }))
  }

  const handleSave = async () => {
    try {
      await onSave(form)
      setShowSuccess(true)
      setTimeout(() => {
        setShowSuccess(false)
        onClose()
      }, 1500)
    } catch (err) {
      console.error('Save failed:', err)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-lg bg-gray-900 border border-gray-800 rounded-2xl shadow-2xl overflow-hidden animate-fade-in">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <h2 className="text-base font-semibold text-gray-100">個人設定</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-300 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-5 space-y-5 max-h-[70vh] overflow-y-auto">
          {/* My Skills */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
              我的技能
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={skillInput}
                onChange={e => setSkillInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && skillInput.trim() && addSkill(skillInput.trim())}
                placeholder="輸入技能..."
                className="input-field flex-1 text-sm"
              />
              <button
                onClick={() => skillInput.trim() && addSkill(skillInput.trim())}
                className="btn-secondary text-sm px-3"
              >
                加入
              </button>
            </div>
            {form.skills.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {form.skills.map(skill => (
                  <span key={skill} className="tag text-xs">
                    {skill}
                    <button
                      onClick={() => removeSkill(skill)}
                      className="ml-1 text-gray-500 hover:text-red-400 transition-colors"
                    >×</button>
                  </span>
                ))}
              </div>
            )}
            {/* Preset skills */}
            <div className="pt-1">
              <p className="text-xs text-gray-600 mb-1.5">快速選擇：</p>
              <div className="flex flex-wrap gap-1">
                {PRESET_SKILLS.filter(s => !form.skills.includes(s)).slice(0, 12).map(skill => (
                  <button
                    key={skill}
                    onClick={() => addSkill(skill)}
                    className="text-xs px-2 py-0.5 rounded border border-gray-700 text-gray-500 hover:text-gray-300 hover:border-gray-600 transition-colors"
                  >
                    + {skill}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Budget */}
          <div className="space-y-3">
            <label className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
              預算範圍偏好 (USD)
            </label>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <p className="text-xs text-gray-600 mb-1">最低預算</p>
                <input
                  type="number"
                  value={form.min_budget}
                  onChange={e => setForm(prev => ({ ...prev, min_budget: Number(e.target.value) }))}
                  className="input-field w-full text-sm"
                  min="0"
                  step="100"
                />
              </div>
              <div>
                <p className="text-xs text-gray-600 mb-1">最高預算</p>
                <input
                  type="number"
                  value={form.max_budget}
                  onChange={e => setForm(prev => ({ ...prev, max_budget: Number(e.target.value) }))}
                  className="input-field w-full text-sm"
                  min="0"
                  step="100"
                />
              </div>
            </div>
          </div>

          {/* Preferred Categories */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
              偏好分類
            </label>
            <div className="flex flex-wrap gap-2">
              {CATEGORIES.map(cat => {
                const isSelected = form.preferred_categories.includes(cat)
                return (
                  <button
                    key={cat}
                    onClick={() => toggleCategory(cat)}
                    className={clsx(
                      'text-sm px-3 py-1.5 rounded-lg border transition-colors duration-150',
                      isSelected
                        ? 'bg-blue-600 border-blue-600 text-white'
                        : 'bg-gray-800 border-gray-700 text-gray-400 hover:text-gray-200 hover:border-gray-600'
                    )}
                  >
                    {cat}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Anthropic API Key */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-gray-400 uppercase tracking-wide flex items-center gap-1.5">
              <svg className="w-3.5 h-3.5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              Anthropic API Key
            </label>
            <input
              type="password"
              value={form.anthropic_api_key}
              onChange={e => setForm(prev => ({ ...prev, anthropic_api_key: e.target.value }))}
              placeholder="sk-ant-..."
              className="input-field w-full text-sm font-mono"
            />
            <p className="text-xs text-gray-600">
              提供 API Key 後，AI 將自動為職缺評分。未提供則顯示 N/A。
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-gray-800 bg-gray-950/50">
          {showSuccess ? (
            <div className="flex items-center gap-2 text-green-400 text-sm">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              設定已儲存！
            </div>
          ) : (
            <p className="text-xs text-gray-600">儲存後將重新評分所有職缺</p>
          )}
          <div className="flex gap-2">
            <button onClick={onClose} className="btn-secondary text-sm">
              取消
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className={clsx(
                'btn-primary text-sm flex items-center gap-1.5',
                saving && 'opacity-70 cursor-not-allowed'
              )}
            >
              {saving && (
                <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              )}
              儲存設定
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
