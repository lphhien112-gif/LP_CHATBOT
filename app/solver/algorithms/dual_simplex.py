# /app/solver/algorithms/dual_simplex.py
import logging
from typing import Dict, List, Any, Tuple, Optional
import numpy as np

from .base_simplex_dictionary_solver import BaseSimplexDictionarySolver
from app.solver.utils import standardize_problem_for_simplex

logger = logging.getLogger(__name__)


class DualSimplexSolver(BaseSimplexDictionarySolver):
    """
    Thuật toán Đơn hình Đối ngẫu (Dual Simplex Method) — theory.md §3.7.
    
    Áp dụng khi:
      - Hệ số hàm mục tiêu z đều >= 0 (dual feasible)
      - Nhưng ∃ b_i < 0 (primal infeasible)
    
    Quy trình:
      Bước 1: Chọn biến RA trước — dòng có b_i âm nhất
      Bước 2: Chọn biến VÀO sau — min{G_j / a_{ij}} với G_j > 0 và a_{ij} > 0
      Lặp cho đến khi mọi b_i >= 0 (primal feasible) → tối ưu
    
    Kế thừa từ Base:
      - _build_standard_dictionary (build z + w_i)
      - _select_leaving_var_dual (chọn biến ra)
      - _select_entering_var_dual (chọn biến vào)
    """

    def __init__(self, problem_data_standardized: Dict[str, Any]):
        super().__init__(problem_data_standardized, objective_key_in_dict='z_dual')
        self.current_phase_info: Optional[str] = None

    def _build_initial_dictionary(self) -> bool:
        self._log("DualSimplexSolver: Building Initial Dictionary...")
        if not self._build_standard_dictionary():
            return False
        self._log_dictionary(phase_info="Initial Build (Dual Simplex)")
        return True

    def _check_dual_feasibility(self) -> bool:
        """Kiểm tra tính chấp nhận được của đối ngẫu: mọi hệ số z >= 0."""
        obj_expr = self.dictionary.get(self.current_objective_key, {})
        for var_name in self.non_basic_vars:
            coeff = obj_expr.get(var_name, 0.0)
            if coeff < -self.epsilon:
                return False
        return True

    def solve(self, max_iterations: int = 50) -> Tuple[Optional[Dict[str, Any]], List[str]]:
        self.iteration_count = 0
        self._log(f"Starting DualSimplexSolver. Max iterations: {max_iterations}")
        self._log(f"Objective: {self.current_objective_type} {self.current_objective_key}")

        if not self._build_initial_dictionary():
            return self._extract_solution("ErrorInSetup"), self.logs

        # Kiểm tra dual feasibility (z hệ số >= 0)
        if not self._check_dual_feasibility():
            self._log("WARNING: Hàm mục tiêu có hệ số âm → Không phải dual feasible.")
            self._generate_tableau_md(phase_info="Initial — NOT Dual Feasible")
            return self._extract_solution("NotDualFeasible"), self.logs

        self.current_phase_info = "Dual Simplex"
        opt_iter = 0

        while opt_iter < max_iterations:
            opt_iter += 1
            self.iteration_count += 1
            self._log_dictionary(phase_info=self.current_phase_info)

            # Bước 1: Chọn biến ra (b_i âm nhất) — kế thừa từ Base
            leaving_var = self._select_leaving_var_dual()
            if leaving_var is None:
                self._log("Dual Simplex: Mọi b_i >= 0. Tối ưu!")
                self._generate_tableau_md(phase_info="Final Optimal")
                return self._extract_solution("Optimal"), self.logs

            # Bước 2: Chọn biến vào — kế thừa từ Base
            entering_var = self._select_entering_var_dual(leaving_var)
            if entering_var is None:
                self._generate_tableau_md(phase_info=self.current_phase_info, leaving_var=leaving_var)
                self._log("Dual Simplex: Bài toán VÔ NGHIỆM (Infeasible).")
                return self._extract_solution("Infeasible"), self.logs

            self._generate_tableau_md(phase_info=self.current_phase_info, entering_var=entering_var, leaving_var=leaving_var)

            if not self._perform_pivot(entering_var, leaving_var):
                self._log("Dual Simplex: Pivot failed.")
                return self._extract_solution("ErrorInPivot"), self.logs

        self._log(f"Max iterations ({max_iterations}) reached.")
        return self._extract_solution("MaxIterationsReached"), self.logs


def solve_with_dual_simplex(
    problem_data_input: Dict[str, Any],
    max_iterations=50
) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """Hàm bao bọc cho DualSimplexSolver."""
    overall_logs: List[str] = []
    overall_logs.append("--- solve_with_dual_simplex called ---")

    standardized_problem_data, was_maximized = standardize_problem_for_simplex(problem_data_input, overall_logs)

    if standardized_problem_data is None:
        overall_logs.append("ERROR: Standardization failed.")
        return {"status": "Error", "message": "Input data standardization failed."}, overall_logs

    standardized_problem_data['objective_type_before_standardization'] = problem_data_input.get("objective", "N/A")

    solver = DualSimplexSolver(standardized_problem_data)
    solution, solver_logs = solver.solve(max_iterations=max_iterations)
    overall_logs.extend(solver_logs)

    if solution and solution.get("status") == "Optimal" and was_maximized:
        if solution.get("objective_value") is not None:
            solution["objective_value"] *= -1
            overall_logs.append(f"Final objective (original MAX) adjusted: {solution['objective_value']:.4g}")

    elif solution and solution.get("status") == "Unbounded" and was_maximized:
        overall_logs.append("Original MAX problem is also Unbounded (Dual Simplex).")

    overall_logs.append("--- solve_with_dual_simplex finished ---")
    return solution, overall_logs
