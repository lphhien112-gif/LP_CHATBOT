import { useState } from 'react'
import { X, Plus, Trash2, Play } from 'lucide-react'

const SOLVERS = [
  { id: 'simple_dictionary', label: 'Đơn hình (từ điển)' },
  { id: 'simplex_bland', label: 'Đơn hình Bland' },
  { id: 'auxiliary', label: 'Hai pha' },
  { id: 'dual_simplex', label: 'Đối ngẫu' },
  { id: 'dual_primal_two_phase', label: 'Hai pha đối ngẫu' },
  { id: 'geometric', label: 'Hình học (2 biến)' },
  { id: 'pulp_cbc', label: 'PuLP CBC' },
]

const OPS = ['<=', '>=', '==']
const varName = (i) => `x${i + 1}`
const num = (v) => (v === '' || v === '-' ? 0 : Number(v))

export default function ProblemForm({ onClose, onSolve }) {
  const [nVars, setNVars] = useState(2)
  const [objType, setObjType] = useState('maximize')
  const [objCoeffs, setObjCoeffs] = useState(['', ''])
  const [constraints, setConstraints] = useState([
    { coeffs: ['', ''], op: '<=', rhs: '' },
    { coeffs: ['', ''], op: '<=', rhs: '' },
  ])
  const [solver, setSolver] = useState('simple_dictionary')

  const resize = (arr, n, fill = '') => {
    const a = arr.slice(0, n)
    while (a.length < n) a.push(fill)
    return a
  }
  const setVars = (n) => {
    n = Math.max(1, Math.min(6, n))
    setNVars(n)
    setObjCoeffs((c) => resize(c, n))
    setConstraints((cs) => cs.map((c) => ({ ...c, coeffs: resize(c.coeffs, n) })))
    if (n !== 2 && solver === 'geometric') setSolver('simple_dictionary')
  }

  const setObj = (i, v) => setObjCoeffs((c) => c.map((x, j) => (j === i ? v : x)))
  const setC = (ci, key, v) =>
    setConstraints((cs) => cs.map((c, j) => (j === ci ? { ...c, [key]: v } : c)))
  const setCC = (ci, vi, v) =>
    setConstraints((cs) =>
      cs.map((c, j) => (j === ci ? { ...c, coeffs: c.coeffs.map((x, k) => (k === vi ? v : x)) } : c)),
    )
  const addC = () => setConstraints((cs) => [...cs, { coeffs: Array(nVars).fill(''), op: '<=', rhs: '' }])
  const delC = (ci) => setConstraints((cs) => (cs.length > 1 ? cs.filter((_, j) => j !== ci) : cs))

  const fmtTerm = (coef, i, first) => {
    const c = num(coef)
    if (c === 0) return ''
    const sign = c < 0 ? '−' : first ? '' : '+'
    const a = Math.abs(c)
    const co = a === 1 ? '' : a
    return ` ${sign} ${co}${varName(i)}`.trim()
  }
  const exprStr = (coeffs) => {
    let s = ''
    let first = true
    coeffs.forEach((c, i) => {
      const t = fmtTerm(c, i, first)
      if (t) {
        s += (first ? '' : ' ') + t
        first = false
      }
    })
    return s || '0'
  }

  const submit = () => {
    const problem = {
      objective_type: objType,
      variables: Array.from({ length: nVars }, (_, i) => varName(i)),
      objective_coeffs: objCoeffs.map(num),
      constraints: constraints.map((c) => ({ coeffs: c.coeffs.map(num), op: c.op, rhs: num(c.rhs) })),
    }
    const word = objType === 'maximize' ? 'Tối đa hóa' : 'Tối thiểu hóa'
    const summary =
      `📐 ${word} $Z = ${exprStr(objCoeffs)}$ với ` +
      constraints.map((c) => `$${exprStr(c.coeffs)} ${c.op.replace('<=', '\\le').replace('>=', '\\ge').replace('==', '=')} ${num(c.rhs)}$`).join(', ')
    onSolve(problem, solver, summary)
    onClose()
  }

  const Coeff = ({ value, onChange, i }) => (
    <span className="inline-flex items-center">
      <input
        type="number"
        step="any"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="0"
        className="w-14 rounded-md border border-slate-300 bg-white px-1.5 py-1 text-center text-sm focus:border-brand-400 focus:outline-none dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
      />
      <span className="mx-0.5 text-sm text-slate-500">{varName(i)}</span>
    </span>
  )

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm" onClick={onClose}>
      <div
        className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl border border-slate-200 bg-white shadow-2xl dark:border-slate-700 dark:bg-slate-900"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 flex items-center justify-between border-b border-slate-200 bg-white/90 px-5 py-3 backdrop-blur dark:border-slate-700 dark:bg-slate-900/90">
          <h3 className="font-semibold text-slate-900 dark:text-white">Nhập bài toán theo form</h3>
          <button onClick={onClose} className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800">
            <X size={18} />
          </button>
        </div>

        <div className="space-y-5 p-5">
          {/* Số biến + loại mục tiêu */}
          <div className="flex flex-wrap items-center gap-3">
            <label className="text-sm text-slate-600 dark:text-slate-300">Số biến:</label>
            <div className="flex items-center gap-1">
              <button onClick={() => setVars(nVars - 1)} className="h-7 w-7 rounded-md border border-slate-300 text-slate-600 hover:bg-slate-100 dark:border-slate-600 dark:hover:bg-slate-800">−</button>
              <span className="w-8 text-center font-medium">{nVars}</span>
              <button onClick={() => setVars(nVars + 1)} className="h-7 w-7 rounded-md border border-slate-300 text-slate-600 hover:bg-slate-100 dark:border-slate-600 dark:hover:bg-slate-800">+</button>
            </div>
            <div className="ml-auto flex overflow-hidden rounded-lg border border-slate-300 dark:border-slate-600">
              {['maximize', 'minimize'].map((t) => (
                <button
                  key={t}
                  onClick={() => setObjType(t)}
                  className={`px-3 py-1.5 text-sm ${objType === t ? 'bg-brand-600 text-white' : 'bg-white text-slate-600 dark:bg-slate-800 dark:text-slate-300'}`}
                >
                  {t === 'maximize' ? 'Tối đa' : 'Tối thiểu'}
                </button>
              ))}
            </div>
          </div>

          {/* Hàm mục tiêu */}
          <div>
            <div className="mb-1.5 text-sm font-medium text-slate-700 dark:text-slate-200">Hàm mục tiêu (Z):</div>
            <div className="flex flex-wrap items-center gap-1.5 rounded-lg bg-slate-50 p-2.5 dark:bg-slate-800/50">
              {objCoeffs.map((c, i) => (
                <Coeff key={i} value={c} i={i} onChange={(v) => setObj(i, v)} />
              ))}
            </div>
          </div>

          {/* Ràng buộc */}
          <div>
            <div className="mb-1.5 flex items-center justify-between">
              <span className="text-sm font-medium text-slate-700 dark:text-slate-200">Ràng buộc:</span>
              <button onClick={addC} className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-brand-600 hover:bg-brand-50 dark:hover:bg-brand-900/20">
                <Plus size={14} /> Thêm
              </button>
            </div>
            <div className="space-y-2">
              {constraints.map((c, ci) => (
                <div key={ci} className="flex flex-wrap items-center gap-1.5 rounded-lg bg-slate-50 p-2.5 dark:bg-slate-800/50">
                  {c.coeffs.map((cc, vi) => (
                    <Coeff key={vi} value={cc} i={vi} onChange={(v) => setCC(ci, vi, v)} />
                  ))}
                  <select
                    value={c.op}
                    onChange={(e) => setC(ci, 'op', e.target.value)}
                    className="rounded-md border border-slate-300 bg-white px-1 py-1 text-sm dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
                  >
                    {OPS.map((o) => (<option key={o} value={o}>{o}</option>))}
                  </select>
                  <input
                    type="number"
                    step="any"
                    value={c.rhs}
                    onChange={(e) => setC(ci, 'rhs', e.target.value)}
                    placeholder="0"
                    className="w-16 rounded-md border border-slate-300 bg-white px-1.5 py-1 text-center text-sm focus:border-brand-400 focus:outline-none dark:border-slate-600 dark:bg-slate-700 dark:text-slate-100"
                  />
                  <button onClick={() => delC(ci)} className="ml-auto rounded-md p-1 text-slate-400 hover:text-red-500" title="Xóa ràng buộc">
                    <Trash2 size={15} />
                  </button>
                </div>
              ))}
            </div>
            <p className="mt-1.5 text-[11px] text-slate-400">Ràng buộc dấu xᵢ ≥ 0 được tự động giả định.</p>
          </div>

          {/* Phương pháp giải */}
          <div>
            <div className="mb-1.5 text-sm font-medium text-slate-700 dark:text-slate-200">Phương pháp giải:</div>
            <select
              value={solver}
              onChange={(e) => setSolver(e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
            >
              {SOLVERS.map((s) => (
                <option key={s.id} value={s.id} disabled={s.id === 'geometric' && nVars !== 2}>
                  {s.label}{s.id === 'geometric' && nVars !== 2 ? ' (chỉ 2 biến)' : ''}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="sticky bottom-0 flex justify-end gap-2 border-t border-slate-200 bg-white/90 px-5 py-3 backdrop-blur dark:border-slate-700 dark:bg-slate-900/90">
          <button onClick={onClose} className="rounded-lg px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800">
            Hủy
          </button>
          <button onClick={submit} className="inline-flex items-center gap-1.5 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-500">
            <Play size={15} /> Giải bài toán
          </button>
        </div>
      </div>
    </div>
  )
}
