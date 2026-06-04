import {
  Sigma, ListChecks, SquarePen, HelpCircle, RotateCcw, Moon, Sun,
  FileText, Sparkles, Scale, GraduationCap,
} from 'lucide-react'

function NavBtn({ icon: Icon, label, onClick, variant = 'ghost' }) {
  const base = 'flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition'
  const styles =
    variant === 'primary'
      ? 'bg-accent-600 text-white hover:bg-accent-500 shadow-sm'
      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white'
  return (
    <button onClick={onClick} className={`${base} ${styles}`}>
      <Icon size={17} className={variant === 'primary' ? '' : 'text-brand-500'} />
      <span className="truncate">{label}</span>
    </button>
  )
}

export default function Sidebar({ dark, hasChat, onOpenPractice, onOpenForm, onOpenHelp, onReset, onToggleTheme, onQuick }) {
  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-slate-200 bg-white lg:flex dark:border-slate-800 dark:bg-slate-900">
      {/* Brand */}
      <div className="flex items-center gap-2.5 border-b border-slate-100 px-4 py-4 dark:border-slate-800">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-sm">
          <Sigma size={20} strokeWidth={2.4} />
        </div>
        <div className="min-w-0">
          <div className="truncate text-sm font-bold text-slate-900 dark:text-white">LP_Chatbot</div>
          <div className="truncate text-[11px] text-slate-500 dark:text-slate-400">Quy hoạch tuyến tính</div>
        </div>
      </div>

      {/* Điều hướng / công cụ */}
      <div className="scroll-thin flex-1 space-y-1 overflow-y-auto p-3">
        <NavBtn icon={ListChecks} label="Luyện tập có chấm điểm" variant="primary" onClick={onOpenPractice} />
        <NavBtn icon={SquarePen} label="Nhập theo form" onClick={onOpenForm} />

        <div className="px-2 pb-1 pt-4 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
          Bắt đầu nhanh
        </div>
        <NavBtn icon={FileText} label="Bài toán mẫu" onClick={() => onQuick('Giải bài toán mẫu')} />
        <NavBtn icon={Sparkles} label="Tạo bài tập" onClick={() => onQuick('Tạo bài tập')} />
        <NavBtn icon={Scale} label="So sánh phương pháp" onClick={() => onQuick('So sánh các phương pháp')} />
        <NavBtn icon={GraduationCap} label="Đơn hình là gì?" onClick={() => onQuick('Phương pháp đơn hình hoạt động thế nào?')} />
      </div>

      {/* Dưới cùng */}
      <div className="space-y-1 border-t border-slate-100 p-3 dark:border-slate-800">
        <NavBtn icon={HelpCircle} label="Hướng dẫn & thuật ngữ" onClick={onOpenHelp} />
        {hasChat && <NavBtn icon={RotateCcw} label="Làm mới hội thoại" onClick={onReset} />}
        <NavBtn icon={dark ? Sun : Moon} label={dark ? 'Giao diện sáng' : 'Giao diện tối'} onClick={onToggleTheme} />
      </div>
    </aside>
  )
}
