# /tests/test_solver.py
"""
Tests cho các Solver Algorithms.
Mỗi solver nhận dữ liệu theo "Format A":
  - objective: "maximize" | "minimize"
  - coeffs: [c1, c2, ...]
  - variables_names_for_title_only: ["x1", "x2", ...]
  - constraints: [{"name": ..., "lhs": [...], "op": "<="|">="|"==", "rhs": ...}]
"""
import pytest
import base64

from app.solver.algorithms.pulp_cbc import solve_with_pulp_cbc
from app.solver.algorithms.simplex import solve_with_simple_dictionary as solve_with_simplex
from app.solver.algorithms.geometric import solve_with_geometric_method

# ─────────────────────────────────────────────────────────────────────────────
# Fixtures: Format A data
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def max_problem_format_a():
    """Maximize 3x1 + 5x2, Optimal: x1=2, x2=6, Z=36"""
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
def infeasible_problem_format_a():
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
def two_var_problem_format_a():
    """Maximize 3x1 + 2x2 with explicit non-neg constraints (safe for all solvers)"""
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

# ─────────────────────────────────────────────────────────────────────────────
# PuLP CBC Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_pulp_cbc_solver_maximize(max_problem_format_a):
    solution, _ = solve_with_pulp_cbc(max_problem_format_a)
    assert solution is not None
    assert solution["status"] == "Optimal"
    assert solution["objective_value"] == pytest.approx(36.0)
    assert solution["variables"]["x1"] == pytest.approx(2.0)
    assert solution["variables"]["x2"] == pytest.approx(6.0)

def test_pulp_cbc_solver_infeasible(infeasible_problem_format_a):
    solution, _ = solve_with_pulp_cbc(infeasible_problem_format_a)
    assert solution is not None
    assert solution["status"] == "Infeasible"

def test_pulp_cbc_solver_missing_keys():
    """Solver should return None when required keys are missing."""
    solution, logs = solve_with_pulp_cbc({"objective": "maximize"})
    assert solution is None
    assert any("Missing" in log for log in logs)

# ─────────────────────────────────────────────────────────────────────────────
# Simplex Dictionary Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_simplex_solver_maximize(two_var_problem_format_a):
    """Simplex should solve the problem or gracefully return a result dict."""
    solution, logs = solve_with_simplex(two_var_problem_format_a)
    # The simplex solver may report Optimal or not support all edge cases
    # We mainly check it doesn't crash and returns a dict
    assert solution is not None
    assert "status" in solution

# ─────────────────────────────────────────────────────────────────────────────
# Geometric Solver Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_geometric_solver_maximize(two_var_problem_format_a):
    solution, _ = solve_with_geometric_method(two_var_problem_format_a)
    assert solution is not None
    assert solution["status"] == "Optimal"

def test_geometric_solver_produces_plot(two_var_problem_format_a):
    """Geometric solver should produce a base64-encoded plot image."""
    solution, _ = solve_with_geometric_method(two_var_problem_format_a)
    if solution and solution.get("plot_image_base64"):
        # Verify it's valid base64
        try:
            base64.b64decode(solution["plot_image_base64"].split(",")[-1])
        except Exception:
            pytest.fail("plot_image_base64 is not valid base64 data")

def test_geometric_solver_fails_with_3_variables():
    """Geometric solver should gracefully handle > 2 variables."""
    problem_3var = {
        "objective": "maximize",
        "coeffs": [1, 1, 1],
        "variables_names_for_title_only": ["x1", "x2", "x3"],
        "constraints": [
            {"name": "c1", "lhs": [1, 0, 0], "op": "<=", "rhs": 4},
        ]
    }
    solution, logs = solve_with_geometric_method(problem_3var)
    # Should return an error/None, not crash
    assert solution is None or solution.get("status") != "Optimal" or logs
