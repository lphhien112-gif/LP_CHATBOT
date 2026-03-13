# /app/solver/simplex_bland_solver.py
import logging
from typing import Dict, List, Any, Tuple, Optional
import numpy as np

from .base_simplex_dictionary_solver import BaseSimplexDictionarySolver
from app.solver.utils import standardize_problem_for_simplex # Import hàm chuẩn hóa

logger = logging.getLogger(__name__)

class SimplexBlandSolver(BaseSimplexDictionarySolver):
    """
    Triển khai thuật toán Simplex bằng phương pháp từ điển,
    sử dụng Quy tắc Bland cho cả việc chọn biến vào và biến ra.
    Kế thừa từ BaseSimplexDictionarySolver, nơi các phương thức chọn biến
    đã mặc định theo Quy tắc Bland.
    Xử lý trường hợp RHS âm cho ràng buộc '<=' bằng một "Pha 1 đơn giản".
    Mong đợi problem_data đầu vào đã được chuẩn hóa:
    - objective: "min"
    - constraints[i].op: "<="
    """
    def __init__(self, problem_data_standardized: Dict[str, Any]):
        super().__init__(problem_data_standardized, objective_key_in_dict='z_bland') # Sử dụng key khác để phân biệt nếu cần
        self.current_phase_info: Optional[str] = None
        # BaseSimplexDictionarySolver.__init__ đã xử lý việc đọc objective, coeffs, vars
        # từ problem_data_standardized.

    def _build_initial_dictionary(self) -> bool:
        self._log("SimplexBlandSolver: Building Initial Dictionary...")
        if not self._build_standard_dictionary():
            return False
        self._log_dictionary(phase_info="Initial Build (Bland)")
        return True

    # _select_entering_variable và _select_leaving_variable kế thừa từ Base (Bland mặc định)
    # _find_leaving_var_phase1, _find_entering_var_phase1, _run_phase1_simple kế thừa từ Base

    def solve(self, max_iterations: int = 50) -> Tuple[Optional[Dict[str, Any]], List[str]]:
        self.iteration_count = 0
        self._log(f"Starting SimplexBlandSolver. Max iterations: {max_iterations}")
        self._log(f"Input problem objective type (before standardization by wrapper): {self.problem_data.get('objective_type_before_standardization', 'N/A')}")
        self._log(f"Solver will use objective: {self.current_objective_type} {self.current_objective_key}")

        if not self._build_initial_dictionary():
            return self._extract_solution("ErrorInSetup"), self.logs

        # Thêm header giải thích quy tắc Bland cho Markdown
        self.step_by_step_md.insert(0, "\\textbf{Phương pháp xoay Bland:}\n\n"
                                       "\\textbf{Chọn biến vào:} Trong số các biến không cơ sở có hệ số âm ($G < 0$) \\\\\n"
                                       "Chọn \\textbf{biến có chỉ số nhỏ nhất} ($x_1, x_2, x_3, w_1, w_2$)\n\n"
                                       "\\textbf{Chọn biến ra:} Y như đơn hình tính $\\frac{b_i}{a_{ij}} (=0)$\n\n"
                                       "\\textbf{\\underline{VD:}}\n")

        initial_feasibility_check_var = self._find_leaving_var_phase1()
        if initial_feasibility_check_var is not None:
            self._log(f"Initial dictionary not feasible ({initial_feasibility_check_var}). Running Phase 1 (Bland).")
            phase1_status = self._run_phase1_simple(max_iterations // 2 if max_iterations > 1 else 1, "Phase 1 (Bland)")
            if phase1_status != "Feasible":
                return self._extract_solution(phase1_status), self.logs
        else:
            self._log("Initial dictionary is feasible. Proceeding to Optimization Phase (Bland).")

        self._log("--- Starting Optimization Phase (SimplexBlandSolver) ---")
        self.current_phase_info = "Optimization (Bland)"

        remaining_iterations = max_iterations - self.iteration_count
        if remaining_iterations <= 0: remaining_iterations = max_iterations // 2 + 1 if max_iterations > 0 else 1

        opt_phase_iter = 0
        while opt_phase_iter < remaining_iterations:
            opt_phase_iter += 1; self.iteration_count += 1
            self._log_dictionary(phase_info=self.current_phase_info)

            entering_var = self._select_entering_variable() # Kế thừa từ BaseSimplex (đã là Bland)
            if not entering_var:
                self._log("Optimization Phase (Bland): Optimal solution found.")
                self._generate_tableau_md(phase_info="Final Optimal")
                return self._extract_solution("Optimal"), self.logs

            leaving_var = self._select_leaving_variable(entering_var) # Kế thừa từ BaseSimplex (đã là Bland)
            if not leaving_var:
                self._log(f"Optimization Phase (Bland): Problem is UNBOUNDED for entering var {entering_var}.")
                self._generate_tableau_md(phase_info=self.current_phase_info, entering_var=entering_var)
                return self._extract_solution("Unbounded"), self.logs


            self._generate_tableau_md(phase_info=self.current_phase_info, entering_var=entering_var, leaving_var=leaving_var)

            if not self._perform_pivot(entering_var, leaving_var):
                 self._log("Optimization Phase (Bland) FAILED: Pivot operation failed.")
                 return self._extract_solution("ErrorInPivot"), self.logs

        self._log(f"Max iterations ({max_iterations}) reached. Algorithm (Bland) terminated.")
        return self._extract_solution("MaxIterationsReached"), self.logs

def solve_with_simplex_bland(
    problem_data_input: Dict[str, Any], # Đây là "Định dạng A" từ DialogManager
    max_iterations=50
) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """
    Hàm bao bọc để giải bài toán LP bằng SimplexBlandSolver.
    Sẽ chuẩn hóa bài toán trước khi giải.
    """
    overall_logs: List[str] = []
    overall_logs.append("--- solve_with_simplex_bland called ---")

    standardized_problem_data, was_maximized = standardize_problem_for_simplex(problem_data_input, overall_logs)

    if standardized_problem_data is None:
        overall_logs.append("ERROR: Standardization failed for SimplexBlandSolver.")
        return {"status": "Error", "message": "Input data standardization failed."}, overall_logs
    
    # Lưu lại loại mục tiêu gốc để log
    standardized_problem_data['objective_type_before_standardization'] = problem_data_input.get("objective", "N/A")


    solver = SimplexBlandSolver(standardized_problem_data)
    solution, solver_logs = solver.solve(max_iterations=max_iterations)
    overall_logs.extend(solver_logs)

    if solution and solution.get("status") == "Optimal" and was_maximized:
        if solution.get("objective_value") is not None:
            solution["objective_value"] *= -1
            overall_logs.append(f"Final objective value (for original MAX problem, Bland) adjusted: {solution['objective_value']:.4g}")
        else:
            overall_logs.append(f"Warning (Bland): Solution status is Optimal but objective_value is None. Cannot adjust for original MAX problem.")


    elif solution and solution.get("status") == "Unbounded" and was_maximized:
        overall_logs.append("Original MAX problem is also Unbounded (Bland).")
        
    overall_logs.append("--- solve_with_simplex_bland finished ---")
    return solution, overall_logs

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Bài toán từ hình ảnh "Bài 3.6" (ví dụ Klee-Minty có thể gây xoay vòng cho Dantzig)
    # min 2x1 - 3x2 + 4x3
    # s.t. 2x2 + 3x3 <= 5  (s_b1)
    #      x1 + x2 + 2x3 <= 4  (s_b2)
    #      x1 + 2x2 + 3x3 <= 7  (s_b3)
    # Lời giải tối ưu: x1=0, x2=0, x3=0, z_bland=0 (vì tất cả hệ số mục tiêu là dương sau khi chuẩn hóa min, và các biến phi âm)
    # Tuy nhiên, ví dụ này đơn giản. Một ví dụ Klee-Minty thực sự sẽ phức tạp hơn.
    # Mục tiêu là kiểm tra quy tắc Bland hoạt động.
    problem_b3_6_new_format = {
        "objective": "min",
        "coeffs": [2, -3, 4], # min 2x1 -3x2 +4x3
        "variables_names_for_title_only": ["x1", "x2", "x3"],
        "constraints": [
            {"name": "w1_constr", "lhs": [0, 2, 3], "op": "<=", "rhs": 5},
            {"name": "w2_constr", "lhs": [1, 1, 2], "op": "<=", "rhs": 4},
            {"name": "w3_constr", "lhs": [1, 2, 3], "op": "<=", "rhs": 7}
            # x1,x2,x3 >= 0 được giả định bởi Simplex, không cần thêm dưới dạng ràng buộc tường minh
            # cho các solver Simplex cơ bản nếu chúng xử lý bài toán dạng chuẩn (biến không âm).
            # Nếu muốn test ràng buộc phi âm tường minh, chúng cần được thêm và chuẩn hóa thành <=.
        ]
    }

    print("--- Test 1: Solving Problem (Bài 3.6) with SimplexBlandSolver ---")
    # Với hàm mục tiêu là Min, x2 (hệ số -3) sẽ vào.
    # s_b1 = 5 - 2x2 - 3x3  => ratio x2: 5/2 = 2.5 (s_b1 ra)
    # s_b2 = 4 - x1 - x2 - 2x3 => ratio x2: 4/1 = 4
    # s_b3 = 7 - x1 - 2x2 - 3x3 => ratio x2: 7/2 = 3.5
    # s_b1 ra.
    solution1, logs1 = solve_with_simplex_bland(problem_b3_6_new_format, max_iterations=10)
    print("\n--- FULL LOGS (Test 1 - Bland) ---")
    for log_entry in logs1: print(log_entry)
    print("\n--- FINAL SOLUTION (Test 1 - Bland) ---")
    if solution1: import json; print(json.dumps(solution1, indent=2))
    # Dự kiến: x1=3, x2=1, x3=0, z_bland = 2*3 - 3*1 + 4*0 = 6 - 3 = 3. (Theo Pulp)
    # Solver tay: x2=2.5, x1=0, x3=0, z = -3*(2.5) = -7.5


    # Test với bài toán có RHS âm (Pha 1 đơn giản sẽ được kích hoạt)
    problem_b1_12_standardized_for_bland = {
        "objective": "min", # Mục tiêu đã là min
        "coeffs": [-3, -2], # Hệ số của hàm min
        "variables_names_for_title_only": ["x1", "x2"],
        "constraints": [
            # standardize_problem_for_simplex sẽ đảm bảo tất cả là <=
            # Nên truyền vào đây dữ liệu gốc để test hàm standardize
            {"name": "RB1_orig", "lhs": [2, 1], "op": "<=", "rhs": 2},
            {"name": "RB2_orig", "lhs": [3, 4], "op": ">=", "rhs": 12} # Sẽ thành -3x1 -4x2 <= -12
        ]
    }
    print("\n\n--- Test 2: Solving Problem (Bài 1.12 - Bland) with negative RHS after standardization ---")
    solution2, logs2 = solve_with_simplex_bland(problem_b1_12_standardized_for_bland, max_iterations=10)
    print("\n--- FULL LOGS (Test 2 - Bland) ---")
    for log_entry in logs2: print(log_entry)
    print("\n--- FINAL SOLUTION (Test 2 - Bland) ---")
    if solution2: import json; print(json.dumps(solution2, indent=2))
    # Bài toán gốc: min Z = -3x1 - 2x2, s.t. 2x1+x2<=2, 3x1+4x2>=12, x1,x2>=0
    # Pulp cho nghiệm: Infeasible.

