Ví dụ cho xoay đơn hình:

### 1. Đề bài (Bài toán gốc)
*   **Hàm mục tiêu:** $\max z = 3x_1 + 2x_2$
*   **Hệ ràng buộc:**
    (1) $-x_1 + x_2 \le 1$
    (2) $x_1 + 2x_2 \le 6$
    *Điều kiện:* $x_1 \ge 0, x_2 \ge 0$

---

### 2. Các bước giải chi tiết

**Bước 1: Chuyển về dạng chuẩn và Xây dựng từ vựng xuất phát**
Trước tiên, ta đổi bài toán $\max$ thành bài toán $\min$ bằng cách đặt $z' = -z$. 
$\Rightarrow$ Hàm mục tiêu mới: $\min z' = -3x_1 - 2x_2$.

Tiếp theo, thêm các biến bù (biến phụ) $w_1 \ge 0$ và $w_2 \ge 0$ vào hệ bất phương trình để biến chúng thành phương trình:
*   $-x_1 + x_2 + w_1 = 1 \Rightarrow w_1 = 1 + x_1 - x_2$
*   $x_1 + 2x_2 + w_2 = 6 \Rightarrow w_2 = 6 - x_1 - 2x_2$

**Từ vựng xuất phát** được lập bằng cách biểu diễn các biến cơ sở ($w_1, w_2$) và hàm mục tiêu theo các biến ngoài hệ ($x_1, x_2$):
*   $w_1 = 1 + x_1 - x_2$
*   $w_2 = 6 - x_1 - 2x_2$
*   $z' = -3x_1 - 2x_2$

*Đánh giá khả thi:* Khi cho $x_1 = 0, x_2 = 0$, ta có $w_1 = 1 \ge 0$ và $w_2 = 6 \ge 0$. Hệ hằng số vế phải đều dương nên từ vựng này khả thi, có thể bắt đầu lặp.

**Bước 2: Xoay đơn hình (Lần lặp 1)**
*   **Chọn biến vào (Entering Variable):** Nhìn vào hàm mục tiêu $z' = -3x_1 - 2x_2$, cả hai biến $x_1$ và $x_2$ đều có hệ số âm ($-3$ và $-2$). Theo quy tắc, ta chọn biến có hệ số âm nhất (hoặc theo chỉ số nhỏ nhất) làm biến vào $\Rightarrow$ **Chọn $x_1$**.
*   **Chọn biến ra (Leaving Variable):** Ta xét xem $w_1$ hay $w_2$ sẽ bị giới hạn trước khi $x_1$ tăng lên (với $x_2 = 0$):
    *   Tại phương trình 1: $w_1 = 1 + x_1$. Khi $x_1$ tăng, $w_1$ cũng tăng theo $\Rightarrow$ $w_1$ không giới hạn sự gia tăng của $x_1$.
    *   Tại phương trình 2: $w_2 = 6 - x_1$. Để đảm bảo $w_2 \ge 0$, ta phải có $x_1 \le 6$.
    *   $\Rightarrow$ $w_2$ là biến cản trở khắt khe nhất nên ta **chọn $w_2$ làm biến ra**.

**Bước 3: Lập từ vựng mới (Từ vựng trung gian)**
Ta rút $x_1$ từ phương trình của $w_2$ để đẩy $x_1$ vào hệ cơ sở và đẩy $w_2$ ra ngoài:
$w_2 = 6 - x_1 - 2x_2 \Rightarrow \mathbf{x_1 = 6 - 2x_2 - w_2}$

Thế $x_1$ vào phương trình của $w_1$ và hàm mục tiêu $z'$:
*   $w_1 = 1 + (6 - 2x_2 - w_2) - x_2 \Rightarrow \mathbf{w_1 = 7 - 3x_2 - w_2}$
*   $z' = -3(6 - 2x_2 - w_2) - 2x_2 = -18 + 6x_2 + 3w_2 - 2x_2 \Rightarrow \mathbf{z' = -18 + 4x_2 + 3w_2}$

**Hệ từ vựng mới thu được:**
*   $x_1 = 6 - 2x_2 - w_2$
*   $w_1 = 7 - 3x_2 - w_2$
*   $z' = -18 + 4x_2 + 3w_2$

**Bước 4: Kiểm tra tính tối ưu và Kết luận**
*   Nhìn vào hàm mục tiêu ở từ vựng mới: $z' = -18 + 4x_2 + 3w_2$.
*   Tất cả các hệ số của các biến ngoài hệ ($x_2$ và $w_2$) hiện tại đều mang dấu dương ($+4$ và $+3$). Điều này có nghĩa là việc tăng bất kỳ biến nào lên cũng chỉ làm giá trị của $z'$ tăng theo (kém đi đối với bài toán $\min$), nên **từ vựng này đã đạt tối ưu**.
*   Cho các biến ngoài hệ bằng $0$ ($x_2 = 0, w_2 = 0$), ta đọc được nghiệm tối ưu:
    *   $x_1 = 6$
    *   $w_1 = 7$
    *   $z' = -18$

