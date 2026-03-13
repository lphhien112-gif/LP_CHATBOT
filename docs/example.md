# VÍ DỤ GIẢI BÀI TOÁN QHTT — TRÌNH BÀY XOAY TRỰC TIẾP

Tài liệu này minh họa các phương pháp giải bài toán QHTT theo đúng cấu trúc lý thuyết trong `theory.md`. Mọi bước xoay đều được trình bày dưới dạng bảng `array` LaTeX với mũi tên $\overset{\downarrow}{}$ (biến vào) và $\leftarrow$ (biến ra).

---

## 1. Phương pháp Đơn hình gốc (Mục 3.2 — $b > 0$)

**Bài toán:**

$$\begin{cases}
\min z = -3x_1 - 2x_2 \\
x_1 + 2x_2 \le 6 \\
2x_1 + x_2 \le 8 \\
x_1, x_2 \ge 0
\end{cases}$$

**Từ vựng xuất phát:**

\[
\begin{array}{rrl}
& z &= \overset{\downarrow}{-} 3x_1 - 2x_2 \\
\hline
& w_1 &= 6 - x_1 - 2x_2 \quad \frac{6}{1} = 6 \\
\leftarrow & w_2 &= 8 - 2x_1 - x_2 \quad \frac{8}{2} = 4
\end{array}
\]

Biến vào: $x_1$ (hệ số âm nhất $-3$). Biến ra: $w_2$ (tỷ số nhỏ nhất $4$).
$x_1 = 4 - 0,5x_2 - 0,5w_2$

\[
\begin{array}{rrl}
& z &= -12 \overset{\downarrow}{-} 0,5x_2 + 1,5w_2 \\
\hline
\leftarrow & w_1 &= 2 - 1,5x_2 + 0,5w_2 \quad \frac{2}{1,5} = \frac{4}{3} \\
& x_1 &= 4 - 0,5x_2 - 0,5w_2 \quad \frac{4}{0,5} = 8
\end{array}
\]

Biến vào: $x_2$ (hệ số $-0,5$). Biến ra: $w_1$ (tỷ số $\frac{4}{3}$).
$x_2 = \frac{4}{3} - \frac{2}{3}w_1 + \frac{1}{3}w_2$

\[
\begin{array}{rrl}
& z &= -\frac{38}{3} + \frac{1}{3}w_1 + \frac{4}{3}w_2 \\
\hline
& x_2 &= \frac{4}{3} - \frac{2}{3}w_1 + \frac{1}{3}w_2 \\
& x_1 &= \frac{10}{3} + \frac{1}{3}w_1 - \frac{2}{3}w_2
\end{array}
\]

Cho $w_1 = 0, w_2 = 0, x_1 = \frac{10}{3}, x_2 = \frac{4}{3}$ \\
GTTƯ: $z = -\frac{38}{3}$

---

## 2. Phương pháp xoay Bland (Mục 3.3 — $\exists b_i = 0$)

\textbf{Phương pháp xoay Bland:}

\textbf{Chọn biến vào:} Trong số các biến không cơ sở có hệ số âm ($G < 0$) \\
Chọn \textbf{biến có chỉ số nhỏ nhất} ($x_1, x_2, x_3, w_1, w_2$)

\textbf{Chọn biến ra:} Y như đơn hình tính $\frac{b_i}{a_{ij}} (=0)$

\textbf{\underline{VD:}}

Giả sử ta đang ở giữa bài toán và gặp từ vựng suy biến:

\[
\begin{array}{rrl}
& z &= 10 \overset{\downarrow}{-} 2x_1 - 3x_2 - 3x_3 \\
\hline
\leftarrow & w_1 &= 0 - x_1 + 2x_2 + x_3 \quad \frac{0}{1} = 0 \\
& w_2 &= 5 - 2x_1 - x_2 + 2x_3 \quad \frac{5}{2} = 2,5
\end{array}
\]

