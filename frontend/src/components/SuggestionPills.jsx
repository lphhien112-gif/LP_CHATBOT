import { ArrowUpRight } from 'lucide-react'

export default function SuggestionPills({ suggestions, onPick, disabled }) {
  if (!suggestions?.length) return null
  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {suggestions.map((s, i) => (
        <button
          key={i}
          disabled={disabled}
          onClick={() => onPick(s.replace(/✨/g, '').trim())}
          className="inline-flex items-center gap-1 rounded-full border border-brand-200 bg-brand-50 px-3 py-1.5 text-xs font-medium text-brand-700 transition hover:bg-brand-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-brand-700/60 dark:bg-brand-900/30 dark:text-brand-200 dark:hover:bg-brand-900/50"
        >
          {s.replace(/✨/g, '').trim()}
          <ArrowUpRight size={13} />
        </button>
      ))}
    </div>
  )
}