**Kết luận cuối cùng cho bài toán gốc ($\max z$):** 
Nghiệm tối ưu của bài toán là $\mathbf{(x_1, x_2) = (6, 0)}$ và giá trị lớn nhất của hàm mục tiêu là $\mathbf{z^* = -(-18) = 18}$. 

*(Lưu ý đính chính: Ở một số hội thoại trước, có nhắc nhầm nghiệm là (4,1) và z=14. Dựa theo chính xác các bước giải ma trận xoay đơn hình trong sổ tay, kết quả chuẩn xác là (6,0) với z=18).*

---

### 3. Thuật toán 2 Pha (Two-Phase Algorithm) (Bao gồm chuyển Pha 2)
Áp dụng khi từ vựng xuất phát ban đầu vi phạm tính khả thi (có hằng số $b_i < 0$).

**Bài toán gốc:** $\min z = -x_1 - 3x_2$
**Ràng buộc:**
(1) $-x_1 + x_2 \le 1$
(2) $x_1 + x_2 \ge 2 \Rightarrow -x_1 - x_2 \le -2$  *(hằng số âm)*
(3) $x_1 \le 3$

**Pha 1: Bài toán bổ trợ**
Thêm biến giả $x_0 \ge 0$. Hàm mục tiêu Pha 1 là $\min w = x_0$ (hay $\max -w = -x_0$).
Từ vựng khởi tạo Pha 1:
\[
\begin{array}{rrl}
& -w &= 0 - x_0 \\
\hline
& w_1 &= 1 + x_1 - x_2 \overset{\downarrow}{+} x_0 \\
\leftarrow & w_2 &= -2 + x_1 + x_2 \overset{\downarrow}{+} x_0 \\
& w_3 &= 3 - x_1 \overset{\downarrow}{+} x_0 
\end{array}
\]

*Xoay đặc biệt:* Ép $x_0$ vào hệ (với hệ số $+1$), chọn biến có hằng số âm nhất ($w_2$) ra khỏi hệ.
$x_0 = 2 - x_1 - x_2 + w_2$

\[
\begin{array}{rrl}
& -w &= -2 + x_1 \overset{\downarrow}{+} x_2 - w_2 \\
\hline
\leftarrow & w_1 &= 3 - 2x_2 + w_2 \quad \frac{3}{2} = 1,5 \\
& x_0 &= 2 - x_1 - x_2 + w_2 \quad \frac{2}{1} = 2 \\
& w_3 &= 5 - 2x_1 - x_2 + w_2 \quad \frac{5}{1} = 5
\end{array}
\]

*Lặp Phase 1 - Xoay 1:* Biến vào $x_2$, biến ra $w_1$.
$x_2 = 1,5 - 0,5w_1 + 0,5w_2$

\[
\begin{array}{rrl}
& -w &= -0,5 \overset{\downarrow}{+} x_1 - 0,5w_1 - 0,5w_2 \\
\hline
& x_2 &= 1,5 - 0,5w_1 + 0,5w_2 \\
\leftarrow & x_0 &= 0,5 - x_1 + 0,5w_1 + 0,5w_2 \quad \frac{0,5}{1} = 0,5 \\
& w_3 &= 3,5 - 2x_1 + 0,5w_1 + 0,5w_2 \quad \frac{3,5}{2} = 1,75
\end{array}
\]

*Lặp Phase 1 - Xoay 2:* Biến vào $x_1$, biến ra $x_0$. 
$x_1 = 0,5 - x_0 + 0,5w_1 + 0,5w_2$.

\[
\begin{array}{rrl}
& -w &= 0 - x_0 \\
\hline
& x_1 &= 0,5 - x_0 + 0,5w_1 + 0,5w_2 \\
& x_2 &= 1,5 + 0,5x_0 - 0,5w_1 + 0,5w_2 \\
& w_3 &= 2,5 + 2x_0 - 0,5w_1 - 0,5w_2
\end{array}
\]
*Kết thúc Pha 1:* Hàm mục tiêu đạt giá trị tối đa $-w = 0$, nghĩa là $x_0 = 0$. Từ vựng đã chấp nhận được!

**Pha 2: Lắp ghép để giải bài toán gốc**
Xóa hoàn toàn $x_0$ đi. Lấy hàm mục tiêu gốc $\min z = -x_1 - 3x_2$ thay các phương trình của biến vào:
$z = -(0,5 + 0,5w_1 + 0,5w_2) - 3(1,5 - 0,5w_1 + 0,5w_2) = -5 + w_1 - 2w_2$

Từ vựng ban đầu của Pha 2 được dựng lên:
\[
\begin{array}{rrl}
& z &= -5 + w_1 \overset{\downarrow}{-} 2w_2 \\
\hline
& x_1 &= 0,5 + 0,5w_1 + 0,5w_2 \\
& x_2 &= 1,5 - 0,5w_1 + 0,5w_2 \\
\leftarrow & w_3 &= 2,5 - 0,5w_1 - 0,5w_2 \quad \frac{2,5}{0,5} = 5
\end{array}
\]
Do là bài toán $\min z$, ta chọn biến có hệ số âm đi vào $\Rightarrow$ $w_2$ vào. Biến ra là $w_3$.
$0,5w_2 = 2,5 - 0,5w_1 - w_3 \Rightarrow w_2 = 5 - w_1 - 2w_3$

