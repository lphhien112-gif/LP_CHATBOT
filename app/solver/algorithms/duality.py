# /app/solver/algorithms/duality.py
"""
Xây dựng bài toán Đối ngẫu (theory.md §3.5) + Độ lệch bù (§3.6).

Module này cung cấp:
  1. build_dual_problem() — Chuyển (P) → (D) theo bảng quy tắc
  2. complementary_slackness() — Kiểm tra/áp dụng điều kiện bù yếu
"""
import logging
from typing import Dict, List, Any, Tuple, Optional
import copy

logger = logging.getLogger(__name__)


def build_dual_problem(
    problem_data: Dict[str, Any]
) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """
    Chuyển bài toán gốc (P) sang bài toán Đối ngẫu (D) theo theory.md §3.5.

    Quy tắc chuyển đổi (P) min → (D) max:
        min c^T x  →  max y^T b
        
        Ràng buộc P        → Biến đối ngẫu y
          a_i^T x = b_i      → y_i tự do
          a_i^T x <= b_i     → y_i <= 0
          a_i^T x >= b_i     → y_i >= 0
        
        Biến x              → Ràng buộc D  
          x_j >= 0           → y^T A_j <= c_j
          x_j <= 0           → y^T A_j >= c_j
          x_j tự do          → y^T A_j = c_j
    
    Input format (Định dạng A):
        {
            "objective": "min" | "max",
            "coeffs": [c1, c2, ...],
            "variables_names_for_title_only": ["x1", "x2", ...],
            "constraints": [
                {"name": "...", "lhs": [a1, a2, ...], "op": "<="|">="|"==", "rhs": b},
                ...
            ]
        }
    
    Returns: (dual_problem_data, step_by_step_md)
    """
    logs: List[str] = []
    step_md: List[str] = []
    
    if not problem_data:
        logs.append("ERROR: Empty problem data.")
        return None, logs

    obj_type = problem_data.get("objective", "min").lower()
    coeffs = problem_data.get("coeffs", [])
    var_names = problem_data.get("variables_names_for_title_only", [])
    constraints = problem_data.get("constraints", [])
    n_vars = len(coeffs)
    n_constrs = len(constraints)

    # Nếu gốc là max → chuyển thành min trước, rồi tạo đối ngẫu max
    # Hoặc xử lý trực tiếp: min → max, max → min
    is_primal_min = obj_type in ["min", "minimize"]

    # Dual sẽ là max nếu primal là min, và ngược lại
    dual_obj_type = "max" if is_primal_min else "min"

    # Biến đối ngẫu: y_1, ..., y_m (m = số ràng buộc)
    dual_var_names = [f"y{i+1}" for i in range(n_constrs)]

    # Hệ số hàm mục tiêu đối ngẫu = b vector
    dual_coeffs = [constr.get("rhs", 0.0) for constr in constraints]

    # Ràng buộc đối ngẫu: cột j → y^T A_j op c_j
    dual_constraints: List[Dict[str, Any]] = []
    
    for j in range(n_vars):
        # Cột j của ma trận A
        col_j = []
        for constr in constraints:
            lhs = constr.get("lhs", [])
            col_j.append(lhs[j] if j < len(lhs) else 0.0)

        # Xác định op cho ràng buộc đối ngẫu dựa trên dấu biến x_j
        # Mặc định giả sử x_j >= 0 → dual constraint <= (cho min primal)
        if is_primal_min:
            dual_op = "<="  # x_j >= 0 → y^T A_j <= c_j
        else:
            dual_op = ">="  # x_j >= 0 → y^T A_j >= c_j

        dual_constraints.append({
            "name": f"D_c{j+1}",
            "lhs": col_j,
            "op": dual_op,
            "rhs": coeffs[j]
        })

    # Dấu biến đối ngẫu y_i dựa trên loại ràng buộc gốc
    dual_var_signs: List[str] = []
    for constr in constraints:
        op = constr.get("op", "<=")
        if op in ["==", "="]:
            dual_var_signs.append("free")
        elif op in ["<=", "≤"]:
            if is_primal_min:
                dual_var_signs.append("<= 0")
            else:
                dual_var_signs.append(">= 0")
        elif op in [">=", "≥"]:
            if is_primal_min:
                dual_var_signs.append(">= 0")
            else:
                dual_var_signs.append("<= 0")

    dual_problem = {
        "objective": dual_obj_type,
        "coeffs": dual_coeffs,
        "variables_names_for_title_only": dual_var_names,
        "constraints": dual_constraints,
        "variable_signs": dual_var_signs  # Metadata: dấu biến đối ngẫu
    }

    # Tạo step-by-step markdown
    # Header
    step_md.append("**Xây dựng bài toán Đối ngẫu (D):**\n")

    # Bảng chuyển đổi
    step_md.append("| Gốc (P) | Đối ngẫu (D) |")
    step_md.append("| --- | --- |")

    primal_obj_str = f"$\\{'min' if is_primal_min else 'max'}\\ " + " + ".join(
        [f"{c:g}{var_names[i] if i < len(var_names) else f'x_{i+1}'}" for i, c in enumerate(coeffs)]
    ) + "$"
    dual_obj_str = f"${dual_obj_type}\\ " + " + ".join(
        [f"{c:g}{dual_var_names[i]}" for i, c in enumerate(dual_coeffs)]
    ) + "$"
    step_md.append(f"| {primal_obj_str} | {dual_obj_str} |")

    for i, constr in enumerate(constraints):
        op = constr.get("op", "<=")
        sign = dual_var_signs[i]
        step_md.append(f"| RB{i+1}: ${op}$ ${constr.get('rhs',0):g}$ | ${dual_var_names[i]}\\ {sign}$ |")

    for j in range(n_vars):
        d_constr = dual_constraints[j]
        var_label = var_names[j] if j < len(var_names) else f"x_{j+1}"
        lhs_str = " + ".join([f"{a:g}{dual_var_names[k]}" for k, a in enumerate(d_constr['lhs'])])
        step_md.append(f"| ${var_label} \\ge 0$ | ${lhs_str} {d_constr['op']} {d_constr['rhs']:g}$ |")

    step_md.append("")

    dual_problem["step_by_step_md"] = step_md
    return dual_problem, step_md


