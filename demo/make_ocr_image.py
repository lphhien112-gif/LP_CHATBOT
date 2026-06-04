# -*- coding: utf-8 -*-
"""Sinh ảnh đề bài LP (giả lập ảnh chụp đề) để minh hoạ tính năng OCR trong video demo."""
from PIL import Image, ImageDraw, ImageFont
import os

OUT = os.path.join(os.path.dirname(__file__), "assets", "ocr_problem.png")

W, H = 1000, 720
# nền hơi ngả vàng như giấy
img = Image.new("RGB", (W, H), (250, 248, 240))
d = ImageDraw.Draw(img)


def font(path_candidates, size):
    for p in path_candidates:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


FONTS = r"C:\Windows\Fonts"
f_title = font([os.path.join(FONTS, "timesbd.ttf"), os.path.join(FONTS, "arialbd.ttf")], 40)
f_body = font([os.path.join(FONTS, "times.ttf"), os.path.join(FONTS, "arial.ttf")], 38)
f_small = font([os.path.join(FONTS, "ariali.ttf"), os.path.join(FONTS, "arial.ttf")], 26)

# khung viền
d.rectangle([24, 24, W - 24, H - 24], outline=(60, 60, 70), width=3)

y = 60
d.text((60, y), "ĐỀ BÀI — QUY HOẠCH TUYẾN TÍNH", font=f_title, fill=(20, 30, 80))
y += 70
d.line([60, y, W - 60, y], fill=(160, 160, 170), width=2)
y += 30

lines = [
    "Tìm phương án tối ưu của bài toán sau:",
    "",
    "      Tối đa hóa   z = 4x1 + 6x2",
    "",
    "      với các ràng buộc:",
    "          2x1 + 3x2 <= 12",
    "          x1  + 3x2 <= 9",
    "          x1 , x2 >= 0",
]
for ln in lines:
    d.text((60, y), ln, font=f_body, fill=(25, 25, 30))
    y += 56

d.text((60, H - 50), "Học phần Quy hoạch tuyến tính", font=f_small, fill=(120, 120, 130))

img.save(OUT)
print("saved", OUT, img.size)
