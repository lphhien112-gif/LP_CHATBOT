# Hướng Dẫn Quy Trình Làm Việc Với Git (Git Workflow)

Tài liệu này hướng dẫn quy trình tiêu chuẩn khi làm việc với Git trong dự án. Việc tuân thủ quy trình này giúp làm việc nhóm hiệu quả, tránh xung đột code và dễ dàng theo dõi lịch sử phát triển.

## 1. Các Nhánh (Branches) Chính

- `main` hoặc `master`: Nhánh chính chứa flow code đã ổn định và sẵn sàng chạy (production-ready). **Không bao giờ commit trực tiếp lên nhánh này.**
- `develop` (tuỳ chọn - nếu dự án quy mô lớn hơn): Nhánh chứa các đoạn code mới nhất đã lấy từ các nhánh tính năng để test cùng nhau trước khi đưa lên nhánh `main`.

## 2. Quy Tắc Đặt Tên Nhánh (Branch Naming Convention)

Khi bắt đầu làm một công việc mới, hãy tạo một nhánh mới từ nhánh gốc (`main` hoặc `develop`).

Cú pháp: `<loại_nhánh>/<tên-ngắn-gọn-của-task>`

**Các loại nhánh thông dụng:**
- `feature/...`: Dành cho việc phát triển tính năng mới. (Ví dụ: `feature/add-login`, `feature/logging-setup`)
- `bugfix/...` hoặc `fix/...`: Dành cho việc sửa lỗi. (Ví dụ: `fix/api-crash-on-null`)
- `hotfix/...`: Dành cho việc sửa lỗi khẩn cấp trên bản production. (Ví dụ: `hotfix/fix-payment-bug`)
- `docs/...`: Dành cho việc viết hoặc cập nhật tài liệu.

**Cách tạo nhánh mới:**
```bash
# Đảm bảo bạn đang ở nhánh chính và có code mới nhất
git checkout main
git pull origin main

# Tạo và chuyển sang nhánh mới
git checkout -b feature/ten-tinh-nang
```

## 3. Quy Tắc Viết Commit Message (Conventional Commits)

Nên chia nhỏ các commit để dễ kiểm soát và không nên gom quá nhiều file rác. Mỗi commit message nên rõ ràng và tuân thủ quy tắc sau:

Cú pháp: `loại_commit: Mô tả ngắn gọn công việc (bằng tiếng Việt hoặc tiếng Anh)`

**Các chuẩn loại commit:**
- `feat:`: Thêm tính năng mới (Feature)
- `fix:`: Sửa lỗi (Bug fix)
- `docs:`: Thay đổi tài liệu (Documentation)
- `style:`: Sửa đổi format code (xoá khoảng trắng, thiếu dấu phẩy,... không thay đổi logic)
- `refactor:`: Cấu trúc lại code nhưng không thêm tính năng hay sửa lỗi
- `test:`: Thêm hoặc chỉnh sửa test cases
- `chore:`: Các thay đổi nhỏ về cấu hình, build tool, thư viện,... không ảnh hưởng đến code của người dùng

**Ví dụ:**
```bash
git commit -m "feat: thêm chức năng đăng nhập cho người dùng"
git commit -m "fix: sửa lỗi crash hệ thống khi nhận payload rỗng"
git commit -m "docs: cập nhật file readme hướng dẫn cài đặt"
```

## 4. Quá Trình Làm Việc Hàng Ngày (Daily Workflow)

### Bước 1: Cập nhật code mới nhất từ nhánh chính
Trước khi bắt đầu code mỗi ngày, hãy cập nhật những thay đổi mới nhất từ nhánh chính vào nhánh làm việc của bạn để tránh dồn xung đột lớn về sau.

```bash
git checkout main
git pull origin main
git checkout feature/ten-nhanh-cua-ban
git merge main  # hoặc 'git rebase main' nếu bạn quen dùng rebase
```

### Bước 2: Viết code và commit
Thực hiện code cho tính năng/fix lỗi. Khi xong một phần code ý nghĩa, hãy commit lại:
```bash
git status
git add [tên_file]  # Hoặc dùng 'git add .' để thêm tất cả thay đổi
git commit -m "feat: [Mô tả rõ ràng những gì vừa làm]"
```

### Bước 3: Đẩy code (Push) lên Remote Repository (GitHub/GitLab)
```bash
git push origin feature/ten-nhanh-cua-ban
```
*(Lưu ý: Lần push đầu tiên của nhánh này có thể bạn cần dùng: `git push -u origin feature/ten-nhanh-cua-ban`)*

## 5. Tạo Pull Request (PR) / Merge Request (MR)

1. Truy cập vào giao diện web (GitHub/GitLab,..) của dự án.
2. Sẽ có nút **"Compare & pull request"** được gợi ý cho nhánh bạn vừa push.
3. Tạo PR, điền tiêu đề và mô tả rõ ràng:
   - Code này thay đổi những gì? Giải quyết vấn đề gì?
   - Có cần lưu ý gì khi test tính năng này không?
4. Thêm người **Reviewers** trong team để họ kiểm tra code chéo.
5. Sau khi code được duyệt (Approve) và không có xung đột (No conflicts), tiến hành nhấn nút **Merge pull request** để đưa code vào nhánh `main`.

## 6. Xử Lý Xung Đột Code (Merge Conflicts)

Xung đột xảy ra khi nhiều người cùng chỉnh sửa vào thay đổi ở một dòng code, hoặc một người xóa chức năng mà người kia lại sửa chức năng đó.

1. Lấy code mới từ nhánh chính về nhánh của bạn:
```bash
git checkout feature/nhanh-cua-ban
git merge main 
```
2. Nếu có `conflict`, terminal (hoặc trình soạn thảo) sẽ báo file nào bị xung đột. Mở những file đó lên (trên VSCode hoặc WebStorm sẽ có giao diện highlight màu xanh lá/xanh dương hỗ trợ xử lý rất trực quan).
3. Chọn các thay đổi muốn giữ lại:
   - Accept Current Change (Giữ phần của bạn).
   - Accept Incoming Change (Lấy phần code người khác).
   - Accept Both Changes (Lấy cả hai và tự tay chỉnh sửa lại).
4. Lưu file lại, kiểm tra code đảm bảo không lỗi, tiến hành commit lại quá trình giải quyết xung đột:
```bash
git add .
git commit -m "chore: resolve merge conflicts with main"
git push origin feature/nhanh-cua-ban
```

---

## ⚡ Tóm Tắt Nhanh Quy Trình Chuẩn (Cheatsheet)

1. `git checkout main` và `git pull` tải bản mới nhất về nhánh main cục bộ.
2. `git checkout -b feature/tên-nhánh` để tạo và di chuyển sang nhánh làm việc.
3. Viết code...
4. `git add .` và `git commit -m "feat: mô tả công việc"`.
5. `git push origin feature/tên-nhánh`.
6. Lên web tạo **Pull Request (PR)**, tag người review.
7. Khi PR được gộp (merged) thành công -> Chuyển về nhánh `main` ở dưới máy tính (`git checkout main`), update code về (`git pull`) và tiếp tục công việc mới.