def complementary_slackness(
    primal_data: Dict[str, Any],
    dual_solution: Dict[str, float],
) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """
    Áp dụng định lý Độ lệch bù (theory.md §3.6) để tìm nghiệm gốc
    từ nghiệm đối ngẫu đã biết.

    Quy tắc:
      - y_i > 0 → ràng buộc (i) của (P) phải chặt (đẳng thức)
      - y_i = 0 → ràng buộc (i) của (P) có thể lỏng
      - Ràng buộc (j) của (D) chặt → x_j có thể > 0
      - Ràng buộc (j) của (D) lỏng → x_j = 0

    Args:
        primal_data: Bài toán gốc (P)
        dual_solution: Nghiệm đối ngẫu y* = {"y1": val, "y2": val, ...}

    Returns: (primal_solution, step_by_step_md)
    """
    step_md: List[str] = []
    step_md.append("**Áp dụng Độ lệch bù (Complementary Slackness):**\n")

    coeffs = primal_data.get("coeffs", [])
    var_names = primal_data.get("variables_names_for_title_only", [])
    constraints = primal_data.get("constraints", [])
    n_vars = len(coeffs)

    y_values = list(dual_solution.values())

    # Bước 1: Xét y* → tìm ràng buộc chặt của (P)
    step_md.append("**Bước 1:** Xét $y^*$ → ràng buộc chặt của (P):\n")
    tight_constraints = []  # Chỉ số ràng buộc chặt
    for i, constr in enumerate(constraints):
        y_val = y_values[i] if i < len(y_values) else 0.0
        if abs(y_val) > 1e-9:
            tight_constraints.append(i)
            step_md.append(f"* $y_{{{i+1}}} = {y_val:g} > 0 \\Rightarrow$ RB ({i+1}) chặt\n")
        else:
            step_md.append(f"* $y_{{{i+1}}} = 0 \\Rightarrow$ không ép thêm\n")

    # Bước 2: Lập hệ phương trình từ ràng buộc chặt
    step_md.append("\n**Bước 2:** Giải hệ từ ràng buộc chặt:\n")

    # Xây dựng hệ Ax = b từ ràng buộc chặt
    import numpy as np
    A_tight = []
    b_tight = []
    for idx in tight_constraints:
        constr = constraints[idx]
        A_tight.append(constr.get("lhs", [])[:n_vars])
        b_tight.append(constr.get("rhs", 0.0))

    result = {"status": "Unknown", "variables": {}, "objective_value": None}

    if len(A_tight) >= n_vars:
        try:
            A_mat = np.array(A_tight[:n_vars], dtype=float)
            b_vec = np.array(b_tight[:n_vars], dtype=float)
            x_sol = np.linalg.solve(A_mat, b_vec)

            for j in range(n_vars):
                vn = var_names[j] if j < len(var_names) else f"x{j+1}"
                result["variables"][vn] = float(x_sol[j])
                step_md.append(f"$\\Rightarrow {vn} = {x_sol[j]:g}$\n")

            obj_val = sum(coeffs[j] * x_sol[j] for j in range(n_vars))
            result["objective_value"] = obj_val
            result["status"] = "Optimal"
            step_md.append(f"\nGTTƯ: $z = {obj_val:g}$\n")

        except np.linalg.LinAlgError:
            step_md.append("Hệ phương trình suy biến. Không giải được trực tiếp.\n")
            result["status"] = "Degenerate"
    else:
        step_md.append(f"Chưa đủ ràng buộc chặt ({len(A_tight)} < {n_vars}). Cần thêm thông tin.\n")
        result["status"] = "Insufficient"

    result["step_by_step_md"] = step_md
    return result, step_md
