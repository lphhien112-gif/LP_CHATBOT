# /tests/test_real_world.py
"""
Kiểm thử các bài toán Quy hoạch tuyến tính **thực tế** (sản xuất, khẩu phần,
đầu tư, vận tải, pha trộn) theo cách chặt chẽ nhất: với mỗi bài toán, lấy
nghiệm của **PuLP CBC làm chuẩn (oracle)** rồi đối chiếu từng bộ giải tự cài
đặt phải cho **cùng giá trị tối ưu z\\*** (so sánh z\\*, không so sánh nghiệm cụ
thể vì bài có thể có nhiều phương án tối ưu).

Cách này không "học thuộc" đáp số — đáp số do PuLP tự tính — nên kiểm chứng
được tính đúng đắn của solver trên bài toán bất kỳ.
"""
import pytest
from typing import Dict, Any, List

from app.solver.algorithms.pulp_cbc import solve_with_pulp_cbc
from app.solver.algorithms.simplex import solve_with_simple_dictionary
from app.solver.algorithms.simplex_bland import solve_with_simplex_bland
from app.solver.algorithms.auxiliary import solve_with_auxiliary_problem_simplex
from app.solver.algorithms.dual_simplex import solve_with_dual_simplex
from app.solver.algorithms.geometric import solve_with_geometric_method


# ═══════════════════════════════════════════════════════════════════════════════
# BỘ BÀI TOÁN THỰC TẾ (Format A)
# ═══════════════════════════════════════════════════════════════════════════════

def _p(objective, coeffs, names, constraints) -> Dict[str, Any]:
    return {
        "objective": objective,
        "coeffs": coeffs,
        "variables_names_for_title_only": names,
        "constraints": [
            {"name": f"c{i+1}", "lhs": lhs, "op": op, "rhs": rhs}
            for i, (lhs, op, rhs) in enumerate(constraints)
        ],
    }


# 1) Kế hoạch sản xuất nội thất (3 sản phẩm) — tối đa lợi nhuận, ràng buộc tài nguyên.
#    Bàn/ghế/tủ lãi 60/30/20; giới hạn gỗ, hoàn thiện, lắp ráp.
RW_FURNITURE = _p("maximize", [60, 30, 20], ["x1", "x2", "x3"], [
    ([8, 6, 1], "<=", 48),     # gỗ
    ([4, 2, 1.5], "<=", 20),   # hoàn thiện
    ([2, 1.5, 0.5], "<=", 8),  # lắp ráp
])

# 2) Pha chế sơn (Reddy Mikks cổ điển) — 2 biến, tối đa lợi nhuận.
RW_PAINT = _p("maximize", [5, 4], ["x1", "x2"], [
    ([6, 4], "<=", 24),
    ([1, 2], "<=", 6),
    ([-1, 1], "<=", 1),
    ([0, 1], "<=", 2),
])

# 3) Khẩu phần ăn (Diet) — 2 biến, tối thiểu chi phí, ràng buộc dinh dưỡng '>='.
#    Hệ số mục tiêu >= 0 và ràng buộc '>=' => dual-feasible.
RW_DIET = _p("minimize", [2, 3], ["x1", "x2"], [
    ([1, 2], ">=", 14),   # vitamin A
    ([3, 1], ">=", 18),   # vitamin C
])

# 4) Phân bổ đầu tư (Investment) — 3 biến, tối đa lợi nhuận kỳ vọng.
RW_INVEST = _p("maximize", [12, 10, 8], ["x1", "x2", "x3"], [
    ([1, 1, 1], "<=", 100),  # ngân sách
    ([1, 0, 0], "<=", 40),   # trần rủi ro kênh 1
    ([0, 1, 0], "<=", 50),   # trần kênh 2
])

# 5) Vận tải 2x2 (Transportation) — 4 biến, tối thiểu chi phí; cung '<=' và cầu '>='.
RW_TRANSPORT = _p("minimize", [8, 6, 10, 4], ["x11", "x12", "x21", "x22"], [
    ([1, 1, 0, 0], "<=", 20),  # cung kho 1
    ([0, 0, 1, 1], "<=", 30),  # cung kho 2
    ([1, 0, 1, 0], ">=", 25),  # cầu cửa hàng 1
    ([0, 1, 0, 1], ">=", 25),  # cầu cửa hàng 2
])

