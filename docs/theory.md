# LÝ THUYẾT QUY HOẠCH TUYẾN TÍNH (QHTT)

## I. Cấu trúc và Mô hình Toán học

**1. Bài toán QHTT dạng tổng quát (Dạng ma trận)**
Mô hình hóa từ một bài toán thực tế (ví dụ: bài toán khẩu phần ăn, thuê xe).
*   **Hàm mục tiêu:** $\min$ hoặc $\max \ z = c^T x$.
*   **Hệ ràng buộc chính:** Gồm các dạng $Ax \le b$, $Ax \ge b$, hoặc $Ax = b$.
*   **Điều kiện biến:** 
    *   $x_j \ge 0$ (biến không âm)
    *   $x_j \le 0$ (biến âm)
    *   $x_j$ tự do (không yêu cầu về dấu).

**2. Bài toán dạng chuẩn và chính tắc**
Để áp dụng thuật toán, cần chuyển bài toán tổng quát về dạng chuẩn hoặc chính tắc:
*   **Hàm mục tiêu:** Đổi về dạng đồng nhất, thông thường là $\min$ (nếu là $\max c^T x$, đổi thành $-\min -c^T x$).
*   **Hệ ràng buộc:** 
    *   Bất phương trình $Ax \le b \rightarrow$ cộng biến phụ $s_i \ge 0$: $Ax + s_i = b$.
    *   Bất phương trình $Ax \ge b \rightarrow$ trừ biến phụ $s_i \ge 0$: $Ax - s_i = b$.
    *   Phương trình $Ax = b \rightarrow$ giữ nguyên.
*   **Điều kiện biến:** Đưa tất cả biến về dạng $\ge 0$. Nếu $x_j \le 0$, đặt $y_j = -x_j \ge 0$; nếu $x_j$ tự do, tách cấu trúc thành $x_j = u_j - v_j$ với $u_j, v_j \ge 0$.

**3. Hệ Từ vựng (Input cho Phương pháp Đơn hình)**
Hệ phương trình biểu diễn các biến cơ sở (biến trong hệ) theo các biến không cơ sở (biến ngoài hệ).
*   **Hàm mục tiêu:** $z = \text{hằng số} + \sum (\text{hệ số} \times \text{biến không cơ sở})$.
*   **Các biến cơ sở ($w_i$ hoặc $x_{m+i}$):** $w_i = b_i - \sum a_{ij} x_j$
*   *Điều kiện xuất phát:* Tập hằng số $b_i \ge 0$ để từ vựng khả thi.

**4. Bài toán bổ trợ (Input cho Thuật toán 2 Pha)**
Áp dụng khi từ vựng ban đầu không khả thi ($b_i < 0$).
*   **Hàm mục tiêu bổ trợ:** $\min x_0$ hoặc $\min \sum x_j$ (tùy thuộc vào thiết lập pha 1).
*   **Hệ ràng buộc:** Thêm biến giả $x_0 \ge 0 \Rightarrow Ax - x_0 \le b$.
*   **Điều kiện:** Tất cả các biến $\ge 0$.

**5. Bài toán Đối ngẫu (Dual Problem)**
Được xây dựng song song từ bài toán gốc (Primal - P).
*   **Hàm mục tiêu:** Đảo ngược (Bài toán gốc $\min c^T x \rightarrow$ Đối ngẫu $\max y^T b$).
*   **Hệ ràng buộc & Điều kiện biến:** Tương tác chéo nhau phụ thuộc vào bảng quy tắc chuyển đổi đối ngẫu (ví dụ: biến đối ngẫu $y$ tương tác với $c^T$, ràng buộc $A^T y \le c$).

---

## II. Các Phương pháp Giải thuật

**1. Phương pháp hình học (Dành cho bài toán 2 biến)**
Biểu diễn tọa độ ràng buộc trên mặt phẳng oxy.
*   **Cách 1 (Tọa độ đỉnh):** Xác định các đỉnh của đa giác miền nghiệm và thay vào hàm mục tiêu để tìm min/max.
*   **Cách 2 (Trượt hàm mục tiêu):** Vẽ đường thẳng hàm mục tiêu $z$, "trượt" song song trên miền nghiệm để xác định điểm cắt tối ưu cuối cùng.
*   **Các trường hợp có thể xảy ra:** Nghiệm duy nhất, vô số nghiệm, vô nghiệm, hoặc bài toán không bị chặn (không giới hạn, $z^* \rightarrow \pm\infty$).

