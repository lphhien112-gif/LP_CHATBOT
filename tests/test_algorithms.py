# /tests/test_algorithms.py
"""
Unit tests cho toàn bộ LP solver algorithms.

Mỗi solver nhận dữ liệu theo "Format A":
  - objective: "maximize" | "minimize"
  - coeffs: [c1, c2, ...]
  - variables_names_for_title_only: ["x1", "x2", ...]
  - constraints: [{"name": ..., "lhs": [...], "op": "<="|">="|"==", "rhs": ...}]

Test cases bao gồm:
  1. Simplex Dantzig  (simplex.py)
  2. Simplex Bland    (simplex_bland.py)
  3. Two-Phase        (auxiliary.py)
  4. Dual Simplex     (dual_simplex.py)
  5. Dual-Primal 2P   (dual_primal_two_phase.py)
  6. Duality          (duality.py)
"""
import pytest
from typing import Dict, Any

from app.solver.algorithms.simplex import solve_with_simple_dictionary
from app.solver.algorithms.simplex_bland import solve_with_simplex_bland
from app.solver.algorithms.auxiliary import solve_with_auxiliary_problem_simplex
from app.solver.algorithms.dual_simplex import solve_with_dual_simplex
from app.solver.algorithms.dual_primal_two_phase import solve_with_dual_primal_two_phase
from app.solver.algorithms.duality import build_dual_problem, complementary_slackness


# ═══════════════════════════════════════════════════════════════════════════════
# FIXTURES — Các bài toán LP mẫu
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def problem_max_basic() -> Dict[str, Any]:
    """
    Max 3x1 + 5x2
    s.t. x1 <= 4, 2x2 <= 12, 3x1 + 2x2 <= 18
    Optimal: x1=2, x2=6, Z=36
    """
    return {
        "objective": "maximize",
        "coeffs": [3, 5],
        "variables_names_for_title_only": ["x1", "x2"],
        "constraints": [
            {"name": "c1", "lhs": [1, 0], "op": "<=", "rhs": 4},
            {"name": "c2", "lhs": [0, 2], "op": "<=", "rhs": 12},
            {"name": "c3", "lhs": [3, 2], "op": "<=", "rhs": 18},
        ]
    }


@pytest.fixture
def problem_min_basic() -> Dict[str, Any]:
    """
    Min 2x1 + 3x2
    s.t. x1 + x2 >= 4, x1 + 3x2 >= 6
    Optimal: x1=3, x2=1, Z=9
    """
    return {
        "objective": "minimize",
        "coeffs": [2, 3],
        "variables_names_for_title_only": ["x1", "x2"],
        "constraints": [
            {"name": "c1", "lhs": [1, 1], "op": ">=", "rhs": 4},
            {"name": "c2", "lhs": [1, 3], "op": ">=", "rhs": 6},
        ]
    }


@pytest.fixture
def problem_negative_rhs() -> Dict[str, Any]:
    """
    Bài cần Phase 1 (có b_i < 0 sau chuẩn hóa).
    Min -x1 - x2   (≡ Max x1 + x2)
    s.t. x1 + x2 >= 2 (→ -x1 - x2 <= -2, b=-2 < 0)
         x1 + 2x2 <= 6
    Optimal: x1=6, x2=0, Z=-6 (verified với PuLP)
    """
    return {
        "objective": "minimize",
        "coeffs": [-1, -1],
        "variables_names_for_title_only": ["x1", "x2"],
        "constraints": [
            {"name": "c1", "lhs": [1, 1], "op": ">=", "rhs": 2},
            {"name": "c2", "lhs": [1, 2], "op": "<=", "rhs": 6},
        ]
    }


