import { Moon, Sun, RotateCcw, Sigma, HelpCircle, ListChecks } from 'lucide-react'

export default function Header({ dark, onToggleTheme, onReset, onOpenHelp, onOpenPractice, hasChat }) {
  return (
    <header className="sticky top-0 z-10 border-b border-slate-200/70 bg-white/80 backdrop-blur-md dark:border-slate-800/70 dark:bg-slate-900/80">
      <div className="mx-auto flex w-full max-w-3xl items-center gap-3 px-4 py-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-sm">
          <Sigma size={20} strokeWidth={2.4} />
        </div>
        <div className="min-w-0 flex-1">
          <h1 className="truncate text-base font-semibold leading-tight">LP_Chatbot</h1>
          <p className="truncate text-xs text-slate-500 dark:text-slate-400">
            Trợ lý giải Quy hoạch tuyến tính · từng bước
          </p>
        </div>

        <button
          onClick={onOpenPractice}
          title="Chế độ luyện tập có chấm điểm"
          className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-2.5 py-1.5 text-sm font-medium text-white transition hover:bg-emerald-500"
        >
          <ListChecks size={16} />
          <span className="hidden sm:inline">Luyện tập</span>
        </button>

        {hasChat && (
          <button
            onClick={onReset}
            title="Bắt đầu lại cuộc trò chuyện"
            className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm text-slate-600 transition hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
          >
            <RotateCcw size={16} />
            <span className="hidden sm:inline">Làm mới</span>
          </button>
        )}

        <button
          onClick={onOpenHelp}
          title="Hướng dẫn & thuật ngữ"
          className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-slate-600 transition hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
        >
          <HelpCircle size={18} />
        </button>

        <button
          onClick={onToggleTheme}
          title={dark ? 'Chuyển sang nền sáng' : 'Chuyển sang nền tối'}
          className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-slate-600 transition hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
        >
          {dark ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </div>
    </header>
  )
}
