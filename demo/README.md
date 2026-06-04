# Demo — quay video tự động

Thư mục này chứa video demo LP_Chatbot và script tạo lại nó bằng **Playwright**.

## Sản phẩm

| File | Mô tả |
|------|-------|
| `assets/lp_chatbot_demo.mp4` | Video demo đầy đủ (~2 phút, 1280×800, H.264) |
| `assets/lp_chatbot_demo.gif` | GIF hero — cảnh giải đơn hình từng bước |
| `assets/feat_geometric.gif` | GIF — phương pháp hình học (miền nghiệm) |
| `assets/feat_nlp.gif` | GIF — nhập bằng lời (NLP) |
| `assets/feat_ocr.gif` | GIF — đọc đề từ ảnh (OCR) |
| `assets/feat_practice.gif` | GIF — luyện tập có chấm điểm |
| `assets/ocr_problem.png` | Ảnh đề mẫu dùng cho cảnh OCR |

## Kịch bản video (7 cảnh)

0. Intro → 1. **Đơn hình** từng bước → 2. **Hình học** (miền nghiệm) →
3. Nhập **bằng lời** (NLP) → 4. **OCR** (đọc đề từ ảnh) →
5. **So sánh phương pháp** → 6. **Luyện tập** có chấm điểm → Outro.

## Cách tạo lại

Yêu cầu: **backend đang chạy** ở `http://localhost:8000`, có `OPENAI_API_KEY` hợp lệ
trong `.env` (các cảnh NLP/OCR cần LLM). Node + Playwright đã có sẵn trong `frontend/node_modules`.

```bash
# 1) (tùy chọn) tạo lại ảnh đề OCR
python demo/make_ocr_image.py            # cần Pillow

# 2) quay video → demo/raw/*.webm
node demo/record_demo.mjs

# 3) chuyển sang MP4 chất lượng cao
ffmpeg -y -i demo/raw/*.webm -movflags +faststart -c:v libx264 -preset slow \
  -crf 20 -pix_fmt yuv420p -vf "scale=1280:800:flags=lanczos,fps=30" \
  demo/assets/lp_chatbot_demo.mp4

# 4) tạo GIF highlight (cảnh đơn hình, ~t=9..23)
ffmpeg -y -ss 9 -t 14 -i demo/assets/lp_chatbot_demo.mp4 \
  -vf "fps=11,scale=760:-1:flags=lanczos,palettegen=stats_mode=diff" /tmp/pal.png
ffmpeg -y -ss 9 -t 14 -i demo/assets/lp_chatbot_demo.mp4 -i /tmp/pal.png \
  -lavfi "fps=11,scale=760:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=3" \
  demo/assets/lp_chatbot_demo.gif
```

## Ghi chú

- Script dùng **Node Playwright** (`record_demo.mjs`). Bản Python không dùng được trên venv
  Python 3.14 ở máy này vì `greenlet` chưa có wheel tương thích.
- Caption/overlay được chèn bằng JS (`page.evaluate`) nên không phụ thuộc thay đổi giao diện;
  caption có `pointer-events:none` để không chặn thao tác chuột.
- Nếu giao diện đổi nhãn nút, cập nhật các selector trong `record_demo.mjs`
  (vd: `Làm mới hội thoại`, `So sánh phương pháp`, `Luyện tập có chấm điểm`).
