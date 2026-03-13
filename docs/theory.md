# TỔNG HỢP LÝ THUYẾT VÀ PHƯƠNG PHÁP GIẢI BÀI TOÁN QUY HOẠCH TUYẾN TÍNH (QHTT)

Tài liệu này tổng hợp cơ sở lý thuyết toán học và chi tiết cách thức hoạt động của các thuật toán giải (Solvers) bài toán Quy hoạch tuyến tính hiện đang được cài đặt trong lõi hệ thống **LP_CHATBOT** (repository: `lphhien112-gif/LP_CHATBOT`).

---

## Mục lục

1. [Các dạng cơ bản của bài toán QHTT](#i-các-dạng-cơ-bản-của-bài-toán-qhtt)
2. [Phân loại tín hiệu nghiệm](#ii-phân-loại-tín-hiệu-nghiệm)
3. [Chi tiết các phương pháp giải (Solvers)](#iii-chi-tiết-các-phương-pháp-giải-solvers)
   - 3.1 [Phương pháp Hình học](#31-phương-pháp-hình-học-geometric-method)
   - 3.2 [Phương pháp Đơn hình (b > 0)](#32-phương-pháp-đơn-hình-simplex-method--b--0)
   - 3.3 [Phương pháp xoay Bland (∃ bᵢ = 0)](#33-phương-pháp-xoay-bland--bᵢ--0)
   - 3.4 [Thuật toán 2 Pha (∃ bᵢ < 0)](#34-thuật-toán-2-pha-two-phase--bᵢ--0)
   - 3.5 [Bài toán Đối ngẫu](#35-bài-toán-đối-ngẫu-duality)
   - 3.6 [Các định lý Đối ngẫu](#36-các-định-lý-đối-ngẫu)
   - 3.7 [Thuật toán Đơn hình Đối ngẫu](#37-thuật-toán-đơn-hình-đối-ngẫu--bᵢ--0)
   - 3.8 [Thuật toán 2 Pha (Đối ngẫu - Gốc)](#38-thuật-toán-2-pha-đối-ngẫu---gốc)

---

## I. CÁC DẠNG CƠ BẢN CỦA BÀI TOÁN QHTT

### 1.1. Dạng tổng quát

Đây là mô hình nguyên thủy nhất khi dịch từ bài toán thực tế (ví dụ: tối ưu chi phí, tối đa lợi nhuận).

* **Hàm mục tiêu:** $\min$ hoặc $\max Z = c^T x$
* **Hệ ràng buộc:** $Ax \le b$, $Ax \ge b$, hoặc $Ax = b$
* **Điều kiện dấu:** Bất kỳ ($x_j \ge 0$, $x_j \le 0$, hoặc $x_j$ tự do)

### 1.2. Dạng chuẩn tắc (Canonical Form)

* **Hàm mục tiêu:** $\min c^T x$
* **Hệ ràng buộc:** $Ax \le b$
* **Điều kiện dấu:** $x \ge 0$

### 1.3. Dạng chính tắc (Standard Form)

Dạng bắt buộc đối với hầu hết các thuật toán Đơn hình (Simplex).

* **Hàm mục tiêu:** $\min c^T x$
* **Hệ ràng buộc:** Tất cả đều là phương trình $Ax = b$ (bằng cách thêm biến phụ $s_i \ge 0$).
* **Điều kiện dấu:** $x \ge 0$

### 1.4. Quy tắc chuyển đổi bài toán (Tổng quát → Chuẩn tắc → Chính tắc)

Hệ thống tự động chuẩn hóa mọi bài toán trước khi đưa vào các lớp Solver theo các quy tắc đại số sau:

* **Hàm mục tiêu:** $\max c^T x \longrightarrow -\min -c^T x$
* **Ràng buộc $\ge$:** $a_i^T x \ge b_i \longrightarrow -a_i^T x \le -b_i$ (cho dạng chuẩn tắc) hoặc $a_i^T x - s_i = b_i$ với $s_i \ge 0$ (cho dạng chính tắc).
* **Biến tự do:** $x_j \text{ tự do} \longrightarrow x_j = x_j^+ - x_j^-$ với $(x_j^+, x_j^- \ge 0)$.
* **Biến âm:** $x_j \le 0 \longrightarrow y_j = -x_j$ với $(y_j \ge 0)$.

---

## II. PHÂN LOẠI TÍN HIỆU NGHIỆM

Quá trình giải có thể trả về 1 trong 4 trạng thái nghiệm sau:

1. **Duy nhất nghiệm:** Bài toán có một tập nghiệm tối ưu $x^*$ duy nhất và đạt giá trị tối ưu $z^*(x^*)$.
2. **Vô số nghiệm:** Bài toán tồn tại vô số tập nghiệm khả thi nhưng chỉ có một giá trị tối ưu $z^*$ duy nhất.
3. **Vô nghiệm:** Tập chấp nhận được rỗng. Tín hiệu: bài toán $\min$ trả về $z^* = +\infty$, bài toán $\max$ trả về $z^* = -\infty$.
4. **Không giới nội:** Miền chấp nhận được không bị chặn. Tín hiệu: bài toán $\min$ trả về $z^* = -\infty$, bài toán $\max$ trả về $z^* = +\infty$.

---

## III. CHI TIẾT CÁC PHƯƠNG PHÁP GIẢI (SOLVERS)

Hệ thống cung cấp 6 phương pháp giải thuần túy toán học và 1 phương pháp giải công nghiệp. Mọi phương pháp đều trả về các bước giải chi tiết (step-by-step logs).

### 3.1. Phương pháp Hình học (Geometric Method)

* **Module:** `app/solver/geometric_solver.py`
* **Điều kiện áp dụng:** Bài toán chỉ có đúng 2 biến chính ($x_1, x_2$).
* **Lý thuyết:** Vẽ toàn bộ các đường thẳng ràng buộc lên mặt phẳng tọa độ để tìm ra "Miền nghiệm khả thi" (Feasible Region).
* **Các cách tiếp cận trong hệ thống:**
    * **Cách 1 (Thế tọa độ điểm):** Tính toán giao điểm của các đường ràng buộc. Lọc ra các điểm thỏa mãn toàn bộ hệ (điểm khả thi). Thay tọa độ vào hàm mục tiêu $Z$ để tìm $\max$ hoặc $\min$.
    * **Cách 2 (Trượt hàm mục tiêu):** Vẽ đường thẳng đồng mức của hàm mục tiêu. Trượt dọc theo miền nghiệm về hướng Gradient (Max) hoặc ngược lại (Min). Điểm chạm cuối cùng là nghiệm tối ưu.

### 3.2. Phương pháp Đơn hình (Simplex Method) — $b > 0$

Bài toán QHTT, dạng chuẩn:
$(P) \longrightarrow (P')$

$$\begin{cases}
\min c^T x \\
Ax \le b \\
x \ge 0
\end{cases}
\iff
\begin{cases}
\min c_1x_1 + c_2x_2 + \dots + c_nx_n \\
a_{11}x_1 + a_{12}x_2 + \dots + a_{1n}x_n \le b_1 \\
a_{21}x_1 + a_{22}x_2 + \dots + a_{2n}x_n \le b_2 \\
\vdots \\
a_{n1}x_1 + a_{n2}x_2 + \dots + a_{nn}x_n \le b_n \\
x_1, \dots, x_n \ge 0
\end{cases}$$

**Bước 1:** Xây dựng từ vựng xuất phát
$z = c_1x_1 + c_2x_2 + \dots + c_nx_n \longrightarrow$ biến không cơ sở (**$G>0$**)
*(Cho **biến không cơ sở** $= 0 \Rightarrow$ **đọc giá trị biến cơ sở**)*

Biến cơ sở:
$w_1 = b_1 - a_{11}x_1 - a_{12}x_2 - \dots - a_{1n}x_n$
$w_2 = b_2 - a_{21}x_1 - a_{22}x_2 - \dots - a_{2n}x_n$
$\vdots$
$w_n = b_n - a_{n1}x_1 - a_{n2}x_2 - \dots - a_{nn}x_n$

**Bước 2:** Thực hiện chọn biến vào/ra:

* **Chọn biến vào cơ sở:** chọn biến (không cơ sở) có hệ số **$G$ âm nhất** ($x_j$) (cột ứng với $x_j$)
* **Chọn biến ra cơ sở:** Chỉ lưu ý cột $x_j$. Trên cột $x_j$, chỉ lấy $\simeq$ dòng mà hệ số trước đó **âm** ($<0$) (I).
Tính: $\min \left\{ \frac{b_i}{|a_{ij}|} \right\}_{i \in I} \longrightarrow$ ứng dòng $i \rightarrow$ biến ra $w_i$
$\Rightarrow$ **Vị trí xoay $a_{ij}$**

**Bước 3:** Tiến hành xoay từ vựng $\Rightarrow$ Từ vựng mới

**Bước 4:** Kiểm tra điều kiện dừng

* $\forall G: G \ge 0 \longrightarrow$ **dừng**
* $\Rightarrow$ **Từ vựng lớn nhất là từ vựng tối ưu $\Rightarrow$ đọc nghiệm và giá trị tối ưu của $(P') \Rightarrow$ trả lại nghiệm và giá trị tối ưu của $(P)$**

### 3.3. Phương pháp xoay Bland — $\exists b_i = 0$

**Phương pháp xoay Bland:**

* **Chọn biến vào:** trong số các biến không cơ sở có hệ số âm ($G < 0$)
**Chọn biến cơ sở nhỏ nhất** ($x_1, x_2, x_3, w_1, w_2$)
* **Chọn biến ra:** y như đơn hình tính $\frac{b_i}{a_{ij}}$ ($=0$)

### 3.4. Thuật toán 2 Pha (Two-Phase) — $\exists b_i < 0$

$(P) \longrightarrow (P')$ dạng chuẩn:

$$\begin{cases}
\min c^T x \\
Ax \le b \quad (\exists b_i < 0) \\
x \ge 0
\end{cases}$$

#### Pha 1

**1>.** Xây dựng bài toán bổ trợ $(\Delta)$

$$(\Delta)
\begin{cases}
\min x_0 \\
a_1^T x - x_0 \le b_1 \\
a_2^T x - x_0 \le b_2 \\
\vdots \\
a_m^T x - x_0 \le b_m \\
x \ge 0; x_0 \ge 0
\end{cases}$$

**2>.** Lập từ vựng xuất phát $(\Delta)$

$$\begin{aligned}
\xi &= \quad x_0 \\
\hline
w_1 &= b_1 - a_1^T x + x_0 \\
\leftarrow w_2 &= b_2 - a_2^T x + \mathbf{x_0} \\
&\vdots \\
w_m &= b_m - a_m^T x + x_0
\end{aligned}$$

**3>.** Biến vào: $x_0$
**Biến ra:** $w_i$ ứng với $b_i$ âm nhất $\Rightarrow$ xoay $\Rightarrow$ **từ vựng mới**
*(từ vựng chấp nhận được $b_i \ge 0$ hoặc $b_i = 0$)*

**4>.** Dùng xoay đơn hình hoặc xoay Bland:

* **4.1.** $\xi = \dots$
**ràng buộc của từ vựng tối ưu $(\Delta)$ ($RB_\Delta$)**
$\rightarrow$ chuyển sang pha 2.
* **4.2.** dạng $\ne 4.1.$
Bài toán vô nghiệm. (**tập chấp nhận được $= \emptyset$**)

#### Pha 2

**1>.** Lập từ vựng chấp nhận được của $(P')$ từ $(P')$ và $(\Delta)$

$$\begin{cases}
z' = \mathbf{\tilde{c}^T x} & \leftarrow \text{hàm mục tiêu } (P') \\
\hline
\mathbf{(RB_\Delta) \text{ khi cho } x_0 = 0} & \leftarrow \text{được lập từ } c^Tx \text{ và } RB_\Delta \text{ (khi cho } x_0 = 0)
\end{cases}$$

**2>.** Xoay đơn hình $\rightarrow$ Kết quả

### 3.5. Bài toán Đối ngẫu (Duality)

#### Bảng quy tắc chuyển đổi (P) → (D)

| Mục tiêu | $\min c^T x$ (primal) | $\max y^T b$ (dual problem) |
| --- | --- | --- |
| **Ràng buộc** | $a_i^T x = b_i, \quad i \in M_1$ | $y_i \text{ tự do}, \quad i \in M_1$ $\rightarrow$ Ràng buộc D |
|  | $a_i^T x \le b_i, \quad i \in M_2$ | $y_i \le 0, \quad i \in M_2$ |
|  | $a_i^T x \ge b_i, \quad i \in M_3$ | $y_i \ge 0, \quad i \in M_3$ |
|  | $x_j \ge 0, \quad j \in N_1$ | $y^T A_j \le c_j, \quad j \in N_1 \longrightarrow \text{cột thứ } J$ |
|  | $x_j \le 0, \quad j \in N_2$ | $y^T A_j \ge c_j, \quad j \in N_2 \rightarrow \text{Ràng buộc}$ |
|  | $x_j \text{ tự do}, \quad j \in N_3$ | $y^T A_j = c_j, \quad j \in N_3$ |

#### Ví dụ: $(P) \longrightarrow (D)$

| $(P)$ | $(D)$ |
| --- | --- |
| $\min x_1 + 2x_2 - 3x_3$ | $\max 5y_1 + 6y_2 - 2y_3 + 6y_4$ |
| $x_1 + x_2 = 5$ | $y_1 \text{ tự do}$ |
| $x_1 - x_2 + 2x_3 = 6$ | $y_2 \text{ tự do} \quad \rightarrow$ Ràng buộc D |
| $x_1 + x_2 - x_3 \le -2$ | $y_3 \le 0$ |
| $-3x_2 + 5x_3 \ge 6$ | $y_4 \ge 0$ |
| $x_1 \ge 0$ | $y_1 + y_2 + y_3 \le 1$ |
| $x_2 \le 0$ | $y_1 - y_2 + y_3 - 3y_4 \ge 2 \quad \rightarrow$ Ràng buộc |
| $x_3 \text{ tự do}$ | $2y_2 - y_3 + 5y_4 = -3$ |

#### Tính chất $(DD) \equiv (P)$

**Cách 1:** (trực tiếp) $(P) \longrightarrow (D) \longrightarrow (DD) \equiv (P)$

| $(P)$ | $(D)$ | $(DD) \equiv (P)$ |
| --- | --- | --- |
| $\min x_1 + 2x_2 - 3x_3$ | $-\min -5y_1 - 6y_2 + 2y_3 - 6y_4$ | $-\max x_1 + 2x_2 - 3x_3$ |
| $x_1 + x_2 = 5$ | $y_1 + y_2 + y_3 \le 1$ | $x_1 \le 0$ |
| $x_1 - x_2 + 2x_3 = 6$ | $y_1 - y_2 + y_3 - 3y_4 \ge 2$ | $x_2 \ge 0$ |
| $x_1 + x_2 - x_3 \le -2$ | $2y_2 - y_3 + 5y_4 = -3$ | $x_3 \text{ tự do}$ |
| $-3x_2 + 5x_3 \ge 6$ | $y_1 \text{ tự do}$ | $x_1 + x_2 = -5$ |
| $x_1 \ge 0$ | $y_2 \text{ tự do}$ | $x_1 - x_2 + 2x_3 = -6$ |
| $x_2 \le 0$ | $y_3 \le 0$ | $x_1 + x_2 - x_3 \ge 2$ |
| $x_3 \text{ tự do}$ | $y_4 \ge 0$ | $-3x_2 + 5x_3 \le -6$ |

*(Ghi chú bổ sung):*

$$\begin{cases}
\min -x_1 - 2x_2 + 3x_3 \\
-x_1 - x_2 = 5 \\
-x_1 + x_2 - 2x_3 = 6 \\
-x_1 - x_2 + x_3 \le -2 \\
3x_2 - 5x_3 \ge 6
\end{cases}
\quad
\begin{array}{|l}
x_1 \le 0 \implies x_1' = -x_1 \\
x_2 \ge 0 \implies x_2' = -x_2 \\
x_3 \text{ tự do} \implies x_3' = -x_3
\end{array}$$

### 3.6. Các định lý Đối ngẫu

#### a>. Định lý đối ngẫu yếu (Weak Duality)

$(P) \min \longrightarrow (D) \max$
Giả sử:

* $x$ là 1 điểm chấp nhận được của $(P)$
* $y$ là 1 điểm chấp nhận được của $(D)$

Khi đó, $y^T b \le c^T x$
**Hệ quả:** nếu $(P)$ không giới nội; tức là, $\min c^T x = -\infty \xrightarrow{\max} y^T b \le -\infty \Rightarrow (D)$ vô nghiệm.

#### b>. Định lý đối ngẫu mạnh (Strong Duality)

* Nếu $x^*$ là nghiệm của $(P)$ và $y^*$ là nghiệm của $(D)$ thì:

$$c^T x^* = y^{*T} b$$

* Nếu $x$ là điểm chấp nhận được của $(P)$ mà $c^T x = y^T b$ với $y$ là điểm chấp nhận được của $(D)$ thì $x^*$ là nghiệm của $(P)$, $y^*$ là nghiệm của $(D)$.

### 3.7. Thuật toán Đơn hình Đối ngẫu — $\exists b_i < 0$

$$(P) \rightarrow (P')
\begin{cases}
\min c^T x \\
Ax \le b \quad (\exists b_i < 0) \\
x \ge 0
\end{cases}$$

**Bước 1: Xây dựng từ vựng xuất phát**

$$\begin{aligned}
Z &= c_1x_1 + c_2x_2 + \dots + c_nx_n \\
\hline
w_1 &= b_1 + a_{11}x_1 + a_{12}x_2 + \dots + a_{1n}x_n \\
w_2 &= b_2 + a_{21}x_1 + a_{22}x_2 + \dots + a_{2n}x_n \\
&\vdots \\
w_n &= b_n + a_{n1}x_1 + a_{n2}x_2 + \dots + a_{nn}x_n
\end{aligned}$$

**Bước 2: Chọn biến vào/ra:**

**a>.** Chọn biến ra: $b_i$ âm nhất (dòng $i$)
**b>.** Chọn biến vào: Xét tỷ lệ $\min \left\{ \frac{G_J}{a_{iJ}} \right\}_{(G>0, a_{iJ} > 0)} \longrightarrow$ cột $(J_o)$

* **b1>.** $\exists J_o \Rightarrow$ xoay bình thường $\Rightarrow$ từ vựng ($b_i \ge 0$) $\Rightarrow$ **Đơn hình (gốc)**
* **b2>.** $\not\exists J_o \Rightarrow$ pha không áp dụng được $\Rightarrow$ xem mục 3.8.

### 3.8. Thuật toán 2 Pha (Đối ngẫu - Gốc)

$\hookrightarrow$ Xử lý trường hợp $b2>$ ở mục 3.7.

#### Pha 1

Lập bài toán bổ trợ:

$$\begin{cases}
\min |c_1|x_1 + |c_2|x_2 + \dots + |c_n|x_n \\
Ax \le b \\
x \ge 0
\end{cases}$$

Dùng thuật toán đơn hình đối ngẫu (Mục 3.7) $\rightarrow$ từ vựng tối ưu của $(P_{BT})$

#### Pha 2

Dùng hàm mục tiêu $(P): z = c^T x$ và ràng buộc của từ vựng cuối phần 1 $\Rightarrow$ từ vựng chấp nhận được của bài toán gốc.
Dùng đơn hình gốc $\Rightarrow \begin{cases} \text{nghiệm} \\ \text{giá trị tối ưu} \end{cases}$ bài toán gốc.
