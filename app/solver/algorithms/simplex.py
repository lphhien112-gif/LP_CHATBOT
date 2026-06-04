# /app/solver/simple_dictionary_solver.py
import logging
from typing import Dict, List, Any, Tuple, Optional
import numpy as np

from .base_simplex_dictionary_solver import BaseSimplexDictionarySolver
from app.solver.utils import standardize_problem_for_simplex # Import hàm chuẩn hóa

logger = logging.getLogger(__name__)

class SimpleDictionarySolver(BaseSimplexDictionarySolver):
    """
    Triển khai thuật toán Simplex bằng phương pháp từ điển,
    sử dụng quy tắc Dantzig để chọn biến vào.
    Kế thừa từ BaseSimplexDictionarySolver.
    Xử lý trường hợp RHS âm cho ràng buộc '<=' bằng một "Pha 1 đơn giản".
    Mong đợi problem_data đầu vào đã được chuẩn hóa:
    - objective: "min"
    - constraints[i].op: "<="
    """
    def __init__(self, problem_data_standardized: Dict[str, Any]):
        # problem_data_standardized ở đây đã được chuẩn hóa (mục tiêu là "min", ràng buộc là "<=")
        super().__init__(problem_data_standardized, objective_key_in_dict='z_obj')
        self.current_phase_info: Optional[str] = None
        # original_objective_type và objective_coeffs_list đã được xử lý trong BaseSimplexDictionarySolver.__init__
        # dựa trên problem_data_standardized (luôn là "min" và các hệ số tương ứng)

    def _build_initial_dictionary(self) -> bool:
        self._log("SimpleDictionarySolver: Building Initial Dictionary...")
        if not self._build_standard_dictionary():
            return False
        self._log_dictionary(phase_info="Initial Build (Dantzig)")
        return True

    def _select_entering_variable(self) -> Optional[str]:
        """
        Chọn biến vào cơ sở theo Quy tắc Dantzig.
        Vì hàm mục tiêu luôn là "minimize", chúng ta tìm hệ số âm nhất (most negative).
        """
        obj_expr = self.dictionary.get(self.current_objective_key)
        if obj_expr is None:
            self._log(f"ERROR: Objective key '{self.current_objective_key}' not found for entering var selection.")
            return None

        # Chỉ chọn biến vào nếu hệ số mục tiêu âm thực sự (nhỏ hơn -epsilon).
        # Khởi tạo bằng -epsilon (KHÔNG phải +epsilon) để tránh chọn nhầm các hệ số
        # dương rất nhỏ (~0) làm biến vào — điều này có thể gây pivot không cải thiện
        # hoặc xoay vòng (cycling).
        most_negative_coeff = -self.epsilon # Tìm hệ số < 0 có giá trị tuyệt đối lớn nhất
        entering_var: Optional[str] = None

        sorted_non_basic_vars = sorted(
            [nb_var for nb_var in self.non_basic_vars if nb_var in self.all_vars_ordered],
            key=lambda v_name: self.all_vars_ordered.index(v_name)
        )
        for var_name in sorted_non_basic_vars:
            coeff = obj_expr.get(var_name, 0.0)
            if coeff < most_negative_coeff:
                most_negative_coeff = coeff
                entering_var = var_name

        if entering_var is None:
            self._log(f"Optimality condition met for {self.current_objective_key} (minimize). No candidates (Dantzig).")
            return None

        self._log(f"Selected Entering (Dantzig): {entering_var} (coeff: {most_negative_coeff:.4g})")
        return entering_var

    # _select_leaving_variable kế thừa từ Base (Bland tie-break)
    # _find_leaving_var_phase1, _find_entering_var_phase1, _run_phase1_simple kế thừa từ Base


    def solve(self, max_iterations: int = 50) -> Tuple[Optional[Dict[str, Any]], List[str]]:
        self.iteration_count = 0
        self._log(f"Starting SimpleDictionarySolver (Dantzig for entering). Max iterations: {max_iterations}")
        self._log(f"Input problem objective type (before standardization by wrapper): {self.problem_data.get('objective_type_before_standardization', 'N/A')}")
        self._log(f"Solver will use objective: {self.current_objective_type} {self.current_objective_key}")


        if not self._build_initial_dictionary(): # Xây dựng từ điển từ dữ liệu đã chuẩn hóa
            return self._extract_solution("ErrorInSetup"), self.logs

        initial_feasibility_check_var = self._find_leaving_var_phase1()
        if initial_feasibility_check_var is not None:
            self._log(f"Initial dictionary not feasible ({initial_feasibility_check_var} has negative constant). Running Phase 1.")
            phase1_status = self._run_phase1_simple(max_iterations // 2 if max_iterations > 1 else 1, "Phase 1 (Dantzig)")
            if phase1_status != "Feasible":
                return self._extract_solution(phase1_status), self.logs
        else:
            self._log("Initial dictionary is feasible. Proceeding to Optimization Phase.")

        self._log("--- Starting Optimization Phase (SimpleDictionarySolver) ---")
        self.current_phase_info = "Optimization"

        remaining_iterations = max_iterations - self.iteration_count
        if remaining_iterations <= 0: remaining_iterations = max_iterations // 2 +1 if max_iterations > 0 else 1


        opt_phase_iter = 0
        while opt_phase_iter < remaining_iterations:
            opt_phase_iter += 1; self.iteration_count += 1
            self._log_dictionary(phase_info=self.current_phase_info)

            entering_var = self._select_entering_variable() # Sử dụng Dantzig (đã ghi đè cho min)
            if not entering_var:
                self._log("Optimization Phase: Optimal solution found.")
                self._generate_tableau_md(phase_info="Final Optimal")
                return self._extract_solution("Optimal"), self.logs

            leaving_var = self._select_leaving_variable(entering_var) # Sử dụng Bland tie-breaker từ lớp cha
            if not leaving_var:
                self._log(f"Optimization Phase: Problem is UNBOUNDED for entering var {entering_var}.")
                self._generate_tableau_md(phase_info=self.current_phase_info, entering_var=entering_var)
                return self._extract_solution("Unbounded"), self.logs

            self._generate_tableau_md(phase_info=self.current_phase_info, entering_var=entering_var, leaving_var=leaving_var)

            if not self._perform_pivot(entering_var, leaving_var):
                 self._log("Optimization Phase FAILED: Pivot operation failed.")
                 return self._extract_solution("ErrorInPivot"), self.logs

        self._log(f"Max iterations ({max_iterations}) reached. Algorithm terminated.")
        return self._extract_solution("MaxIterationsReached"), self.logs

def solve_with_simple_dictionary(
    problem_data_input: Dict[str, Any], # Đây là "Định dạng A" từ DialogManager
    max_iterations=50
) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """
    Hàm bao bọc để giải bài toán LP bằng SimpleDictionarySolver.
    Sẽ chuẩn hóa bài toán trước khi giải.
    """
    overall_logs: List[str] = []
    overall_logs.append("--- solve_with_simple_dictionary called ---")
    
    # Bước 1: Chuẩn hóa bài toán
    # problem_data_input ở đây là "Định dạng A"
    standardized_problem_data, was_maximized = standardize_problem_for_simplex(problem_data_input, overall_logs)

    if standardized_problem_data is None:
        overall_logs.append("ERROR: Standardization failed for SimpleDictionarySolver.")
        return {"status": "Error", "message": "Input data standardization failed."}, overall_logs
    
    # Lưu lại loại mục tiêu gốc để log, solver class sẽ tự biết là đang min
    standardized_problem_data['objective_type_before_standardization'] = problem_data_input.get("objective", "N/A")

    # Bước 2: Khởi tạo và chạy solver với dữ liệu đã chuẩn hóa
    solver = SimpleDictionarySolver(standardized_problem_data)
    solution, solver_logs = solver.solve(max_iterations=max_iterations)
    overall_logs.extend(solver_logs)

    # Bước 3: Điều chỉnh lại giá trị hàm mục tiêu nếu bài toán gốc là Maximize
    if solution and solution.get("status") == "Optimal" and was_maximized:
        if solution.get("objective_value") is not None:
            solution["objective_value"] *= -1
            overall_logs.append(f"Final objective value (for original MAX problem) adjusted: {solution['objective_value']:.4g}")
        else: # Thêm trường hợp giá trị mục tiêu là None mặc dù status là Optimal
             overall_logs.append(f"Warning: Solution status is Optimal but objective_value is None. Cannot adjust for original MAX problem.")


    elif solution and solution.get("status") == "Unbounded" and was_maximized:
        # Nếu bài toán min -Z không bị chặn dưới (tiến tới -vô cùng),
        # thì bài toán max Z không bị chặn trên (tiến tới +vô cùng).
        # Trạng thái "Unbounded" vẫn giữ nguyên.
        overall_logs.append("Original MAX problem is also Unbounded.")
    
    overall_logs.append("--- solve_with_simple_dictionary finished ---")
    return solution, overall_logs

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Test với bài toán gốc là MAX, sẽ được chuẩn hóa thành MIN
    problem_to_standardize_max = {
        "objective": "max",
        "coeffs": [3, 5], # Maximize 3x1 + 5x2
        "variables_names_for_title_only": ["x1", "x2"],
        "constraints": [
            {"name": "c1", "lhs": [1, 0], "op": "<=", "rhs": 4},       # x1 <= 4
            {"name": "c2", "lhs": [0, 2], "op": "<=", "rhs": 12},      # 2x2 <= 12 => x2 <= 6
            {"name": "c3", "lhs": [3, 2], "op": "<=", "rhs": 18}       # 3x1 + 2x2 <= 18
            # Lời giải: x1=2, x2=6, Z_max=36. Khi min, -Z_min = -36
        ]
    }
    print("--- Test 1: Solving MAX problem (will be standardized to MIN) ---")
    solution1, logs1 = solve_with_simple_dictionary(problem_to_standardize_max, max_iterations=10)
    print("\n--- FULL LOGS (Test 1) ---")
    for log_entry in logs1: print(log_entry)
    print("\n--- FINAL SOLUTION (Test 1) ---")
    if solution1: import json; print(json.dumps(solution1, indent=2))


    # Test với bài toán gốc là MIN và có ràng buộc >=
    problem_to_standardize_min_geq = {
        "objective": "min",
        "coeffs": [1, 1], # Min x1 + x2
        "variables_names_for_title_only": ["x1", "x2"],
        "constraints": [
            {"name": "c1", "lhs": [1, 1], "op": ">=", "rhs": 2},       # x1 + x2 >= 2  => -x1 -x2 <= -2
            {"name": "c2", "lhs": [1, 0], "op": "<=", "rhs": 3},       # x1 <= 3
            {"name": "c3", "lhs": [0, 1], "op": "<=", "rhs": 3}        # x2 <= 3
            # Lời giải: x1=1, x2=1, Z_min=2 (ví dụ) hoặc x1=0, x2=2 or x1=2, x2=0
        ]
    }
    print("\n\n--- Test 2: Solving MIN problem with GEQ constraint ---")
    solution2, logs2 = solve_with_simple_dictionary(problem_to_standardize_min_geq, max_iterations=10)
    print("\n--- FULL LOGS (Test 2) ---")
    for log_entry in logs2: print(log_entry)
    print("\n--- FINAL SOLUTION (Test 2) ---")
    if solution2: import json; print(json.dumps(solution2, indent=2))

    # Test với bài toán có RHS âm (Pha 1 đơn giản sẽ được kích hoạt)
    # min -3x1 - 2x2
    # 2x1 + x2 <= 2
    # -3x1 - 4x2 <= -12  (RHS âm)
    # x1,x2 >=0 được giả định bởi Simplex, không cần thêm tường minh cho SimpleDictSolver
    problem_b1_12_modified_for_simple_solver = {
        "objective": "min",
        "coeffs": [-3, -2],
        "variables_names_for_title_only": ["x1", "x2"],
        "constraints": [
            {"name": "RB1_prime", "lhs": [2, 1], "op": "<=", "rhs": 2},
            {"name": "RB2_prime", "lhs": [-3, -4], "op": "<=", "rhs": -12}
        ]
    }
    print("\n\n--- Test 3: Solving Problem (Bài 1.12) with negative RHS ---")
    solution3, logs3 = solve_with_simple_dictionary(problem_b1_12_modified_for_simple_solver, max_iterations=10)
    print("\n--- FULL LOGS (Test 3) ---")
    for log_entry in logs3: print(log_entry)
    print("\n--- FINAL SOLUTION (Test 3) ---")
    if solution3: import json; print(json.dumps(solution3, indent=2))


    # Test với bài toán không bị chặn
    # Min -x1 - x2 (Tương đương Max x1+x2)
    # s.t. -x1 + x2 <= 1  (x2 <= 1 + x1)
    #      x1 - x2 <= 1  (x1 <= 1 + x2)
    #      x1, x2 >= 0
    # Bài này Max sẽ không bị chặn. Vậy Min (-x1-x2) sẽ không bị chặn dưới.
    problem_unbounded_min = {
        "objective": "min",
        "coeffs": [-1, -1],
        "variables_names_for_title_only": ["x1", "x2"],
        "constraints": [
            {"name": "c1", "lhs": [-1, 1], "op": "<=", "rhs": 1},
            {"name": "c2", "lhs": [1, -1], "op": "<=", "rhs": 1},
            # Thêm x1 >= 0 => -x1 <= 0
            {"name": "c3_x1_non_neg", "lhs": [-1, 0], "op": "<=", "rhs": 0},
            # Thêm x2 >= 0 => -x2 <= 0
            {"name": "c4_x2_non_neg", "lhs": [0, -1], "op": "<=", "rhs": 0},
        ]
    }
    # Nếu không có ràng buộc x1,x2 >=0, nó có thể tìm ra nghiệm khác.
    # Để SimpleDictionarySolver hoạt động đúng, các ràng buộc phi âm cũng cần được chuyển thành <=.
    # standardize_problem_for_simplex sẽ làm điều đó nếu chúng được cung cấp là ">=".

    print("\n\n--- Test 4: Solving Unbounded Problem (Min -x1-x2) ---")
    # Bài toán gốc là Max x1+x2, s.t. -x1+x2<=1, x1-x2<=1, x1,x2>=0 (Unbounded)
    # Chuyển thành Min -x1-x2, s.t. -x1+x2<=1, x1-x2<=1, x1>=0, x2>=0
    # Hàm standardize sẽ không đổi mục tiêu, nhưng sẽ đổi x1>=0 thành -x1<=0, và x2>=0 thành -x2<=0.
    problem_for_unbounded_test = {
        "objective": "max", # Sẽ được standardize thành min
        "coeffs": [1,1],
        "variables_names_for_title_only": ["x1", "x2"],
        "constraints": [
            {"name": "c1", "lhs": [-1, 1], "op": "<=", "rhs": 1},
            {"name": "c2", "lhs": [1, -1], "op": "<=", "rhs": 1},
            {"name": "nonneg_x1", "lhs": [1,0], "op": ">=", "rhs": 0}, # sẽ thành -x1 <= 0
            {"name": "nonneg_x2", "lhs": [0,1], "op": ">=", "rhs": 0}, # sẽ thành -x2 <= 0
        ]
    }
    solution4, logs4 = solve_with_simple_dictionary(problem_for_unbounded_test, max_iterations=10)
    print("\n--- FULL LOGS (Test 4 Unbounded) ---")
    for log_entry in logs4: print(log_entry)
    print("\n--- FINAL SOLUTION (Test 4 Unbounded) ---")
    if solution4: import json; print(json.dumps(solution4, indent=2))

