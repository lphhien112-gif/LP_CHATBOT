# /app/solver/algorithms/dual_primal_two_phase.py
import logging
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
import copy

from .base_simplex_dictionary_solver import BaseSimplexDictionarySolver
from app.solver.utils import standardize_problem_for_simplex

logger = logging.getLogger(__name__)


class DualPrimalTwoPhaseSolver(BaseSimplexDictionarySolver):
    """
    Thuật toán 2 Pha Đối ngẫu - Gốc (theory.md §3.8).

    Áp dụng khi:
      - ∃ b_i < 0 nhưng hệ số z CÓ giá trị âm
      → Không chạy được Dual Simplex trực tiếp

    Pha 1: Lập bài toán bổ trợ min |c_i|x_i, chạy Dual Simplex → từ vựng khả thi
    Pha 2: Lắp hàm mục tiêu gốc, chạy Primal Simplex → nghiệm tối ưu

    Kế thừa từ Base:
      - _build_standard_dictionary (build z + w_i)
      - _select_leaving_var_dual, _select_entering_var_dual (Dual Simplex)
      - _select_entering_variable, _select_leaving_variable (Primal Simplex / Bland)
    """

    def __init__(self, problem_data_standardized: Dict[str, Any]):
        super().__init__(problem_data_standardized, objective_key_in_dict='z_dp2p')
        self.current_phase: int = 0
        self.original_objective_coeffs: List[float] = list(self.problem_data.get("coeffs", []))
        self.phase1_objective_key = 'z_bt'  # z bổ trợ

    def _build_initial_dictionary(self) -> bool:
        """Pha 1: Build dictionary với hàm mục tiêu |c_i|."""
        self._log("DualPrimalTwoPhaseSolver: Building Initial Dictionary (Phase 1)...")
        self.current_phase = 1
        self.current_objective_key = self.phase1_objective_key
        self.current_objective_type = "minimize"

        # Tạo hệ số |c_i| cho Pha 1
        abs_coeffs = [abs(c) for c in self.original_objective_coeffs]
        if not self._build_standard_dictionary(obj_coeffs=abs_coeffs):
            return False

        self._log_dictionary(phase_info="Phase 1 — Bài toán bổ trợ (|c_i|)")
        self._generate_tableau_md(phase_info="Phase 1 — Initial")
        return True

    def _run_dual_simplex_phase(self, max_iters: int) -> str:
        """Chạy Dual Simplex cho Pha 1 — kế thừa methods từ Base."""
        phase_iter = 0
        while phase_iter < max_iters:
            phase_iter += 1
            self.iteration_count += 1
            self._log_dictionary(phase_info=f"Phase {self.current_phase} — Dual Iter {phase_iter}")

            leaving = self._select_leaving_var_dual()
            if leaving is None:
                self._generate_tableau_md(phase_info=f"Phase {self.current_phase} — Feasible")
                self._log("Dual Simplex Pha 1: Mọi b_i >= 0. Từ vựng khả thi!")
                return "Feasible"

            entering = self._select_entering_var_dual(leaving)
            if entering is None:
                self._generate_tableau_md(phase_info=f"Phase {self.current_phase}", leaving_var=leaving)
                self._log("Dual Simplex Pha 1: Infeasible.")
                return "Infeasible"

            self._generate_tableau_md(
                phase_info=f"Phase {self.current_phase}",
                entering_var=entering, leaving_var=leaving
            )

            if not self._perform_pivot(entering, leaving):
                return "ErrorInPivot"

        return "MaxIterationsReached"

    def _run_primal_simplex_phase(self, max_iters: int) -> str:
        """Chạy Primal Simplex cho Pha 2 — kế thừa methods từ Base."""
        phase_iter = 0
        while phase_iter < max_iters:
            phase_iter += 1
            self.iteration_count += 1
            self._log_dictionary(phase_info=f"Phase {self.current_phase} — Primal Iter {phase_iter}")

            entering = self._select_entering_variable()  # Bland mặc định từ Base
            if not entering:
                self._generate_tableau_md(phase_info="Phase 2 — Final Optimal")
                return "Optimal"

            leaving = self._select_leaving_variable(entering)  # Bland từ Base
            if not leaving:
                self._generate_tableau_md(phase_info="Phase 2", entering_var=entering)
                return "Unbounded"

            self._generate_tableau_md(
                phase_info="Phase 2",
                entering_var=entering, leaving_var=leaving
            )

            if not self._perform_pivot(entering, leaving):
                return "ErrorInPivot"

        return "MaxIterationsReached"

    def solve(self, max_iterations: int = 50) -> Tuple[Optional[Dict[str, Any]], List[str]]:
        self.iteration_count = 0
        self._log(f"Starting DualPrimalTwoPhaseSolver. Max iterations: {max_iterations}")

        if not self._build_initial_dictionary():
            return self._extract_solution("ErrorInSetup"), self.logs

        # --- PHA 1: Dual Simplex trên bài toán bổ trợ (|c_i|) ---
        max_p1 = max_iterations // 2 if max_iterations > 1 else 1
        p1_status = self._run_dual_simplex_phase(max_p1)
        self._log(f"Phase 1 (Dual on |c| objective) ended: {p1_status}")

        if p1_status != "Feasible":
            return self._extract_solution(f"Phase1_{p1_status}"), self.logs

        # --- PHA 2: Lắp hàm mục tiêu gốc, chạy Primal Simplex ---
        self._log("--- Preparing Phase 2: Lắp hàm mục tiêu gốc ---")
        self.current_phase = 2
        self.current_objective_key = 'z_dp2p'
        self.current_objective_type = "minimize"

        # Xóa hàm mục tiêu bổ trợ
        if self.phase1_objective_key in self.dictionary:
            del self.dictionary[self.phase1_objective_key]

        # Khôi phục hàm mục tiêu gốc bằng substitution
        z_expr: Dict[str, float] = {'const': 0.0}
        for i, dv in enumerate(self.decision_vars_names):
            coeff = self.original_objective_coeffs[i] if i < len(self.original_objective_coeffs) else 0.0
            if dv in self.basic_vars:
                dv_expr = self.dictionary.get(dv, {})
                z_expr['const'] += coeff * dv_expr.get('const', 0.0)
                for nb_var, nb_coeff in dv_expr.items():
                    if nb_var != 'const':
                        z_expr[nb_var] = z_expr.get(nb_var, 0.0) + coeff * nb_coeff
            elif dv in self.non_basic_vars:
                z_expr[dv] = z_expr.get(dv, 0.0) + coeff

        self.dictionary[self.current_objective_key] = z_expr
        self._log_dictionary(phase_info="Phase 2 — Initial (Original Objective)")
        self._generate_tableau_md(phase_info="Phase 2 — Initial")

        # Chạy Primal Simplex
        remaining = max_iterations - self.iteration_count
        if remaining <= 0:
            remaining = max_iterations // 2 + 1
        p2_status = self._run_primal_simplex_phase(remaining)
        self._log(f"Phase 2 (Primal Simplex) ended: {p2_status}")

        return self._extract_solution(p2_status), self.logs


def solve_with_dual_primal_two_phase(
    problem_data_input: Dict[str, Any],
    max_iterations=50
) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """Hàm bao bọc cho DualPrimalTwoPhaseSolver."""
    overall_logs: List[str] = []
    overall_logs.append("--- solve_with_dual_primal_two_phase called ---")

    standardized, was_maximized = standardize_problem_for_simplex(problem_data_input, overall_logs)

    if standardized is None:
        overall_logs.append("ERROR: Standardization failed.")
        return {"status": "Error", "message": "Input data standardization failed."}, overall_logs

    standardized['objective_type_before_standardization'] = problem_data_input.get("objective", "N/A")

    solver = DualPrimalTwoPhaseSolver(standardized)
    solution, solver_logs = solver.solve(max_iterations=max_iterations)
    overall_logs.extend(solver_logs)

    if solution and solution.get("status") == "Optimal" and was_maximized:
        if solution.get("objective_value") is not None:
            solution["objective_value"] *= -1
            overall_logs.append(f"Final objective (original MAX) adjusted: {solution['objective_value']:.4g}")

    overall_logs.append("--- solve_with_dual_primal_two_phase finished ---")
    return solution, overall_logs