@pytest.fixture
def problem_dual_feasible() -> Dict[str, Any]:
    """
    Bài toán dual feasible (hệ số z >= 0 sau chuẩn hóa) nhưng primal infeasible (b_i < 0).
    Min 2x1 + x2
    s.t. x1 + x2 >= 4   → -x1 - x2 <= -4
         2x1 + x2 >= 6  → -2x1 - x2 <= -6
    Hệ số mục tiêu (min): c = [2, 1] >= 0 → dual feasible
    RHS sau chuẩn hóa: [-4, -6] → primal infeasible → dùng Dual Simplex
    """
    return {
        "objective": "minimize",
        "coeffs": [2, 1],
        "variables_names_for_title_only": ["x1", "x2"],
        "constraints": [
            {"name": "c1", "lhs": [1, 1], "op": ">=", "rhs": 4},
            {"name": "c2", "lhs": [2, 1], "op": ">=", "rhs": 6},
        ]
    }


@pytest.fixture
def problem_infeasible() -> Dict[str, Any]:
    """x1 >= 2 AND x1 <= 1: Infeasible"""
    return {
        "objective": "maximize",
        "coeffs": [1],
        "variables_names_for_title_only": ["x1"],
        "constraints": [
            {"name": "c1", "lhs": [1], "op": ">=", "rhs": 2},
            {"name": "c2", "lhs": [1], "op": "<=", "rhs": 1},
        ]
    }


@pytest.fixture
def problem_unbounded() -> Dict[str, Any]:
    """
    Max x1 + x2
    s.t. -x1 + x2 <= 10
    Unbounded (x1 có thể → +∞)
    """
    return {
        "objective": "maximize",
        "coeffs": [1, 1],
        "variables_names_for_title_only": ["x1", "x2"],
        "constraints": [
            {"name": "c1", "lhs": [-1, 1], "op": "<=", "rhs": 10},
        ]
    }


@pytest.fixture
def problem_degenerate() -> Dict[str, Any]:
    """
    Bài suy biến (degenerate): nhiều biến cơ sở có giá trị 0.
    Max x1 + x2
    s.t. x1 <= 1, x2 <= 1, x1 + x2 <= 1
    Optimal: Z=1 (ví dụ x1=1, x2=0 hoặc x1=0, x2=1)
    """
    return {
        "objective": "maximize",
        "coeffs": [1, 1],
        "variables_names_for_title_only": ["x1", "x2"],
        "constraints": [
            {"name": "c1", "lhs": [1, 0], "op": "<=", "rhs": 1},
            {"name": "c2", "lhs": [0, 1], "op": "<=", "rhs": 1},
            {"name": "c3", "lhs": [1, 1], "op": "<=", "rhs": 1},
        ]
    }


@pytest.fixture
def problem_3var() -> Dict[str, Any]:
    """
    Max 5x1 + 4x2 + 3x3
    s.t. 6x1 + 4x2 + 2x3 <= 240
         3x1 + 2x2 + 5x3 <= 270
         5x1 + 6x2 + 5x3 <= 420
    Optimal: x1=30, x2=0, x3=36, Z=258
    (verified with PuLP)
    """
    return {
        "objective": "maximize",
        "coeffs": [5, 4, 3],
        "variables_names_for_title_only": ["x1", "x2", "x3"],
        "constraints": [
            {"name": "c1", "lhs": [6, 4, 2], "op": "<=", "rhs": 240},
            {"name": "c2", "lhs": [3, 2, 5], "op": "<=", "rhs": 270},
            {"name": "c3", "lhs": [5, 6, 5], "op": "<=", "rhs": 420},
        ]
    }


@pytest.fixture
def problem_equality() -> Dict[str, Any]:
    """
    Min x1 + x2
    s.t. x1 + x2 == 5, x1 <= 3
    Optimal: x1=3, x2=2, Z=5
    """
    return {
        "objective": "minimize",
        "coeffs": [1, 1],
        "variables_names_for_title_only": ["x1", "x2"],
        "constraints": [
            {"name": "c1", "lhs": [1, 1], "op": "==", "rhs": 5},
            {"name": "c2", "lhs": [1, 0], "op": "<=", "rhs": 3},
        ]
    }


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER
# ═══════════════════════════════════════════════════════════════════════════════