**2. Phương pháp Đơn hình (Simplex Method - Dantzig)**
Thuật toán biến đổi đại số ma trận lặp giải QHTT ở dạng chuẩn.
*   **Bước 1:** Lập từ vựng xuất phát (cho biến ngoài hệ = 0 để tìm giá trị biến cơ sở).
*   **Bước 2 (Chọn biến vào):** Nhìn hàm mục tiêu, chọn biến không cơ sở có hệ số âm mạnh nhất để đưa vào hệ (với bài toán min).
*   **Bước 3 (Chọn biến ra):** Dựa trên hệ số cột của biến vào, xét tỷ số $\theta = \frac{b_i}{-a_{ij}}$ (với $a_{ij} < 0$). Biến có tỷ số $\theta$ nhỏ nhất không âm sẽ làm biến ra.
*   **Bước 4:** Xoay đơn hình (Pivot) thế biến vào và biến ra. Giải lại hệ phương trình để lập từ vựng mới. Lặp lại cho đến khi từ vựng nằm ở trạng thái tối ưu (toán tử hàm mục tiêu đều $\ge 0$).
*   *Lưu ý:* Nếu xác định được biến vào nhưng không có biến ra hợp lệ, bài toán không bị chặn.

**3. Phương pháp xoay Bland**
Quy tắc bổ sung giải quyết triệt để tình trạng **bài toán bị xoay vòng (cycling)** khi hệ thống bị suy biến ($b_i = 0$ kéo dài).
*   **Quy tắc:** Khi có nhiều lựa chọn biến vào (nhiều hệ số âm) hoặc xét biến ra (các tỷ số bằng nhau), luôn **ưu tiên chọn biến có cấu trúc chỉ số danh pháp nhỏ nhất** (ví dụ: ưu tiên $x_1$ trước $x_2$, ưu tiên $w_1$ trước $w_2$).

**4. Thuật toán 2 Pha (Two-Phase Algorithm)**
Cách tiếp cận khi từ vựng xuất phát ban đầu vi phạm tính khả thi ($b_i < 0$).
*   **Pha 1:** Lập bài toán bổ trợ với biến giả $x_0 \ge 0$ và hàm mục tiêu $\min x_0$. Lặp đơn hình nguyên lý bình thường cho đến khi tìm được từ vựng khả thi mới với $x_0 = 0$.
*   **Pha 2:** Loại bỏ triệt để biến giả $x_0$. Đưa hàm mục tiêu ban đầu chèn ngược lại hệ từ vựng khả thi thu được. Tiếp tục xoay đơn hình nguyên thủy để tìm ra nghiệm tối ưu thật sự.

**5. Phương pháp Đơn hình Đối ngẫu (Dual Simplex Method)**
Thuật toán mang tính bước lùi so với đơn hình gốc, đi từ một từ vựng **tối ưu nhưng chưa khả thi** dần trở về khả thi:
*   **Bước 1 (Chọn biến ra xếp trước):** Định hướng dọn dẹp biến vi phạm, chọn phương trình có hệ số $b_i$ âm nhất làm biến ra.
*   **Bước 2 (Chọn biến vào xếp sau):** Đảm bảo duy trì trạng thái tối ưu, xét tỷ số giữa hệ số hàm mục tiêu và hệ số tương ứng trên dòng của biến ra để chọn hướng biến vào.
*   Nếu không thể xoay trực tiếp, có thể lập bài toán bổ trợ và giải pha 1 đối ngẫu với hàm mục tiêu $\min \sum x_j$.

**6. Giải bài toán qua Lý thuyết Đối ngẫu (Duality & Complementary Slackness)**
*   **Tính chất:** Một điểm tối ưu của đối ngẫu (D) cũng hoàn toàn là điểm tối ưu của bài toán gốc (P), thỏa mãn phương trình cực đại: $c^T x^* = y^T b^*$.
*   **Định lý độ lệch bù (Complementary Slackness):** Khi đã biết nghiệm của bài toán đối ngẫu $y^*$, ta dùng định lý này để tìm nghiệm gốc $x^*$ không cần phải xoay đơn hình vòng lặp. 
    *   Nếu ràng buộc kiểm tra của đối ngẫu lỏng (slack > 0) $\rightarrow$ biến nguyên thủy tương ứng cố định bằng không $x_j = 0$.
    *   Nếu biến đối ngẫu $y_i > 0 \rightarrow$ ràng buộc nguyên thủy tương ứng bị kẹp chặt (slack = 0).
    *   Sau khi loại bỏ các biến bằng 0 ra khỏi tầm ảnh hưởng, tiến hành giải hệ phương trình tuyến tính thông thường để tìm các vector $x^*$ còn lại.