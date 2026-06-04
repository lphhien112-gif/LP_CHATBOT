# /tests/test_random_lp.py
"""
Kiểm chứng diện rộng bằng **100 bài toán LP sinh ngẫu nhiên có kiểm soát**
(property-based testing). Mỗi bài dùng một seed cố định nên hoàn toàn tái lập.

Hai họ bài toán (đều bảo đảm khả thi & giới nội nên luôn có nghiệm tối ưu):
  - Chẵn  -> "product-mix": maximize, mọi ràng buộc '<=' (hệ số dương)  => luôn bị chặn.
  - Lẻ    -> "diet":        minimize, mọi ràng buộc '>=' (hệ số dương)  => bị chặn dưới.

Với mỗi bài, **PuLP CBC là chuẩn (oracle)**; ba bộ giải tự cài đặt (đơn hình
Dantzig, Bland, hai pha) phải cho **cùng giá trị tối ưu z\\*** (so sánh z\\*,
không so sánh nghiệm vì có thể có nhiều phương án tối ưu).
"""
import random
import pytest

from app.solver.algorithms.pulp_cbc import solve_with_pulp_cbc
from app.solver.algorithms.simplex import solve_with_simple_dictionary
from app.solver.algorithms.simplex_bland import solve_with_simplex_bland
from app.solver.algorithms.auxiliary import solve_with_auxiliary_problem_simplex

N_PROBLEMS = 100

GENERAL_SOLVERS = {
    "simplex_dantzig": solve_with_simple_dictionary,
    "simplex_bland": solve_with_simplex_bland,
    "two_phase": solve_with_auxiliary_problem_simplex,
}


def make_problem(seed: int) -> dict:
    """Sinh một bài toán LP khả thi & giới nội từ seed (tái lập được)."""
    rng = random.Random(1000 + seed)
    n = rng.choice([2, 3, 4])     # số biến
    m = rng.choice([2, 3, 4])     # số ràng buộc
    names = [f"x{j+1}" for j in range(n)]
    coeffs = [rng.randint(1, 9) for _ in range(n)]
    if seed % 2 == 0:  # product-mix: max, '<='
        objective, op = "maximize", "<="
        rhs_lo, rhs_hi = 10, 40
    else:              # diet: min, '>='
        objective, op = "minimize", ">="
        rhs_lo, rhs_hi = 5, 25
    constraints = [
        {"name": f"c{k+1}",
         "lhs": [rng.randint(1, 9) for _ in range(n)],
         "op": op,
         "rhs": rng.randint(rhs_lo, rhs_hi)}
        for k in range(m)
    ]
    return {"objective": objective, "coeffs": coeffs,
            "variables_names_for_title_only": names, "constraints": constraints}


@pytest.mark.parametrize("seed", range(N_PROBLEMS))
def test_random_lp_matches_pulp(seed):
    """Mỗi bài ngẫu nhiên: 3 bộ giải phải khớp z* của PuLP CBC."""
    data = make_problem(seed)

    oracle, _ = solve_with_pulp_cbc(data)
    assert oracle is not None and oracle["status"] == "Optimal", \
        f"[seed={seed}] PuLP (oracle) phải cho Optimal"
    z_star = oracle["objective_value"]

    for name, fn in GENERAL_SOLVERS.items():
        solution, _ = fn(data, 200)
        assert solution is not None, f"[seed={seed}/{name}] trả về None"
        assert solution["status"] == "Optimal", \
            f"[seed={seed}/{name}] mong đợi Optimal, nhận {solution['status']}"
        assert solution["objective_value"] == pytest.approx(z_star, abs=1e-3), \
            f"[seed={seed}/{name}] z*={solution['objective_value']} != PuLP {z_star}"