Theo Dantzig thông thường: chọn $x_2$ hoặc $x_3$ (hệ số âm nhất $-3$).
Theo **Bland**: trong $\{x_1, x_2, x_3\}$ đều có hệ số âm $\rightarrow$ chọn $x_1$ (chỉ số nhỏ nhất).
Biến ra: $w_1$ có tỷ số $0$ (nhỏ nhất). Nếu nhiều dòng cùng tỷ số $0$, cũng chọn biến có chỉ số nhỏ nhất.

$x_1 = 0 - w_1 + 2x_2 + x_3$

\[
\begin{array}{rrl}
& z &= 10 + 2w_1 - 7x_2 - 5x_3 \\
\hline
& x_1 &= 0 - w_1 + 2x_2 + x_3 \\
& w_2 &= 5 + 2w_1 - 5x_2
\end{array}
\]

Thuật toán tiếp tục tiến lên mà không bị mắc kẹt tại $b_i = 0$.

---

## 3. Thuật toán 2 Pha (Mục 3.4 — $\exists b_i < 0$)

**Bài toán:**

$$\begin{cases}
\min z = x_1 + x_2 \\
-x_1 - x_2 \le -2 \quad (\exists b_i < 0) \\
x_1 - x_2 \le 1 \\
x_1, x_2 \ge 0
\end{cases}$$

### Pha 1: Bài toán bổ trợ $(\Delta)$: $\min \xi = x_0$

Từ vựng xuất phát $(\Delta)$:

\[
\begin{array}{rrl}
& \xi &= 0 + x_0 \\
\hline
\leftarrow & w_1 &= -2 + x_1 + x_2 \overset{\downarrow}{+} x_0 \\
& w_2 &= 1 - x_1 + x_2 + x_0
\end{array}
\]

Xoay đặc biệt: biến vào $x_0$, biến ra $w_1$ (hằng số âm nhất $-2$).
$x_0 = 2 - x_1 - x_2 + w_1$

\[
\begin{array}{rrl}
& \xi &= 2 \overset{\downarrow}{-} x_1 - x_2 + w_1 \\
\hline
& x_0 &= 2 - x_1 - x_2 + w_1 \quad \frac{2}{1} = 2 \\
\leftarrow & w_2 &= 3 - 2x_1 + w_1 \quad \frac{3}{2} = 1,5
\end{array}
\]

Biến vào: $x_1$ (hệ số $-1$). Biến ra: $w_2$ (tỷ số $1,5$).
$x_1 = 1,5 - 0,5w_2 + 0,5w_1$

\[
\begin{array}{rrl}
& \xi &= 0,5 \overset{\downarrow}{-} x_2 + 0,5w_1 + 0,5w_2 \\
\hline
\leftarrow & x_0 &= 0,5 - x_2 + 0,5w_1 + 0,5w_2 \quad \frac{0,5}{1} = 0,5 \\
& x_1 &= 1,5 + 0,5w_1 - 0,5w_2
\end{array}
\]

Biến vào: $x_2$ (hệ số $-1$). Biến ra: $x_0$ (tỷ số $0,5$).
$x_2 = 0,5 - x_0 + 0,5w_1 + 0,5w_2$

\[
\begin{array}{rrl}
& \xi &= 0 + x_0 \\
\hline
& x_2 &= 0,5 - x_0 + 0,5w_1 + 0,5w_2 \\
& x_1 &= 1,5 + 0,5w_1 - 0,5w_2
\end{array}
\]

Kết thúc Pha 1: $\xi = 0 \Rightarrow x_0 = 0$. Từ vựng đã chấp nhận được!

### Pha 2: Lắp hàm mục tiêu gốc

Cho $x_0 = 0$. Thế vào hàm mục tiêu gốc $z = x_1 + x_2$:
$z = (1,5 + 0,5w_1 - 0,5w_2) + (0,5 + 0,5w_1 + 0,5w_2) = 2 + w_1$

\[
\begin{array}{rrl}
& z &= 2 + w_1 \\
\hline
& x_2 &= 0,5 + 0,5w_1 + 0,5w_2 \\
& x_1 &= 1,5 + 0,5w_1 - 0,5w_2
\end{array}
\]