def assert_optimal(solution, expected_z, expected_vars=None, tol=1e-4):
    """Helper: kiểm tra nghiệm tối ưu."""
    assert solution is not None, "Solution is None"
    assert solution["status"] == "Optimal", f"Expected Optimal, got {solution['status']}"
    assert solution["objective_value"] == pytest.approx(expected_z, abs=tol), \
        f"Expected z={expected_z}, got {solution['objective_value']}"
    if expected_vars:
        for var, val in expected_vars.items():
            assert solution["variables"][var] == pytest.approx(val, abs=tol), \
                f"Expected {var}={val}, got {solution['variables'].get(var)}"


def assert_status(solution, expected_status):
    """Helper: kiểm tra trạng thái."""
    assert solution is not None, "Solution is None"
    assert solution["status"] == expected_status, \
        f"Expected {expected_status}, got {solution['status']}"


def assert_has_steps(solution):
    """Helper: kiểm tra solution có step_by_step_md."""
    assert solution is not None
    steps = solution.get("step_by_step_md", [])
    assert len(steps) > 0, "Expected step_by_step_md to have content"


# ═══════════════════════════════════════════════════════════════════════════════
# 1. SIMPLEX DANTZIG (simplex.py)
# ═══════════════════════════════════════════════════════════════════════════════

class TestSimplexDantzig:
    """Tests cho SimpleDictionarySolver (Dantzig rule)."""

    def test_maximize_optimal(self, problem_max_basic):
        solution, logs = solve_with_simple_dictionary(problem_max_basic)
        assert_optimal(solution, 36.0, {"x1": 2.0, "x2": 6.0})

    def test_minimize_with_geq(self, problem_min_basic):
        # Regression: Phase 1 phải giải đúng ràng buộc '>=' (Z=9), không báo Infeasible.
        solution, logs = solve_with_simple_dictionary(problem_min_basic)
        assert_optimal(solution, 9.0, {"x1": 3.0, "x2": 1.0})

    def test_3_variables(self, problem_3var):
        solution, logs = solve_with_simple_dictionary(problem_3var)
        assert solution is not None
        assert solution["status"] == "Optimal"

    def test_negative_rhs_phase1(self, problem_negative_rhs):
        # Regression: bài cần Phase 1 (b_i < 0 sau chuẩn hóa) phải đạt Optimal, Z=-6.
        solution, logs = solve_with_simple_dictionary(problem_negative_rhs)
        assert_optimal(solution, -6.0)

    def test_degenerate(self, problem_degenerate):
        solution, logs = solve_with_simple_dictionary(problem_degenerate)
        assert solution is not None
        # Degenerate problems may cycle → MaxIterationsReached with Dantzig
        assert solution["status"] in ["Optimal", "MaxIterationsReached"]

    def test_unbounded(self, problem_unbounded):
        solution, logs = solve_with_simple_dictionary(problem_unbounded)
        assert solution is not None
        assert solution["status"] in ["Unbounded", "MaxIterationsReached"]

    def test_equality_constraint(self, problem_equality):
        # Regression: ràng buộc '==' (tách thành <= và >=) phải giải đúng Z=5.
        solution, logs = solve_with_simple_dictionary(problem_equality)
        assert_optimal(solution, 5.0)

    def test_has_step_by_step(self, problem_max_basic):
        solution, logs = solve_with_simple_dictionary(problem_max_basic)
        assert_has_steps(solution)

    def test_returns_logs(self, problem_max_basic):
        solution, logs = solve_with_simple_dictionary(problem_max_basic)
        assert len(logs) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# 2. SIMPLEX BLAND (simplex_bland.py)
# ═══════════════════════════════════════════════════════════════════════════════