# 6) Pha trộn phân bón (Blending) — 2 biến, tối thiểu chi phí; tổng '==' và dinh dưỡng '>='.
RW_BLEND = _p("minimize", [0.4, 0.6], ["x1", "x2"], [
    ([1, 1], "==", 100),       # tổng khối lượng
    ([0.3, 0.1], ">=", 20),    # đạm
    ([0.2, 0.5], ">=", 25),    # lân
])

# Metadata: (id, data, nvars, geometric_ok, dual_feasible)
REAL_WORLD: List[tuple] = [
    ("furniture_3sp", RW_FURNITURE, 3, False, False),
    ("paint_reddymikks", RW_PAINT, 2, True, False),
    ("diet_min", RW_DIET, 2, True, True),
    ("investment_3kenh", RW_INVEST, 3, False, False),
    ("transport_2x2", RW_TRANSPORT, 4, False, False),
    ("blending_phanbon", RW_BLEND, 2, False, False),  # có '==' nên không test hình học
]

GENERAL_SOLVERS = {
    "simplex_dantzig": solve_with_simple_dictionary,
    "simplex_bland": solve_with_simplex_bland,
    "two_phase": solve_with_auxiliary_problem_simplex,
}


def _pulp_oracle(data: Dict[str, Any]) -> Dict[str, Any]:
    sol, _ = solve_with_pulp_cbc(data)
    assert sol is not None and sol["status"] == "Optimal", \
        "PuLP (oracle) phải giải được bài toán thực tế này."
    return sol


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Mọi bộ giải tổng quát phải khớp z* của PuLP (6 bài × 3 solver = 18 ca)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("solver_name", list(GENERAL_SOLVERS))
@pytest.mark.parametrize("pid,data,nvars,geo,dualf", REAL_WORLD,
                         ids=[r[0] for r in REAL_WORLD])
def test_realworld_matches_pulp(pid, data, nvars, geo, dualf, solver_name):
    oracle = _pulp_oracle(data)
    z_star = oracle["objective_value"]

    solution, logs = GENERAL_SOLVERS[solver_name](data)
    assert solution is not None, f"[{solver_name}/{pid}] trả về None"
    assert solution["status"] == "Optimal", \
        f"[{solver_name}/{pid}] mong đợi Optimal, nhận {solution['status']}"
    assert solution["objective_value"] == pytest.approx(z_star, abs=1e-3), \
        f"[{solver_name}/{pid}] z*={solution['objective_value']} != PuLP {z_star}"


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Phương pháp hình học khớp z* trên các bài 2 biến (miền bị chặn)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("pid,data,nvars,geo,dualf",
                         [r for r in REAL_WORLD if r[3]],
                         ids=[r[0] for r in REAL_WORLD if r[3]])
def test_realworld_geometric(pid, data, nvars, geo, dualf):
    z_star = _pulp_oracle(data)["objective_value"]
    solution, logs = solve_with_geometric_method(data)
    assert solution is not None and solution["status"] == "Optimal", \
        f"[geometric/{pid}] không cho Optimal"
    assert solution["objective_value"] == pytest.approx(z_star, abs=1e-3), \
        f"[geometric/{pid}] z*={solution['objective_value']} != PuLP {z_star}"


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Đơn hình đối ngẫu khớp z* trên bài min '>=' dual-feasible
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("pid,data,nvars,geo,dualf",
                         [r for r in REAL_WORLD if r[4]],
                         ids=[r[0] for r in REAL_WORLD if r[4]])
def test_realworld_dual_simplex(pid, data, nvars, geo, dualf):
    z_star = _pulp_oracle(data)["objective_value"]
    solution, logs = solve_with_dual_simplex(data)
    assert solution is not None and solution["status"] == "Optimal", \
        f"[dual_simplex/{pid}] không cho Optimal"
    assert solution["objective_value"] == pytest.approx(z_star, abs=1e-3), \
        f"[dual_simplex/{pid}] z*={solution['objective_value']} != PuLP {z_star}"