Mọi hệ số của $z$ đều $\ge 0$ $\Rightarrow$ Từ vựng tối ưu, không cần xoay thêm!
Cho $w_1 = 0, w_2 = 0, x_1 = 1,5, x_2 = 0,5$ \\
GTTƯ: $z = 2$

---

## 4. Thuật toán Đơn hình Đối ngẫu (Mục 3.7 — $\exists b_i < 0$)

**Bài toán:**

$$\begin{cases}
\min z = 2x_1 + 3x_2 \\
-x_1 - 2x_2 \le -4 \\
-2x_1 - x_2 \le -5 \\
x_1, x_2 \ge 0
\end{cases}$$

**Từ vựng xuất phát** (hệ số $z$ đều $\ge 0$ nhưng $b_i < 0$):

\[
\begin{array}{rrl}
& z &= 2x_1 + 3x_2 \\
\hline
& w_1 &= -4 + x_1 + 2x_2 \\
\leftarrow & w_2 &= -5 + 2\overset{\downarrow}{x_1} + x_2
\end{array}
\]

Chọn biến ra trước: $w_2$ ($b_2 = -5$ âm nhất).
Chọn biến vào sau: $\min\left\{\frac{2}{2}, \frac{3}{1}\right\} = \min(1, 3) = 1 \Rightarrow x_1$.

$x_1 = 2,5 - 0,5x_2 + 0,5w_2$

\[
\begin{array}{rrl}
& z &= 5 + 2\overset{\downarrow}{x_2} + w_2 \\
\hline
\leftarrow & w_1 &= -1,5 + 1,5x_2 + 0,5w_2 \\
& x_1 &= 2,5 - 0,5x_2 + 0,5w_2
\end{array}
\]

Biến ra: $w_1$ ($b_1 = -1,5$ âm).
Chọn biến vào: $\min\left\{\frac{2}{1,5}, \frac{1}{0,5}\right\} = \min(\frac{4}{3}, 2) = \frac{4}{3} \Rightarrow x_2$.

$x_2 = 1 + \frac{2}{3}w_1 - \frac{1}{3}w_2$

\[
\begin{array}{rrl}
& z &= 7 + \frac{4}{3}w_1 + \frac{1}{3}w_2 \\
\hline
& x_2 &= 1 + \frac{2}{3}w_1 - \frac{1}{3}w_2 \\
& x_1 &= 2 - \frac{1}{3}w_1 + \frac{2}{3}w_2
\end{array}
\]

Mọi $b_i \ge 0$ và mọi hệ số $z \ge 0$ $\Rightarrow$ Tối ưu!
Cho $w_1 = 0, w_2 = 0, x_1 = 2, x_2 = 1$ \\
GTTƯ: $z = 7$

---

## 5. Thuật toán 2 Pha Đối ngẫu - Gốc (Mục 3.8)

**Tình huống:** $\exists b_i < 0$ nhưng hệ số $z$ có giá trị âm $\Rightarrow$ không chạy được Đơn hình Đối ngẫu trực tiếp.

$$\begin{cases}
\min z = -2x_1 + 3x_2 \\
-x_1 - x_2 \le -4 \\
x_1, x_2 \ge 0
\end{cases}$$

### Pha 1: Bài toán bổ trợ

Lấy $|c_i|$ để ép hệ số $\ge 0$: $z_{BT} = 2x_1 + 3x_2$

\[
\begin{array}{rrl}
& z_{BT} &= 2\overset{\downarrow}{x_1} + 3x_2 \\
\hline
\leftarrow & w_1 &= -4 + x_1 + x_2 \quad \frac{|-4|}{1}
\end{array}
\]

Chạy Đơn hình Đối ngẫu: biến ra $w_1$ ($b = -4$), biến vào $x_1$ ($\frac{2}{1} < \frac{3}{1}$).
$x_1 = 4 - x_2 + w_1$