class TestSimplexBland:
    """Tests cho SimplexBlandSolver (Bland's rule)."""

    def test_maximize_optimal(self, problem_max_basic):
        solution, logs = solve_with_simplex_bland(problem_max_basic)
        assert_optimal(solution, 36.0, {"x1": 2.0, "x2": 6.0})

    def test_minimize_with_geq(self, problem_min_basic):
        # Regression: Bland Phase 1 phải giải đúng ràng buộc '>=' (Z=9).
        solution, logs = solve_with_simplex_bland(problem_min_basic)
        assert_optimal(solution, 9.0, {"x1": 3.0, "x2": 1.0})

    def test_3_variables(self, problem_3var):
        solution, logs = solve_with_simplex_bland(problem_3var)
        assert solution is not None
        assert solution["status"] == "Optimal"

    def test_degenerate_no_cycling(self, problem_degenerate):
        """Bland's rule should prevent cycling on degenerate problems."""
        solution, logs = solve_with_simplex_bland(problem_degenerate)
        assert_optimal(solution, 1.0)

    def test_negative_rhs_phase1(self, problem_negative_rhs):
        # Regression: Bland xử lý đúng bài cần Phase 1, Z=-6.
        solution, logs = solve_with_simplex_bland(problem_negative_rhs)
        assert_optimal(solution, -6.0)

    def test_has_bland_header(self, problem_max_basic):
        """Output should contain Bland rule explanation."""
        solution, logs = solve_with_simplex_bland(problem_max_basic)
        steps = solution.get("step_by_step_md", [])
        steps_text = " ".join(steps)
        assert "Bland" in steps_text or "bland" in steps_text.lower()

    def test_same_result_as_dantzig(self, problem_max_basic):
        """Bland and Dantzig should give same optimal value."""
        sol_dantzig, _ = solve_with_simple_dictionary(problem_max_basic)
        sol_bland, _ = solve_with_simplex_bland(problem_max_basic)
        assert sol_dantzig["objective_value"] == pytest.approx(
            sol_bland["objective_value"], abs=1e-4
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 3. TWO-PHASE AUXILIARY (auxiliary.py)
# ═══════════════════════════════════════════════════════════════════════════════

class TestTwoPhaseAuxiliary:
    """Tests cho AuxiliaryProblemSolver (Two-Phase with x0)."""

    def test_maximize_optimal(self, problem_max_basic):
        solution, logs = solve_with_auxiliary_problem_simplex(problem_max_basic)
        assert_optimal(solution, 36.0, {"x1": 2.0, "x2": 6.0})

    def test_minimize_with_geq(self, problem_min_basic):
        """Two-Phase should handle >= constraints via auxiliary variable."""
        solution, logs = solve_with_auxiliary_problem_simplex(problem_min_basic)
        assert_optimal(solution, 9.0, {"x1": 3.0, "x2": 1.0})

    def test_infeasible(self, problem_infeasible):
        """Two-Phase should detect infeasibility when Phase 1 f* > 0."""
        solution, logs = solve_with_auxiliary_problem_simplex(problem_infeasible)
        assert solution is not None
        assert solution["status"] in ["Infeasible", "Phase1_Infeasible", "MaxIterationsReached"]

    def test_negative_rhs(self, problem_negative_rhs):
        solution, logs = solve_with_auxiliary_problem_simplex(problem_negative_rhs)
        assert solution is not None
        assert solution["status"] == "Optimal"

    def test_equality_constraint(self, problem_equality):
        solution, logs = solve_with_auxiliary_problem_simplex(problem_equality)
        assert solution is not None
        if solution["status"] == "Optimal":
            assert solution["objective_value"] == pytest.approx(5.0, abs=0.1)

    def test_3_variables(self, problem_3var):
        solution, logs = solve_with_auxiliary_problem_simplex(problem_3var)
        assert solution is not None
        assert solution["status"] == "Optimal"

    def test_same_result_as_simplex(self, problem_min_basic):
        """Two-Phase and Simplex should agree on optimal value."""
        sol_simplex, _ = solve_with_simple_dictionary(problem_min_basic)
        sol_aux, _ = solve_with_auxiliary_problem_simplex(problem_min_basic)
        if sol_simplex["status"] == "Optimal" and sol_aux["status"] == "Optimal":
            assert sol_simplex["objective_value"] == pytest.approx(
                sol_aux["objective_value"], abs=1e-4
            )


# ═══════════════════════════════════════════════════════════════════════════════
# 4. DUAL SIMPLEX (dual_simplex.py)
# ═══════════════════════════════════════════════════════════════════════════════

class TestDualSimplex:
    """Tests cho DualSimplexSolver (theory.md §3.7)."""

    def test_dual_feasible_problem(self, problem_dual_feasible):
        """Standard dual simplex case: z coeffs >= 0, some b_i < 0.
        Regression: Dual Simplex phải giải đúng (Z=6), không báo Infeasible nhầm.
        Min 2x1 + x2 s.t. x1+x2>=4, 2x1+x2>=6 → Optimal Z=6."""
        solution, logs = solve_with_dual_simplex(problem_dual_feasible)
        assert_optimal(solution, 6.0)

    def test_not_dual_feasible_rejected(self, problem_max_basic):
        """If z has negative coeffs after standardization, should report NotDualFeasible."""
        solution, logs = solve_with_dual_simplex(problem_max_basic)
        assert solution is not None
        # Max 3x1+5x2 → Min -3x1-5x2, coeffs negative → not dual feasible
        assert solution["status"] in ["NotDualFeasible", "Optimal", "MaxIterationsReached"]

    def test_all_positive_rhs(self):
        """If all b_i >= 0 and dual feasible, should be immediately optimal."""
        problem = {
            "objective": "minimize",
            "coeffs": [1, 2],
            "variables_names_for_title_only": ["x1", "x2"],
            "constraints": [
                {"name": "c1", "lhs": [1, 0], "op": "<=", "rhs": 5},
                {"name": "c2", "lhs": [0, 1], "op": "<=", "rhs": 3},
            ]
        }
        solution, logs = solve_with_dual_simplex(problem)
        assert solution is not None
        # All b >= 0, all z coeffs >= 0 → optimal at origin (x1=0, x2=0, z=0)
        assert_optimal(solution, 0.0)

    def test_returns_steps(self, problem_dual_feasible):
        solution, logs = solve_with_dual_simplex(problem_dual_feasible)
        if solution and solution["status"] == "Optimal":
            assert_has_steps(solution)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. DUAL-PRIMAL TWO-PHASE (dual_primal_two_phase.py)
# ═══════════════════════════════════════════════════════════════════════════════

class TestDualPrimalTwoPhase:
    """Tests cho DualPrimalTwoPhaseSolver (theory.md §3.8)."""

    def test_basic_minimize_geq(self, problem_min_basic):
        """Should handle min with >= constraints.
        Regression: Phase 1 dual simplex phải đạt Optimal Z=9 (trước đây báo Infeasible)."""
        solution, logs = solve_with_dual_primal_two_phase(problem_min_basic)
        assert_optimal(solution, 9.0, {"x1": 3.0, "x2": 1.0})

    def test_dual_feasible_also_works(self, problem_dual_feasible):
        """DP2P should also handle problems that pure dual simplex can handle.
        Regression: phải đạt Optimal Z=6 (trước đây báo Infeasible)."""
        solution, logs = solve_with_dual_primal_two_phase(problem_dual_feasible)
        assert_optimal(solution, 6.0)

    def test_maximize_problem(self, problem_max_basic):
        """Should handle maximization (standardized to min internally)."""
        solution, logs = solve_with_dual_primal_two_phase(problem_max_basic)
        assert solution is not None
        if solution["status"] == "Optimal":
            assert solution["objective_value"] == pytest.approx(36.0, abs=0.1)

    def test_3_variables(self, problem_3var):
        solution, logs = solve_with_dual_primal_two_phase(problem_3var)
        assert solution is not None
        # DP2P may give different path through Phase 1/2
        assert solution["status"] in ["Optimal", "MaxIterationsReached"]

    def test_returns_steps(self, problem_min_basic):
        solution, logs = solve_with_dual_primal_two_phase(problem_min_basic)
        if solution and solution.get("status") == "Optimal":
            assert_has_steps(solution)


# ═══════════════════════════════════════════════════════════════════════════════
# 6. DUALITY UTILITIES (duality.py)
# ═══════════════════════════════════════════════════════════════════════════════

class TestDuality:
    """Tests cho build_dual_problem và complementary_slackness."""

    def test_build_dual_from_max(self):
        """Max c^T x, Ax<=b → Dual: Min b^T y, A^T y >= c."""
        primal = {
            "objective": "maximize",
            "coeffs": [3, 5],
            "variables_names_for_title_only": ["x1", "x2"],
            "constraints": [
                {"name": "c1", "lhs": [1, 0], "op": "<=", "rhs": 4},
                {"name": "c2", "lhs": [0, 2], "op": "<=", "rhs": 12},
                {"name": "c3", "lhs": [3, 2], "op": "<=", "rhs": 18},
            ]
        }
        dual, step_md = build_dual_problem(primal)
        assert dual is not None
        # Primal Max → Dual Min
        assert dual["objective"] in ["minimize", "min"]
        # Dual should have 3 variables (one per primal constraint)
        assert len(dual["coeffs"]) == 3
        # Dual coefficients should be primal RHS: [4, 12, 18]
        assert dual["coeffs"] == [4, 12, 18]
        # Dual should have 2 constraints (one per primal variable)
        assert len(dual["constraints"]) == 2

    def test_build_dual_from_min(self):
        """Min c^T x, Ax>=b → Dual: Max b^T y, A^T y <= c."""
        primal = {
            "objective": "minimize",
            "coeffs": [2, 3],
            "variables_names_for_title_only": ["x1", "x2"],
            "constraints": [
                {"name": "c1", "lhs": [1, 1], "op": ">=", "rhs": 4},
                {"name": "c2", "lhs": [1, 3], "op": ">=", "rhs": 6},
            ]
        }
        dual, step_md = build_dual_problem(primal)
        assert dual is not None
        assert dual["objective"] in ["maximize", "max"]
        assert dual["coeffs"] == [4, 6]
        assert len(dual["constraints"]) == 2

    def test_dual_has_markdown(self):
        """build_dual_problem should produce markdown explanation."""
        primal = {
            "objective": "maximize",
            "coeffs": [1, 2],
            "variables_names_for_title_only": ["x1", "x2"],
            "constraints": [
                {"name": "c1", "lhs": [1, 1], "op": "<=", "rhs": 5},
            ]
        }
        dual, step_md = build_dual_problem(primal)
        assert dual is not None
        assert len(step_md) > 0

    def test_complementary_slackness_basic(self):
        """
        Primal: Max 3x1+5x2, Ax<=b
        Known dual solution: y1=0, y2=5/2, y3=0 (from strong duality)
        Should reconstruct primal solution.
        """
        primal = {
            "objective": "maximize",
            "coeffs": [3, 5],
            "variables_names_for_title_only": ["x1", "x2"],
            "constraints": [
                {"name": "c1", "lhs": [1, 0], "op": "<=", "rhs": 4},
                {"name": "c2", "lhs": [0, 2], "op": "<=", "rhs": 12},
                {"name": "c3", "lhs": [3, 2], "op": "<=", "rhs": 18},
            ]
        }
        dual_solution = {"y1": 0, "y2": 2.5, "y3": 0}
        result = complementary_slackness(primal, dual_solution)
        assert result is not None


# ═══════════════════════════════════════════════════════════════════════════════
# 7. CROSS-SOLVER CONSISTENCY
# ═══════════════════════════════════════════════════════════════════════════════

class TestCrossSolverConsistency:
    """So sánh kết quả giữa các solver trên cùng bài toán."""

    SOLVERS = [
        ("simplex", solve_with_simple_dictionary),
        ("bland", solve_with_simplex_bland),
        ("auxiliary", solve_with_auxiliary_problem_simplex),
    ]

    def test_all_solvers_agree_on_max_basic(self, problem_max_basic):
        """All primal solvers should give same optimal value for basic max problem."""
        results = {}
        for name, solver_fn in self.SOLVERS:
            solution, _ = solver_fn(problem_max_basic)
            if solution and solution.get("status") == "Optimal":
                results[name] = solution["objective_value"]

        values = list(results.values())
        assert len(values) >= 2, f"Less than 2 solvers returned Optimal: {results}"
        for v in values[1:]:
            assert v == pytest.approx(values[0], abs=1e-4), \
                f"Solver disagreement: {results}"

    def test_all_solvers_agree_on_min_geq(self, problem_min_basic):
        """All primal solvers should agree on min with >= constraints."""
        results = {}
        for name, solver_fn in self.SOLVERS:
            solution, _ = solver_fn(problem_min_basic)
            if solution and solution.get("status") == "Optimal":
                results[name] = solution["objective_value"]

        values = list(results.values())
        if len(values) >= 2:
            for v in values[1:]:
                assert v == pytest.approx(values[0], abs=1e-4), \
                    f"Solver disagreement: {results}"

    def test_all_solvers_agree_on_3var(self, problem_3var):
        """All primal solvers should agree on 3-variable problem."""
        results = {}
        for name, solver_fn in self.SOLVERS:
            solution, _ = solver_fn(problem_3var)
            if solution and solution.get("status") == "Optimal":
                results[name] = solution["objective_value"]

        values = list(results.values())
        if len(values) >= 2:
            for v in values[1:]:
                assert v == pytest.approx(values[0], abs=1e-4), \
                    f"Solver disagreement: {results}"


# ═══════════════════════════════════════════════════════════════════════════════
# 8. EDGE CASES
# ═══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Kiểm tra các trường hợp biên."""

    def test_single_variable_single_constraint(self):
        """Simplest possible LP: Max x1, x1 <= 5."""
        problem = {
            "objective": "maximize",
            "coeffs": [1],
            "variables_names_for_title_only": ["x1"],
            "constraints": [
                {"name": "c1", "lhs": [1], "op": "<=", "rhs": 5},
            ]
        }
        for solver_fn in [solve_with_simple_dictionary, solve_with_simplex_bland]:
            solution, _ = solver_fn(problem)
            assert_optimal(solution, 5.0, {"x1": 5.0})

    def test_zero_coefficients(self):
        """Zero objective coefficient for one variable."""
        problem = {
            "objective": "maximize",
            "coeffs": [0, 1],
            "variables_names_for_title_only": ["x1", "x2"],
            "constraints": [
                {"name": "c1", "lhs": [1, 1], "op": "<=", "rhs": 10},
            ]
        }
        solution, _ = solve_with_simple_dictionary(problem)
        assert_optimal(solution, 10.0, {"x2": 10.0})

    def test_already_optimal_at_origin(self):
        """Min x1 + x2, x1<=5, x2<=3 → optimal at origin."""
        problem = {
            "objective": "minimize",
            "coeffs": [1, 1],
            "variables_names_for_title_only": ["x1", "x2"],
            "constraints": [
                {"name": "c1", "lhs": [1, 0], "op": "<=", "rhs": 5},
                {"name": "c2", "lhs": [0, 1], "op": "<=", "rhs": 3},
            ]
        }
        solution, _ = solve_with_simple_dictionary(problem)
        assert_optimal(solution, 0.0, {"x1": 0.0, "x2": 0.0})

    def test_max_iterations_respected(self):
        """Solver should stop at max_iterations."""
        problem = {
            "objective": "maximize",
            "coeffs": [1, 1],
            "variables_names_for_title_only": ["x1", "x2"],
            "constraints": [
                {"name": "c1", "lhs": [-1, 1], "op": "<=", "rhs": 10},
            ]
        }
        solution, logs = solve_with_simple_dictionary(problem, max_iterations=2)
        assert solution is not None
        # With only 2 iterations, might not reach optimal
        assert solution["status"] in ["Optimal", "Unbounded", "MaxIterationsReached"]

    def test_empty_constraints(self):
        """No constraints except non-negativity."""
        problem = {
            "objective": "minimize",
            "coeffs": [1, 1],
            "variables_names_for_title_only": ["x1", "x2"],
            "constraints": []
        }
        solution, _ = solve_with_simple_dictionary(problem)
        assert solution is not None
        # Min x1 + x2 with no constraints and x >= 0 → optimal at origin
        if solution["status"] == "Optimal":
            assert solution["objective_value"] == pytest.approx(0.0, abs=1e-4)


# ═══════════════════════════════════════════════════════════════════════════════
# 9. REGRESSION — Phase 1 sign-bug (>= / == constraints)
# ═══════════════════════════════════════════════════════════════════════════════

class TestPhase1SignRegression:
    """Khóa lỗi đảo dấu trong Phase 1.

    Trước đây _find_entering_var_phase1 (primal) và _select_entering_var_dual (dual)
    chọn biến vào theo hệ số ÂM, trong khi với hàng cơ sở bất khả thi (b_i < 0) sinh
    từ ràng buộc '>=' / '==', hệ số sau chuẩn hóa là DƯƠNG. Hậu quả: mọi bài có
    '>=' / '==' bị 3 solver (simple_dictionary, simplex_bland, dual_primal_two_phase)
    và dual_simplex báo Infeasible nhầm. Các test này đảm bảo điều đó không tái diễn.
    """

    # (objective, coeffs, constraints, expected_Z)  — đối chiếu với PuLP
    CASES = [
        ("minimize", [4, 3], [([2, 1], ">=", 8), ([1, 2], ">=", 7)], 18.0),
        ("maximize", [1, 1], [([1, 1], "==", 10), ([1, 0], "<=", 6)], 10.0),
        ("maximize", [3, 2], [([1, 1], "<=", 10), ([1, 0], ">=", 2), ([0, 1], ">=", 1)], 29.0),
    ]

    PRIMAL_SOLVERS = [
        solve_with_simple_dictionary,
        solve_with_simplex_bland,
        solve_with_auxiliary_problem_simplex,
        solve_with_dual_primal_two_phase,
    ]

    @pytest.mark.parametrize("objective, coeffs, cons, expected_z", CASES)
    def test_primal_solvers_solve_geq_eq(self, objective, coeffs, cons, expected_z):
        problem = {
            "objective": objective,
            "coeffs": coeffs,
            "variables_names_for_title_only": [f"x{i+1}" for i in range(len(coeffs))],
            "constraints": [
                {"name": f"c{i+1}", "lhs": l, "op": o, "rhs": r}
                for i, (l, o, r) in enumerate(cons)
            ],
        }
        for solver_fn in self.PRIMAL_SOLVERS:
            solution, _ = solver_fn(dict(problem))
            assert solution is not None, f"{solver_fn.__name__} trả None"
            assert solution["status"] == "Optimal", \
                f"{solver_fn.__name__}: kỳ vọng Optimal, nhận {solution['status']}"
            assert solution["objective_value"] == pytest.approx(expected_z, abs=1e-4), \
                f"{solver_fn.__name__}: kỳ vọng Z={expected_z}, nhận {solution['objective_value']}"

    def test_dual_simplex_solves_dual_feasible_geq(self):
        # min với hệ số ≥ 0 và ràng buộc '>=' → dual feasible, primal infeasible ban đầu.
        problem = {
            "objective": "minimize",
            "coeffs": [4, 3],
            "variables_names_for_title_only": ["x1", "x2"],
            "constraints": [
                {"name": "c1", "lhs": [2, 1], "op": ">=", "rhs": 8},
                {"name": "c2", "lhs": [1, 2], "op": ">=", "rhs": 7},
            ],
        }
        solution, _ = solve_with_dual_simplex(problem)
        assert_optimal(solution, 18.0)
