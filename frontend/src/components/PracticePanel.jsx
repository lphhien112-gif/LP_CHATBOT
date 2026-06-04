import { useEffect, useRef, useState } from 'react'
import { X, RefreshCw, CheckCircle2, XCircle, Trophy, Target, Flame, ListChecks, Eye, ArrowRight, RotateCcw } from 'lucide-react'
import { practiceNew, practiceGrade } from '../lib/api'
import { renderMarkdown, renderKatex } from '../lib/markdown'
import { getProgress, recordAttempt, resetProgress } from '../lib/progress'

function Rendered({ html, isMarkdown }) {
  const ref = useRef(null)
  const out = isMarkdown ? renderMarkdown(html) : html
  useEffect(() => {
    if (ref.current) renderKatex(ref.current)
  }, [out])
  return <div ref={ref} className="prose-chat" dangerouslySetInnerHTML={{ __html: out }} />
}

function Stat({ icon: Icon, label, value, color }) {
  return (
    <div className="flex items-center gap-2.5 rounded-xl border border-slate-200 bg-white p-3 dark:border-slate-700 dark:bg-slate-800/60">
      <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${color}`}>
        <Icon size={18} />
      </div>
      <div className="min-w-0">
        <div className="text-lg font-bold leading-none text-slate-900 dark:text-white">{value}</div>
        <div className="text-[11px] text-slate-500 dark:text-slate-400">{label}</div>
      </div>
    </div>
  )
}

export default function PracticePanel({ onClose }) {
  const [problem, setProblem] = useState(null)
  const [vars, setVars] = useState([])
  const [answers, setAnswers] = useState({})
  const [result, setResult] = useState(null)
  const [showSol, setShowSol] = useState(false)
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(getProgress())

  const loadNew = async () => {
    setLoading(true)
    setResult(null)
    setShowSol(false)
    try {
      const data = await practiceNew()
      setProblem(data.display_html)
      setVars(data.variables || [])
      setAnswers(Object.fromEntries([...(data.variables || []), 'z'].map((v) => [v, ''])))
    } catch {
      setProblem('<p>Không tạo được bài luyện tập. Vui lòng thử lại.</p>')
    }
    setLoading(false)
  }

  useEffect(() => {
    loadNew()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const submit = async () => {
    if (result) return
    try {
      const r = await practiceGrade(answers)
      if (r.error) return
      setResult(r)
      setProgress(recordAttempt(r.correct))
    } catch {
      /* ignore */
    }
  }

  const accuracy = progress.total ? Math.round((progress.correct / progress.total) * 100) : 0

  return (
    <div className="fixed inset-0 z-50 bg-slate-50 dark:bg-slate-950">
      <div className="flex h-full flex-col">
        {/* Header */}
        <div className="flex items-center gap-3 border-b border-slate-200 bg-white px-4 py-3 dark:border-slate-800 dark:bg-slate-900">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-700 text-white">
            <ListChecks size={20} />
          </div>
          <div className="flex-1">
            <h2 className="text-base font-semibold leading-tight">Luyện tập có chấm điểm</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">Tự giải → nhập nghiệm → nhận phản hồi tức thì</p>
          </div>
          <button onClick={onClose} className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800">
            <X size={16} /> Thoát
          </button>
        </div>

        <div className="scroll-thin flex-1 overflow-y-auto">
          <div className="mx-auto w-full max-w-2xl space-y-5 px-4 py-6">
            {/* Dashboard */}
            <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-4">
              <Stat icon={Target} label="Đã làm" value={progress.total} color="bg-brand-100 text-brand-600 dark:bg-brand-900/30 dark:text-brand-300" />
              <Stat icon={CheckCircle2} label="Đúng" value={progress.correct} color="bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-300" />
              <Stat icon={Trophy} label="Tỉ lệ đúng" value={`${accuracy}%`} color="bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-300" />
              <Stat icon={Flame} label={`Streak (cao nhất ${progress.bestStreak})`} value={progress.streak} color="bg-rose-100 text-rose-600 dark:bg-rose-900/30 dark:text-rose-300" />
            </div>
            {progress.total > 0 && (
              <button onClick={() => setProgress(resetProgress())} className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-slate-600">
                <RotateCcw size={12} /> Đặt lại tiến độ
              </button>
            )}

            {/* Bài toán */}
            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">📝 Đề bài — hãy tự giải</span>
                <button onClick={loadNew} disabled={loading} className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-brand-600 hover:bg-brand-50 disabled:opacity-50 dark:hover:bg-brand-900/20">
                  <RefreshCw size={13} className={loading ? 'animate-spin' : ''} /> Đề khác
                </button>
              </div>
              {loading ? (
                <p className="py-6 text-center text-sm text-slate-400">Đang tạo đề…</p>
              ) : (
                <Rendered html={problem || ''} isMarkdown={false} />
              )}
            </div>

            {/* Nhập nghiệm */}
            {!loading && (
              <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                <div className="mb-3 text-sm font-semibold text-slate-700 dark:text-slate-200">✍️ Nhập nghiệm tối ưu của bạn</div>
                <div className="flex flex-wrap items-center gap-3">
                  {vars.map((v) => (
                    <label key={v} className="flex items-center gap-1.5 text-sm">
                      <span className="font-mono text-slate-600 dark:text-slate-300">{v} =</span>
                      <input
                        type="number" step="any" value={answers[v] ?? ''} disabled={!!result}
                        onChange={(e) => setAnswers((a) => ({ ...a, [v]: e.target.value }))}
                        className="w-20 rounded-md border border-slate-300 bg-white px-2 py-1 text-center focus:border-brand-400 focus:outline-none disabled:opacity-60 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
                      />
                    </label>
                  ))}
                  <label className="flex items-center gap-1.5 text-sm">
                    <span className="font-mono text-slate-600 dark:text-slate-300">z* =</span>
                    <input
                      type="number" step="any" value={answers.z ?? ''} disabled={!!result}
                      onChange={(e) => setAnswers((a) => ({ ...a, z: e.target.value }))}
                      className="w-24 rounded-md border border-slate-300 bg-white px-2 py-1 text-center focus:border-brand-400 focus:outline-none disabled:opacity-60 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
                    />
                  </label>
                </div>
                <p className="mt-2 text-[11px] text-slate-400">Nhập số thập phân (làm tròn 2 chữ số cũng được).</p>

                {!result ? (
                  <button onClick={submit} className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500">
                    <CheckCircle2 size={16} /> Nộp bài
                  </button>
                ) : (
                  <div className="mt-4 space-y-3">
                    <div className={`flex items-center gap-2 rounded-xl p-3 ${result.correct ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-300' : 'bg-rose-50 text-rose-700 dark:bg-rose-900/20 dark:text-rose-300'}`}>
                      {result.correct ? <CheckCircle2 size={20} /> : <XCircle size={20} />}
                      <span className="font-semibold">{result.correct ? '🎉 Chính xác! Làm tốt lắm.' : 'Chưa đúng — xem đáp án & lời giải bên dưới.'}</span>
                    </div>
                    <div className="space-y-1 text-sm">
                      {Object.entries(result.variables).map(([v, r]) => (
                        <div key={v} className="flex items-center gap-2">
                          {r.ok ? <CheckCircle2 size={15} className="text-emerald-500" /> : <XCircle size={15} className="text-rose-500" />}
                          <span className="font-mono">{v}</span>: bạn nhập <b>{r.got}</b>{!r.ok && <> · đáp án <b className="text-emerald-600 dark:text-emerald-400">{Number(r.expected).toFixed(2)}</b></>}
                        </div>
                      ))}
                      <div className="flex items-center gap-2">
                        {result.z.ok ? <CheckCircle2 size={15} className="text-emerald-500" /> : <XCircle size={15} className="text-rose-500" />}
                        <span className="font-mono">z*</span>: bạn nhập <b>{result.z.got}</b>{!result.z.ok && <> · đáp án <b className="text-emerald-600 dark:text-emerald-400">{Number(result.z.expected).toFixed(2)}</b></>}
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      <button onClick={() => setShowSol((s) => !s)} className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-600 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800">
                        <Eye size={15} /> {showSol ? 'Ẩn lời giải' : 'Xem lời giải mẫu'}
                      </button>
                      <button onClick={loadNew} className="inline-flex items-center gap-1.5 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-500">
                        Bài tiếp theo <ArrowRight size={15} />
                      </button>
                    </div>

                    {showSol && result.solution_steps?.length > 0 && (
                      <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-800/50">
                        <Rendered html={result.solution_steps.join('\n\n')} isMarkdown={true} />
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