\[
\begin{array}{rrl}
& z &= -15 + 3w_1 + 4w_3 \\
\hline
& x_1 &= 3 - w_3 \\
& x_2 &= 4 - w_1 - w_3 \\
& w_2 &= 5 - w_1 - 2w_3
\end{array}
\]
Hàm mục tiêu $z$ có tất cả hệ số $\ge 0$, do đó hàm đã đạt giá trị **nhỏ nhất**!
Kết luận: $\min z = -15$ tại nghiệm tối ưu cấu thành với $x_1 = 3, x_2 = 4$.

---

### 4. Phương pháp Đơn hình Đối ngẫu (Dual Simplex Method)
Khởi đầu từ một từ vựng tối ưu (hệ số hàm mục tiêu $\le 0$ đối với bài toán max) nhưng vi phạm ở hằng số ($b_i < 0$).

**Bài toán:** $\min z = 2x_1 + 3x_2$ với ràng buộc $x_1 + x_2 \ge 2 \Rightarrow -x_1 - x_2 \le -2$.
Đổi để giải: $\max -z = -2x_1 - 3x_2$.

\[
\begin{array}{rrl}
& -z &= -2x_1 - 3x_2 \\
\hline
\leftarrow & w_1 &= -2 \overset{\downarrow}{+} x_1 + x_2 
\end{array}
\]
*Quy tắc xoay đối ngẫu (ngược với đơn hình gốc):*
- **Chọn biến ra trước:** Chọn phương trình có hằng số âm nhất $\Rightarrow$ chọn **$w_1$**.
- **Chọn biến vào sau:** Lấy độ lớn hệ số hàm mục tiêu chia cho hệ số *dương* tương ứng trên phương trình biến ra. 
  * Thay $x_1$: $\frac{|-2|}{1} = 2$
  * Thay $x_2$: $\frac{|-3|}{1} = 3$
  * Chọn min tỷ số $\Rightarrow$ **biến vào là $x_1$**.

Thực hiện rút $x_1$ từ phương trình của $w_1$:
$w_1 = -2 + x_1 + x_2 \Rightarrow \mathbf{x_1 = 2 - x_2 + w_1}$

Tính toán từ vựng mới:
\[
\begin{array}{rrl}
& -z &= -4 - x_2 - 2w_1 \\
\hline
& x_1 &= 2 - x_2 + w_1 
\end{array}
\]
Từ vựng mới có hàm mục tiêu tối ưu (hệ số đều âm) và hằng số dương (khả thi). Bài toán kết thúc với thuật toán kết hợp tại GTTƯ: $z = 4$ tại $x_1 = 2, x_2 = 0$.

---

### 5. Lý thuyết Đối ngẫu và Độ lệch bù (Complementary Slackness)
Phương pháp tìm nghiệm bài toán gốc (P) rất nhanh khi đã biết nghiệm bài toán đối ngẫu (D) mà không cần lập từ vựng xoay.

**Bài toán gốc (P):** $\max z = 3x_1 + 2x_2$
(1) $x_1 \le 4 \quad (w_1)$
(2) $x_2 \le 6 \quad (w_2)$
(3) $x_1 + x_2 \le 8 \quad (w_3)$

**Bài toán đối ngẫu (D):** $\min v = 4y_1 + 6y_2 + 8y_3$
(1) $y_1 + y_3 \ge 3$
(2) $y_2 + y_3 \ge 2$

*Giả sử đã biết sẵn nghiệm tối ưu của (D):* $y^* = (0, 0, 3)$. 

**Áp dụng định lý độ lệch bù:**
- **Bước 1:** Xét các ràng buộc của bài toán đối ngẫu thế $y^*$ vào:
  + (1) $0 + 3 = 3 \ge 3$ (Ràng buộc chặt) $\Rightarrow x_1 \ge 0$.
  + (2) $0 + 3 = 3 > 2$ (Ràng buộc lỏng, slack dư $1$) $\Rightarrow \mathbf{x_2 = 0}$ (biến gốc tương ứng phải bằng $0$).

- **Bước 2:** Xét các giá trị của biến đối ngẫu $y^*$:
  + $y_1 = 0 \Rightarrow$ không cung cấp thông tin thêm.
  + $y_2 = 0 \Rightarrow$ không cung cấp thông tin thêm.
  + $y_3 = 3 > 0 \Rightarrow$ Ràng buộc (3) của bài toán gốc bị ép chặt (không còn slack $w_3 = 0$) $\Rightarrow \mathbf{x_1 + x_2 = 8}$.

- **Bước 3:** Giải hệ phương trình tuyến tính dựa trên các dữ liệu bị ép:
$\begin{cases} x_2 = 0 \\ x_1 + x_2 = 8 \end{cases} \Rightarrow \mathbf{x_1 = 8, x_2 = 0}$

Vị chi, nghiệm gốc tối ưu là $x^* = (8, 0)$, hoàn toàn có thể tính nhẩm ra đáp án ngay lập tức qua đối ngẫu!