\[
\begin{array}{rrl}
& z_{BT} &= 8 + x_2 + 2w_1 \\
\hline
& x_1 &= 4 - x_2 + w_1
\end{array}
\]

Mọi $b_i \ge 0$ $\Rightarrow$ Từ vựng khả thi thu được!

### Pha 2: Lắp hàm mục tiêu gốc

Bỏ $z_{BT}$, lắp $z = -2x_1 + 3x_2$:
$z = -2(4 - x_2 + w_1) + 3x_2 = -8 + 5x_2 - 2w_1$

\[
\begin{array}{rrl}
& z &= -8 + 5x_2 - 2w_1 \\
\hline
& x_1 &= 4 - x_2 + w_1
\end{array}
\]

Mọi hệ số $z$ nhìn: $+5 \ge 0$ nhưng $-2 < 0$. Cần xoay thêm?
Thực tế $w_1$ là biến bù (luôn $\ge 0$), hệ số $-2$ ứng với $w_1$: dòng duy nhất có $w_1$ với hệ số $+1 > 0$ nên không có biến ra hợp lệ.
$\Rightarrow$ Bài toán **không giới nội** ($z \to -\infty$).

---

## 6. Xây dựng Bài toán Đối ngẫu (Mục 3.5)

**Bài toán Gốc (P):**

$$\begin{cases}
\min 5x_1 - 2x_2 \\
2x_1 + x_2 \ge 3 \\
x_1 - 3x_2 \le 4 \\
x_1 \ge 0, x_2 \text{ tự do}
\end{cases}$$

**Bài toán Đối ngẫu (D):**

| Gốc (P) | Đối ngẫu (D) |
| --- | --- |
| $\min 5x_1 - 2x_2$ | $\max 3y_1 + 4y_2$ |
| RB1: $\ge 3$ | $y_1 \ge 0$ |
| RB2: $\le 4$ | $y_2 \le 0$ |
| $x_1 \ge 0$ | $2y_1 + y_2 \le 5$ |
| $x_2$ tự do | $y_1 - 3y_2 = -2$ |

$$\Rightarrow (D): \begin{cases}
\max 3y_1 + 4y_2 \\
2y_1 + y_2 \le 5 \\
y_1 - 3y_2 = -2 \\
y_1 \ge 0, y_2 \le 0
\end{cases}$$

---

## 7. Độ lệch bù (Complementary Slackness — Mục 3.6)

**Bài toán gốc (P):** $\max z = 3x_1 + 2x_2$
(1) $x_1 \le 4$, (2) $x_2 \le 6$, (3) $x_1 + x_2 \le 8$

**Bài toán đối ngẫu (D):** $\min v = 4y_1 + 6y_2 + 8y_3$
(1) $y_1 + y_3 \ge 3$, (2) $y_2 + y_3 \ge 2$

Giả sử đã biết nghiệm tối ưu của (D): $y^* = (1, 0, 2)$.

**Áp dụng định lý độ lệch bù:**

**Bước 1:** Thế $y^*$ vào ràng buộc của (D):
* (1) $1 + 2 = 3 \ge 3$ (Chặt) $\Rightarrow$ $x_1$ có thể $> 0$.
* (2) $0 + 2 = 2 \ge 2$ (Chặt) $\Rightarrow$ $x_2$ có thể $> 0$.

**Bước 2:** Xét $y^*$:
* $y_1 = 1 > 0 \Rightarrow$ RB (1) của (P) chặt: $x_1 = 4$.
* $y_2 = 0 \Rightarrow$ Không ép thêm thông tin.
* $y_3 = 2 > 0 \Rightarrow$ RB (3) của (P) chặt: $x_1 + x_2 = 8$.

**Bước 3:** Giải hệ:
$\begin{cases} x_1 = 4 \\ x_1 + x_2 = 8 \end{cases} \Rightarrow x_1 = 4, x_2 = 4$

GTTƯ: $z = 3(4) + 2(4) = 20$.
