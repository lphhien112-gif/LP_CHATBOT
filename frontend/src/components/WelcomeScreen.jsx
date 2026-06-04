import { Sigma, Sparkles, PenLine, MessageSquareText, GraduationCap, SquarePen } from 'lucide-react'

// Các nhóm ví dụ — đều đã được kiểm chứng chạy đúng end-to-end.
const GROUPS = [
  {
    icon: PenLine,
    title: 'Nhập theo công thức',
    color: 'text-brand-500',
    examples: [
      'Tối đa hóa 3x + 5y với điều kiện x ≤ 4, 2y ≤ 12, 3x + 2y ≤ 18, x, y ≥ 0',
      'Tối thiểu 2x + 3y với x + y ≥ 4, x + 3y ≥ 6, x, y ≥ 0',
    ],
  },
  {
    icon: MessageSquareText,
    title: 'Mô tả bằng lời (bài toán thực tế)',
    color: 'text-emerald-500',
    examples: [
      'Một xưởng làm bàn và ghế. Mỗi bàn lãi 3, mỗi ghế lãi 5. Bàn cần 1 giờ máy, ghế cần 2 giờ, có 12 giờ. Tối đa 4 bàn. Hãy tối đa lợi nhuận.',
    ],
  },
  {
    icon: GraduationCap,
    title: 'Hỏi lý thuyết',
    color: 'text-amber-500',
    examples: [
      'Phương pháp đơn hình hoạt động thế nào?',
      'Bài toán đối ngẫu là gì?',
    ],
  },
]

export default function WelcomeScreen({ onPick, onOpenForm }) {
  return (
    <div className="mx-auto flex max-w-2xl flex-col items-center pt-8 text-center animate-fade-in-up">
      <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-lg shadow-brand-500/30">
        <Sigma size={34} strokeWidth={2.2} />
      </div>
      <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
        Chào bạn 👋 Mình là LP_Chatbot
      </h2>
      <p className="mt-2 max-w-md text-sm text-slate-500 dark:text-slate-400">
        Trợ lý giải <strong>Quy hoạch tuyến tính</strong> — mô hình hóa, giải{' '}
        <strong>từng bước</strong> (đơn hình, hình học, hai pha, đối ngẫu…) và giải thích kết quả.
      </p>

      {/* Hướng dẫn nhập nhanh */}
      <div className="mt-6 w-full rounded-xl border border-brand-100 bg-brand-50/50 p-3 text-left text-xs text-slate-600 dark:border-brand-900/40 dark:bg-brand-900/10 dark:text-slate-300">
        <div className="flex items-center gap-1.5 font-semibold text-brand-700 dark:text-brand-300">
          <Sparkles size={14} /> Mẹo nhập
        </div>
        <ul className="mt-1.5 space-y-1 pl-1">
          <li>• Viết <em>“Tối đa hóa / Tối thiểu …”</em> rồi <em>“với điều kiện …”</em> ngăn cách bằng dấu phẩy.</li>
          <li>• Hoặc mô tả bài toán bằng lời thường — mình tự bóc tách giúp.</li>
          <li>• 📷 <em>Chụp/tải ảnh đề bài</em> (nút “Ảnh đề”) — mình đọc rồi điền sẵn để bạn xem lại.</li>
          <li>• Chọn <em>phương pháp giải</em> ở ô nhập, hoặc thêm <em>“bằng phương pháp hình học”</em>.</li>
          <li>• Bấm <em>“Luyện tập”</em> (góc trên) để tự giải → chấm điểm như đi thi.</li>
        </ul>
        <button
          onClick={onOpenForm}
          className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-lg border border-brand-300 bg-white px-3 py-2 text-sm font-medium text-brand-700 transition hover:bg-brand-50 dark:border-brand-700/60 dark:bg-slate-900 dark:text-brand-300 dark:hover:bg-brand-900/20"
        >
          <SquarePen size={15} /> Nhập theo form (chính xác, không cần gõ đề)
        </button>
      </div>

      {/* Ví dụ theo nhóm */}
      <div className="mt-6 w-full space-y-4">
        {GROUPS.map((g) => (
          <div key={g.title}>
            <div className="mb-2 flex items-center gap-1.5 text-left text-xs font-semibold uppercase tracking-wide text-slate-400">
              <g.icon size={14} className={g.color} />
              {g.title}
            </div>
            <div className="grid gap-2">
              {g.examples.map((ex, i) => (
                <button
                  key={i}
                  onClick={() => onPick(ex)}
                  className="group flex items-start gap-2.5 rounded-xl border border-slate-200 bg-white p-3 text-left text-sm text-slate-700 shadow-sm transition hover:border-brand-300 hover:shadow-md dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-brand-600"
                >
                  <Sparkles size={15} className={`mt-0.5 shrink-0 ${g.color} transition group-hover:scale-110`} />
                  <span className="leading-snug">{ex}</span>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
