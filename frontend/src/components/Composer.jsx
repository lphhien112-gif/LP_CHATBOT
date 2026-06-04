import { useEffect, useRef, useState } from 'react'
import { SendHorizontal, Loader2, SquarePen, ImagePlus } from 'lucide-react'
import MethodSelector, { METHODS } from './MethodSelector'
import { extractImage } from '../lib/api'

export default function Composer({ onSend, disabled, onOpenForm }) {
  const [value, setValue] = useState('')
  const [method, setMethod] = useState('auto')
  const [ocr, setOcr] = useState({ loading: false, error: '' })
  const ref = useRef(null)
  const fileRef = useRef(null)

  // Tự co giãn chiều cao theo nội dung (tối đa ~6 dòng)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 168) + 'px'
  }, [value])

  const submit = () => {
    const text = value.trim()
    if (!text || disabled) return
    const phrase = (METHODS.find((m) => m.id === method) || {}).phrase || ''
    const finalMsg = phrase ? `${text} ${phrase}` : text
    onSend(finalMsg)
    setValue('')
  }

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  const onPickImage = async (e) => {
    const file = e.target.files?.[0]
    e.target.value = '' // cho phép chọn lại cùng file
    if (!file) return
    if (file.size > 8 * 1024 * 1024) {
      setOcr({ loading: false, error: 'Ảnh quá lớn (tối đa 8MB).' })
      return
    }
    setOcr({ loading: true, error: '' })
    try {
      const dataUrl = await new Promise((resolve, reject) => {
        const r = new FileReader()
        r.onload = () => resolve(r.result)
        r.onerror = reject
        r.readAsDataURL(file)
      })
      const { text } = await extractImage(dataUrl)
      setValue(text || '')
      setOcr({ loading: false, error: '' })
      ref.current?.focus()
    } catch (err) {
      setOcr({ loading: false, error: err.message || 'Không đọc được ảnh.' })
    }
  }

  return (
    <div className="border-t border-slate-200/70 bg-white/80 backdrop-blur-md dark:border-slate-800/70 dark:bg-slate-900/80">
      <div className="mx-auto w-full max-w-3xl px-4 py-3">
        <div className="rounded-2xl border border-slate-300 bg-white shadow-sm transition focus-within:border-brand-400 focus-within:ring-2 focus-within:ring-brand-400/30 dark:border-slate-700 dark:bg-slate-800">
          {/* Thanh công cụ: chọn phương pháp giải + nhập form + chụp ảnh */}
          <div className="flex flex-wrap items-center gap-2 border-b border-slate-100 px-2.5 py-1.5 dark:border-slate-700/60">
            <MethodSelector value={method} onChange={setMethod} />
            <button
              type="button"
              onClick={onOpenForm}
              title="Nhập bài toán theo form (chính xác, không qua phân tích văn bản)"
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-600 transition hover:border-brand-300 hover:text-brand-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:border-brand-600"
            >
              <SquarePen size={14} className="text-brand-500" />
              Nhập form
            </button>
            <button
              type="button"
              onClick={() => fileRef.current?.click()}
              disabled={ocr.loading}
              title="Chụp/tải ảnh đề bài — AI đọc rồi điền vào ô nhập để bạn xem lại"
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-600 transition hover:border-brand-300 hover:text-brand-600 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:border-brand-600"
            >
              {ocr.loading ? <Loader2 size={14} className="animate-spin text-brand-500" /> : <ImagePlus size={14} className="text-brand-500" />}
              {ocr.loading ? 'Đang đọc ảnh…' : 'Ảnh đề'}
            </button>
            <input ref={fileRef} type="file" accept="image/*" capture="environment" className="hidden" onChange={onPickImage} />
            <span className="hidden text-[11px] text-slate-400 lg:inline">hoặc gõ đề trực tiếp bên dưới</span>
          </div>

          {/* Ô nhập + nút gửi */}
          <div className="flex items-end gap-2 p-2">
            <textarea
              ref={ref}
              rows={1}
              value={value}
              disabled={disabled}
              onChange={(e) => setValue(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder="Nhập bài toán Quy hoạch tuyến tính… (vd: Tối đa hóa 3x + 5y với điều kiện x ≤ 4, 2y ≤ 12, 3x + 2y ≤ 18)"
              className="scroll-thin max-h-44 flex-1 resize-none bg-transparent px-2 py-1.5 text-[15px] leading-relaxed text-slate-800 placeholder:text-slate-400 focus:outline-none disabled:opacity-60 dark:text-slate-100"
            />
            <button
              onClick={submit}
              disabled={disabled || !value.trim()}
              title="Gửi (Enter)"
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-600 text-white shadow-sm transition hover:bg-brand-500 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {disabled ? <Loader2 size={18} className="animate-spin" /> : <SendHorizontal size={18} />}
            </button>
          </div>
        </div>
        {ocr.error ? (
          <p className="mt-1.5 px-1 text-center text-[11px] text-rose-500">{ocr.error}</p>
        ) : (
          <p className="mt-1.5 px-1 text-center text-[11px] text-slate-400">
            Nhấn <kbd className="font-mono">Enter</kbd> để gửi · <kbd className="font-mono">Shift+Enter</kbd> xuống dòng · 📷 “Ảnh đề” để đọc từ ảnh
          </p>
        )}
      </div>
    </div>
  )
}
