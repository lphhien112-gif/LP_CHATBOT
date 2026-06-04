import { Check, ChevronDown, Workflow } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

// Các phương pháp giải. `phrase` là cụm từ backend nhận diện để chọn solver;
// rỗng = để hệ thống tự chọn.
export const METHODS = [
  { id: 'auto', label: 'Tự động', phrase: '', desc: 'Hệ thống tự chọn phương pháp phù hợp' },
  { id: 'simplex', label: 'Đơn hình', phrase: 'bằng phương pháp đơn hình', desc: 'Đơn hình dạng từ điển (Dantzig)' },
  { id: 'bland', label: 'Bland', phrase: 'bằng phương pháp Bland', desc: 'Đơn hình quy tắc Bland (chống xoay vòng)' },
  { id: 'two_phase', label: 'Hai pha', phrase: 'bằng phương pháp hai pha', desc: 'Hai pha (biến phụ trợ)' },
  { id: 'dual', label: 'Đối ngẫu', phrase: 'bằng phương pháp đối ngẫu', desc: 'Đơn hình đối ngẫu' },
  { id: 'geometric', label: 'Hình học', phrase: 'bằng phương pháp hình học', desc: 'Phương pháp hình học (2 biến)' },
  { id: 'pulp', label: 'PuLP', phrase: 'bằng PuLP', desc: 'Bộ giải PuLP CBC (nhanh, kiểm chứng)' },
]

export default function MethodSelector({ value, onChange }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)
  const current = METHODS.find((m) => m.id === value) || METHODS[0]

  useEffect(() => {
    const onClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [])

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        title="Chọn phương pháp giải"
        className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-600 transition hover:border-brand-300 hover:text-brand-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:border-brand-600"
      >
        <Workflow size={14} className="text-brand-500" />
        <span>{current.label}</span>
        <ChevronDown size={14} className={`transition ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="absolute bottom-full left-0 z-20 mb-2 w-64 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xl dark:border-slate-700 dark:bg-slate-800">
          <div className="border-b border-slate-100 px-3 py-2 text-[11px] font-semibold uppercase tracking-wide text-slate-400 dark:border-slate-700">
            Phương pháp giải
          </div>
          {METHODS.map((m) => (
            <button
              key={m.id}
              type="button"
              onClick={() => {
                onChange(m.id)
                setOpen(false)
              }}
              className={`flex w-full items-start gap-2 px-3 py-2 text-left transition hover:bg-slate-50 dark:hover:bg-slate-700/50 ${
                m.id === value ? 'bg-brand-50/60 dark:bg-brand-900/20' : ''
              }`}
            >
              <Check
                size={15}
                className={`mt-0.5 shrink-0 ${m.id === value ? 'text-brand-600' : 'text-transparent'}`}
              />
              <span className="min-w-0">
                <span className="block text-sm font-medium text-slate-800 dark:text-slate-100">{m.label}</span>
                <span className="block text-[11px] leading-tight text-slate-400">{m.desc}</span>
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
