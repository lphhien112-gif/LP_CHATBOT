import { X, BookOpen, Lightbulb, Workflow, GraduationCap } from 'lucide-react'

const METHODS = [
  ['Đơn hình (từ điển)', 'Phương pháp chuẩn — biến đổi từ vựng từng bước (quy tắc Dantzig).'],
  ['Đơn hình Bland', 'Như đơn hình nhưng chọn biến theo chỉ số nhỏ nhất — chống xoay vòng (degenerate).'],
  ['Hai pha', 'Khi bài toán chưa có cơ sở khả thi: pha 1 tìm điểm khả thi, pha 2 tối ưu.'],
  ['Đối ngẫu', 'Dùng khi hệ số mục tiêu ≥ 0 nhưng có vế phải âm (đơn hình đối ngẫu).'],
  ['Hình học', 'Vẽ miền nghiệm và xét các đỉnh — chỉ áp dụng cho bài 2 biến.'],
  ['PuLP CBC', 'Bộ giải công nghiệp — cho kết quả cuối nhanh để đối chiếu.'],
]

const GLOSSARY = [
  ['Biến quyết định', 'Các ẩn cần tìm (x₁, x₂, …) trong bài toán.'],
  ['Hàm mục tiêu (z)', 'Đại lượng cần tối đa/tối thiểu hóa.'],
  ['Ràng buộc', 'Các điều kiện giới hạn (≤, ≥, =) mà nghiệm phải thỏa.'],
  ['Biến bù (wᵢ)', 'Biến thêm vào để biến bất đẳng thức thành đẳng thức.'],
  ['Từ vựng (dictionary)', 'Hệ phương trình biểu diễn biến cơ sở theo biến phi cơ sở.'],
  ['Biến cơ sở / phi cơ sở', 'Cơ sở: đang khác 0; phi cơ sở: gán = 0 để đọc nghiệm.'],
  ['Biến vào / ra', 'Mỗi bước xoay: 1 biến vào cơ sở (↓), 1 biến rời cơ sở (←).'],
  ['Nghiệm tối ưu z*', 'Giá trị tốt nhất của hàm mục tiêu tại đỉnh tối ưu.'],
]

function Section({ icon: Icon, title, children }) {
  return (
    <div>
      <div className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-brand-700 dark:text-brand-300">
        <Icon size={16} /> {title}
      </div>
      {children}
    </div>
  )
}

export default function HelpPanel({ onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm" onClick={onClose}>
      <div
        className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl border border-slate-200 bg-white shadow-2xl dark:border-slate-700 dark:bg-slate-900"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 flex items-center justify-between border-b border-slate-200 bg-white/90 px-5 py-3 backdrop-blur dark:border-slate-700 dark:bg-slate-900/90">
          <h3 className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white">
            <GraduationCap size={18} className="text-brand-500" /> Hướng dẫn & Thuật ngữ
          </h3>
          <button onClick={onClose} className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800">
            <X size={18} />
          </button>
        </div>

        <div className="space-y-6 p-5 text-sm text-slate-700 dark:text-slate-200">
          <Section icon={Lightbulb} title="Cách dùng nhanh">
            <ul className="space-y-1.5 pl-1">
              <li>• <strong>Gõ đề trực tiếp</strong>: “Tối đa hóa 3x + 2y với điều kiện x + 2y ≤ 6, …”.</li>
              <li>• <strong>Mô tả bằng lời</strong>: kể bài toán thực tế, hệ thống tự mô hình hóa.</li>
              <li>• 📷 <strong>Ảnh đề</strong>: chụp/tải ảnh đề (kể cả viết tay) → AI đọc và điền sẵn.</li>
              <li>• <strong>Nhập theo form</strong>: bấm “Nhập form” để điền chính xác từng hệ số.</li>
              <li>• <strong>Chọn phương pháp</strong> ở ô nhập, hoặc gõ “bằng phương pháp hình học”.</li>
              <li>• <strong>Luyện tập</strong>: tự giải → chấm điểm; <strong>“tạo bài tập”</strong>, <strong>“so sánh”</strong>, <strong>“giải thích bước 1”</strong>.</li>
            </ul>
          </Section>

          <Section icon={Workflow} title="Các phương pháp giải">
            <div className="space-y-2">
              {METHODS.map(([name, desc]) => (
                <div key={name} className="rounded-lg bg-slate-50 p-2.5 dark:bg-slate-800/50">
                  <span className="font-medium text-slate-800 dark:text-slate-100">{name}</span>
                  <p className="text-[13px] leading-snug text-slate-500 dark:text-slate-400">{desc}</p>
                </div>
              ))}
            </div>
          </Section>

          <Section icon={BookOpen} title="Thuật ngữ cơ bản">
            <dl className="divide-y divide-slate-100 dark:divide-slate-800">
              {GLOSSARY.map(([term, def]) => (
                <div key={term} className="grid grid-cols-[8.5rem_1fr] gap-2 py-1.5">
                  <dt className="font-medium text-slate-800 dark:text-slate-100">{term}</dt>
                  <dd className="text-[13px] leading-snug text-slate-500 dark:text-slate-400">{def}</dd>
                </div>
              ))}
            </dl>
          </Section>
        </div>
      </div>
    </div>
  )
}
