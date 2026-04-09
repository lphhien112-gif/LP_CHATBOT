# /app/solver/base_simplex_dictionary_solver.py
import logging
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseSimplexDictionarySolver(ABC):
    """
    Lớp cơ sở cho các bộ giải Simplex sử dụng phương pháp từ điển.
    Cung cấp logic xoay chung và triển khai quy tắc Bland mặc định cho việc chọn biến.
    Lớp này mong đợi problem_data đầu vào đã được chuẩn hóa bởi hàm bao bọc:
    - "objective": "min"
    - "coeffs": list of objective coefficients for the "min" problem
    - "variables_names_for_title_only": ordered list of variable names
    - "constraints": list of constraints, where each constraint.op is "<="
                     (nếu solver này chỉ xử lý biến bù đơn giản).
    """
    def __init__(self, problem_data_standardized: Dict[str, Any], objective_key_in_dict: str = 'z_obj'):
        self.problem_data: Dict[str, Any] = problem_data_standardized # Dữ liệu đã được chuẩn hóa
        self.logs: List[str] = []
        self.step_by_step_md: List[str] = [] # Lưu trữ lời giải từng bước dạng Markdown/LaTeX

        # Dữ liệu đầu vào đã được chuẩn hóa, nên objective sẽ là "min"
        self.current_objective_type: str = self.problem_data.get("objective", "min").lower()
        if self.current_objective_type != "min":
            # This should ideally not happen if data is pre-standardized by the wrapper
            self._log(f"CRITICAL WARNING: BaseSimplexDictionarySolver received non-minimization problem type '{self.current_objective_type}' despite expecting standardized input. Proceeding as minimization.")
            self.current_objective_type = "min"

        # objective_coeffs_list là hệ số của hàm "min" (đã có thể bị nhân -1 nếu gốc là max)
        self.objective_coeffs_list: List[float] = self.problem_data.get("coeffs", [])
        self.decision_vars_names: List[str] = list(self.problem_data.get("variables_names_for_title_only", []))

        if not self.decision_vars_names and self.objective_coeffs_list:
            self.decision_vars_names = [f"x{i+1}" for i in range(len(self.objective_coeffs_list))]
            self._log(f"Warning: No variable names provided to BaseSimplex, auto-generating: {self.decision_vars_names}")
        elif len(self.decision_vars_names) != len(self.objective_coeffs_list):
            self._log(f"ERROR: Mismatch between variable names ({len(self.decision_vars_names)}) and objective coeffs ({len(self.objective_coeffs_list)}) in BaseSimplex.")
            # Consider raising an error here if strictness is required

        self.iteration_count: int = 0
        self.dictionary: Dict[str, Dict[str, float]] = {}

        self.slack_vars_names: List[str] = []
        self.surplus_vars_names: List[str] = [] # Thường không dùng nếu ràng buộc đã là <=
        self.artificial_vars_names: List[str] = [] # Thường được xử lý bởi solver chuyên biệt hơn

        self.all_vars_ordered: List[str] = []
        self.basic_vars: List[str] = []
        self.non_basic_vars: List[str] = []
        self.epsilon: float = 1e-9
        self.current_objective_key: str = objective_key_in_dict

        self._build_initial_dictionary_common_setup()

    def _log(self, message: str, print_to_console: bool = False):
        self.logs.append(message)
        if print_to_console: # For debugging during development
            logger.info(f"BaseSimplex: {message}")


    def _format_expr(self, expr_dict: Dict[str, float]) -> str:
        parts = []
        const_val = expr_dict.get('const', 0.0)
        # Hiển thị hằng số nếu nó khác 0 hoặc nếu không có biến nào khác trong biểu thức
        if abs(const_val) > self.epsilon or not any(abs(val) > self.epsilon for name, val in expr_dict.items() if name != 'const'):
            parts.append(f"{const_val:.4g}")

        # Sắp xếp các biến để hiển thị nhất quán
        sorted_vars = sorted(
            [var for var in expr_dict if var != 'const' and abs(expr_dict[var]) > self.epsilon],
            key=lambda v_name: self.all_vars_ordered.index(v_name) if v_name in self.all_vars_ordered else float('inf')
        )

        for var_name in sorted_vars:
            coeff = expr_dict[var_name]
            abs_coeff = abs(coeff)
            current_sign = "-" if coeff < 0 else "+"
            
            term_str = ""
            if abs(abs_coeff - 1.0) < self.epsilon: # Hệ số là 1 hoặc -1
                term_str = var_name
            else:
                term_str = f"{abs_coeff:.4g}{var_name}"

            if not parts or (len(parts) == 1 and (parts[0].strip() == "0" or parts[0].strip() == "0.0")): # Nếu phần tử đầu tiên là 0
                 parts = [f"{current_sign.strip()}{term_str}"] if current_sign == "-" else [term_str]
            else:
                parts.append(f" {current_sign} {term_str}")
        
        if not parts: return "0"
        result = "".join(parts).strip() # Dùng join rỗng rồi strip
        if result.startswith("+") and len(result) > 1: # Bỏ dấu + ở đầu nếu có
            result = result[1:].strip()
        return result


    def _log_dictionary(self, phase_info: Optional[str] = None):
        phase_str = f" ({phase_info})" if phase_info else ""
        obj_key_display = self.current_objective_key
        # self.current_objective_type đã được đặt là "min" trong __init__
        log_str = f"--- Iteration {self.iteration_count}{phase_str} ---\nCurrent Dictionary (Objective: {self.current_objective_type} {obj_key_display}):\n"
        
        if obj_key_display in self.dictionary:
            log_str += f"{obj_key_display} = {self._format_expr(self.dictionary[obj_key_display])}\n"
        else:
            log_str += f"{obj_key_display} = [Not yet fully defined in dictionary]\n"


        sorted_basic_vars_for_log = sorted(
            [bv for bv in self.basic_vars if bv in self.dictionary and bv != obj_key_display],
            key=lambda v: self.all_vars_ordered.index(v) if v in self.all_vars_ordered else float('inf')
        )

        for var_name in sorted_basic_vars_for_log:
            log_str += f"{var_name} = {self._format_expr(self.dictionary[var_name])}\n"
        
        # Log các biến cơ sở không tìm thấy trong dictionary (nếu có, để debug)
        for var_name in self.basic_vars:
            if var_name != obj_key_display and var_name not in self.dictionary :
                 self._log(f"Warning: Basic variable '{var_name}' is in self.basic_vars but not found in self.dictionary during logging.")

        self._log(log_str)

    def _format_var_latex(self, var_name: str) -> str:
        import re
        match = re.match(r"^([a-zA-Z]+)(\d+)$", var_name)
        if match:
            return f"{match.group(1)}_{{{match.group(2)}}}"
        return var_name

    def _format_expr_latex(self, expr_dict: Dict[str, float], highlight_var: Optional[str] = None) -> str:
        parts = []
        const_val = expr_dict.get('const', 0.0)
        
        if abs(const_val) > self.epsilon or not any(abs(val) > self.epsilon for name, val in expr_dict.items() if name != 'const'):
            parts.append(f"{const_val:g}".replace('.', ','))

        sorted_vars = sorted(
            [var for var in expr_dict if var != 'const' and abs(expr_dict[var]) > self.epsilon],
            key=lambda v_name: self.all_vars_ordered.index(v_name) if v_name in self.all_vars_ordered else float('inf')
        )

        for var_name in sorted_vars:
            coeff = expr_dict[var_name]
            abs_coeff = abs(coeff)
            current_sign = "-" if coeff < 0 else "+"
            
            formatted_var = self._format_var_latex(var_name)
            is_highlight = (highlight_var and var_name == highlight_var)
            
            coeff_str = f"{abs_coeff:g}".replace('.', ',')
            
            term_str = ""
            if abs(abs_coeff - 1.0) < self.epsilon:
                term_str = formatted_var
            else:
                term_str = f"{coeff_str}{formatted_var}"

            if not parts or (len(parts) == 1 and parts[0] in ["0", "0,0"]):
                 sign_str = current_sign if current_sign == "-" else ""
                 if is_highlight:
                     # Mũi tên ↓ đặt trực tiếp lên biến (không phải dấu -)
                     term_str = f"\\overset{{\\downarrow}}{{{term_str}}}"
                 
                 parts = [f"{sign_str}{term_str}".strip()]
            else:
                sign_str = current_sign
                if is_highlight:
                    # Mũi tên ↓ trực tiếp trên biến, dấu ± riêng
                    term_str = f"\\overset{{\\downarrow}}{{{term_str}}}"
                parts.append(f" {sign_str} {term_str}")
        
        if not parts: return "0"
        result = "".join(parts).strip()
        if result.startswith("+ "): result = result[2:]
        return result

    def _get_objective_display_name(self) -> str:
        """Trả về tên hiển thị LaTeX cho objective key hiện tại."""
        mapping = {
            'z_obj': 'z',
            'z_bland': 'z',
            'z_original': 'z',
            'z_dual': 'z',
            'z_dp2p': 'z',
            'z_bt': 'z_{BT}',
            'f_aux': '\\xi',
        }
        return mapping.get(self.current_objective_key, 'z')

    def _generate_tableau_md(self, phase_info: Optional[str] = None, entering_var: Optional[str] = None, leaving_var: Optional[str] = None):
        """Tạo bảng Simplex Tableau dạng Markdown/LaTeX từ Dictionary hiện tại.
        Hỗ trợ đánh dấu biến vào (entering) và biến ra (leaving).
        """
        md = "\n\\[\n\\begin{array}{rrl}\n"
        
        # Dòng mục tiêu
        obj_key = self.current_objective_key
        obj_display = self._get_objective_display_name()
        if obj_key in self.dictionary:
            base_expr_str = self._format_expr_latex(self.dictionary[obj_key], highlight_var=entering_var)
            
            md += f"& {obj_display} &= {base_expr_str} \\\\\n"
            md += "\\hline\n"
        else:
            md += f"& {obj_display} &= 0 \\\\\n"
            md += "\\hline\n"

        # Các dòng biến cơ sở
        sorted_basic = sorted(
            [bv for bv in self.basic_vars if bv in self.dictionary and bv != obj_key],
            key=lambda v: self.all_vars_ordered.index(v) if v in self.all_vars_ordered else float('inf')
        )
        
        ratio_details = getattr(self, 'latest_ratio_details', {}) if entering_var else {}

        for bv in sorted_basic:
            expr_str = self._format_expr_latex(self.dictionary[bv])
            formatted_bv = self._format_var_latex(bv)
            prefix = "\\leftarrow" if (leaving_var and bv == leaving_var) else ""
            
            ratio_str = ""
            if bv in ratio_details:
                const_val, coeff_val, ratio_val = ratio_details[bv]
                const_s = f"{const_val:g}".replace('.', ',')
                coeff_s = f"{coeff_val:g}".replace('.', ',')
                ratio_s = f"{ratio_val:g}".replace('.', ',')
                ratio_str = f" \\quad \\frac{{{const_s}}}{{{coeff_s}}} = {ratio_s}"
                
            md += f"{prefix} & {formatted_bv} &= {expr_str}{ratio_str} \\\\\n"
            
        md += "\\end{array}\n\\]\n"
        self.step_by_step_md.append(md)


    def _build_initial_dictionary_common_setup(self):
        # self.decision_vars_names được lấy từ problem_data_standardized["variables_names_for_title_only"]
        self.all_vars_ordered.extend(self.decision_vars_names)
        self.non_basic_vars = list(self.decision_vars_names) # Ban đầu tất cả biến quyết định là phi cơ sở

    def _build_standard_dictionary(self, obj_coeffs: Optional[List[float]] = None) -> bool:
        """
        Xây dựng từ vựng chuẩn: hàm mục tiêu z + biến bù w_i.
        Dùng chung cho simplex, bland, dual_simplex, dual_primal_two_phase.
        
        Args:
            obj_coeffs: Hệ số hàm mục tiêu. Nếu None, dùng self.objective_coeffs_list.
        """
        coeffs = obj_coeffs if obj_coeffs is not None else self.objective_coeffs_list

        # Hàm mục tiêu
        z_expr: Dict[str, float] = {'const': 0.0}
        for i, var_name in enumerate(self.decision_vars_names):
            if i < len(coeffs):
                z_expr[var_name] = coeffs[i]
        self.dictionary[self.current_objective_key] = z_expr

        # Ràng buộc → biến bù w_i
        constraints_from_input = self.problem_data.get("constraints", [])
        for i, constr in enumerate(constraints_from_input):
            if constr.get("op") not in ["<=", "≤"]:
                self._log(f"CRITICAL ERROR: Constraint '{constr.get('name', i+1)}' type '{constr.get('op')}' but expected '<='.")
                return False

            slack_var_name = f"w{i+1}"
            self.slack_vars_names.append(slack_var_name)
            if slack_var_name not in self.all_vars_ordered:
                self.all_vars_ordered.append(slack_var_name)
            self.basic_vars.append(slack_var_name)

            constr_expr: Dict[str, float] = {'const': constr.get("rhs", 0.0)}
            lhs_coeffs_list = constr.get("lhs", [])
            for j, var_name in enumerate(self.decision_vars_names):
                if j < len(lhs_coeffs_list):
                    constr_expr[var_name] = -lhs_coeffs_list[j]
            self.dictionary[slack_var_name] = constr_expr

        self._log(f"Variables ordered: {self.all_vars_ordered}")
        return True

    # --- Phase 1 đơn giản (dùng cho simplex, bland khi ∃ b_i < 0) ---

    def _find_leaving_var_phase1(self) -> Optional[str]:
        """Pha 1: Chọn biến cơ sở có hằng số âm nhất (Bland tie-break)."""
        most_negative_const = -self.epsilon
        candidates: List[str] = []
        for var_name in self.basic_vars:
            if var_name == self.current_objective_key:
                continue
            const_val = self.dictionary.get(var_name, {}).get('const', 0.0)
            if const_val < most_negative_const:
                most_negative_const = const_val
                candidates = [var_name]
            elif abs(const_val - most_negative_const) < self.epsilon and most_negative_const < -self.epsilon:
                candidates.append(var_name)
        if not candidates:
            return None
        candidates.sort(key=lambda v: self.all_vars_ordered.index(v))
        leaving = candidates[0]
        self._log(f"Phase 1 Leaving (Bland): {leaving} (const: {most_negative_const:.4g})")
        return leaving

    def _find_entering_var_phase1(self, leaving_var: str) -> Optional[str]:
        """Pha 1: Chọn biến vào cho leaving_var đã chọn (Bland)."""
        leaving_expr = self.dictionary.get(leaving_var)
        if leaving_expr is None:
            return None
        candidates: List[str] = []
        for var_name in self.non_basic_vars:
            if var_name not in self.all_vars_ordered:
                continue
            coeff = leaving_expr.get(var_name, 0.0)
            if coeff < -self.epsilon:
                candidates.append(var_name)
        if not candidates:
            self._log(f"Phase 1 ERROR: No entering var for {leaving_var}. Infeasible.")
            return None
        candidates.sort(key=lambda v: self.all_vars_ordered.index(v))
        entering = candidates[0]
        self._log(f"Phase 1 Entering (Bland): {entering} (coeff: {leaving_expr.get(entering, 0):.4g})")
        return entering

    def _run_phase1_simple(self, max_phase1_iterations: int, phase_label: str = "Phase 1") -> str:
        """Chạy Pha 1 đơn giản: lặp xoay đến khi mọi b_i >= 0."""
        self._log(f"--- Starting {phase_label} ---")
        phase1_iter = 0
        while phase1_iter < max_phase1_iterations:
            phase1_iter += 1
            self.iteration_count += 1
            self._log_dictionary(phase_info=phase_label)

            leaving = self._find_leaving_var_phase1()
            if leaving is None:
                self._generate_tableau_md(phase_info=phase_label)
                self._log(f"{phase_label}: Dictionary is feasible.")
                return "Feasible"

            entering = self._find_entering_var_phase1(leaving)
            if entering is None:
                self._generate_tableau_md(phase_info=phase_label, leaving_var=leaving)
                self._log(f"{phase_label}: Infeasible.")
                return "Infeasible"

            self._generate_tableau_md(phase_info=phase_label, entering_var=entering, leaving_var=leaving)

            if not self._perform_pivot(entering, leaving):
                return "ErrorInPivot"

        self._log(f"{phase_label}: Max iterations ({max_phase1_iterations}) reached.")
        return "MaxIterationsReached"

    # --- Dual Simplex methods (dùng cho dual_simplex, dual_primal_two_phase) ---

    def _select_leaving_var_dual(self) -> Optional[str]:
        """Dual Simplex: biến ra = dòng có b_i âm nhất."""
        most_negative = -self.epsilon
        leaving: Optional[str] = None
        sorted_basic = sorted(
            [bv for bv in self.basic_vars if bv in self.all_vars_ordered and bv != self.current_objective_key],
            key=lambda v: self.all_vars_ordered.index(v)
        )
        for bv in sorted_basic:
            const_val = self.dictionary.get(bv, {}).get('const', 0.0)
            if const_val < most_negative:
                most_negative = const_val
                leaving = bv
        if leaving:
            self._log(f"Dual — Biến ra: {leaving} (b = {most_negative:.4g})")
        return leaving

    def _select_entering_var_dual(self, leaving_var: str) -> Optional[str]:
        """Dual Simplex: biến vào = min{G_j / a_ij_original} với G >= 0 và a_ij_original > 0.
        Trong dict, coeff = -a_ij_original, nên cần coeff < 0."""
        leaving_expr = self.dictionary.get(leaving_var, {})
        obj_expr = self.dictionary.get(self.current_objective_key, {})
        best_ratio = float('inf')
        entering: Optional[str] = None

        sorted_nb = sorted(
            [nb for nb in self.non_basic_vars if nb in self.all_vars_ordered],
            key=lambda v: self.all_vars_ordered.index(v)
        )
        for var_name in sorted_nb:
            a_ij = leaving_expr.get(var_name, 0.0)
            g_j = obj_expr.get(var_name, 0.0)
            # coeff < 0 trong dict ↔ a_ij_original > 0
            if a_ij < -self.epsilon and g_j > -self.epsilon:
                ratio = g_j / (-a_ij)
                if ratio < best_ratio - self.epsilon:
                    best_ratio = ratio
                    entering = var_name
                elif abs(ratio - best_ratio) < self.epsilon and entering is None:
                    entering = var_name

        if entering:
            self._log(f"Dual — Biến vào: {entering} (ratio = {best_ratio:.4g})")
        else:
            self._log(f"Dual — Không tìm được biến vào cho {leaving_var}.")
        return entering

    @abstractmethod
    def _build_initial_dictionary(self) -> bool:
        """
        Xây dựng từ điển ban đầu từ self.problem_data (đã được chuẩn hóa).
        Phải được triển khai bởi lớp con.
        Lớp con sẽ thêm biến bù, biến nhân tạo nếu cần.
        """
        pass

    def _select_entering_variable(self) -> Optional[str]:
        """
        Chọn biến vào cơ sở theo Quy tắc Bland (mặc định).
        Vì hàm mục tiêu đã được chuẩn hóa thành "minimize", tìm hệ số âm nhất.
        """
        obj_expr = self.dictionary.get(self.current_objective_key)
        if obj_expr is None:
            self._log(f"ERROR: Objective key '{self.current_objective_key}' not found in dictionary for selecting entering variable.")
            return None

        candidate_entering_vars: List[str] = []
        # self.current_objective_type sẽ luôn là "min"
        for var_name in self.non_basic_vars: # Chỉ xét các biến phi cơ sở
            if var_name not in self.all_vars_ordered: continue # Đảm bảo biến có trong danh sách
            coeff = obj_expr.get(var_name, 0.0)
            if coeff < -self.epsilon: # Cho hàm min, tìm hệ số âm
                candidate_entering_vars.append(var_name)

        if not candidate_entering_vars:
            self._log(f"Optimality condition met for objective '{self.current_objective_key}' (minimize). No more candidates for entering variable.")
            return None

        # Quy tắc Bland: Chọn biến có chỉ số nhỏ nhất (theo thứ tự trong all_vars_ordered)
        candidate_entering_vars.sort(key=lambda v_name: self.all_vars_ordered.index(v_name))
        entering_var = candidate_entering_vars[0]

        coeff_val_in_obj = obj_expr.get(entering_var, 0.0)

        self._log(f"Selected Entering (Bland for Min Objective): {entering_var} (coeff in obj '{self.current_objective_key}': {coeff_val_in_obj:.4g}, index: {self.all_vars_ordered.index(entering_var)})")
        return entering_var

    def _select_leaving_variable(self, entering_var: str) -> Optional[str]:
        """Chọn biến ra khỏi cơ sở theo Quy tắc Bland (mặc định)."""
        min_ratio = float('inf')
        candidate_leaving_vars_for_min_ratio: List[str] = []

        self._log(f"Calculating ratios for entering variable '{entering_var}':")
        self.latest_ratio_details = {}

        # Sắp xếp các biến cơ sở để đảm bảo tính nhất quán khi chọn biến rời nếu có nhiều tỷ lệ bằng nhau (mặc dù Bland sẽ xử lý sau)
        sorted_basic_vars = sorted(
            [bv for bv in self.basic_vars if bv in self.all_vars_ordered],
            key=lambda v_name: self.all_vars_ordered.index(v_name)
            )

        for basic_var_name in sorted_basic_vars:
            if basic_var_name == self.current_objective_key: # Không cho hàm mục tiêu ra
                continue

            basic_var_expr = self.dictionary.get(basic_var_name)
            if basic_var_expr is None:
                self._log(f"Warning: Basic variable '{basic_var_name}' not in dictionary during leaving variable selection.")
                continue

            coeff_entering_in_row = basic_var_expr.get(entering_var, 0.0)

            # Chỉ xét khi hệ số của biến vào trong dòng ràng buộc là âm (để khi chia không đổi dấu bất đẳng thức)
            if coeff_entering_in_row < -self.epsilon:
                constant_term = basic_var_expr.get('const', 0.0)
                # Tỷ lệ: hằng số / (-hệ số của biến vào)
                ratio = constant_term / (-coeff_entering_in_row)

                # Chỉ xét tỷ lệ không âm (cho phép bằng 0 để xử lý suy biến)
                if ratio >= -self.epsilon: # Dùng -epsilon để bao gồm cả trường hợp bằng 0
                    self.latest_ratio_details[basic_var_name] = (constant_term, -coeff_entering_in_row, ratio)
                    self._log(f"  - Row '{basic_var_name}': const={constant_term:.4g}, coeff_entering={coeff_entering_in_row:.4g}, ratio = {ratio:.4g}")
                    if ratio < min_ratio - self.epsilon: # Tìm tỷ lệ nhỏ nhất
                        min_ratio = ratio
                        candidate_leaving_vars_for_min_ratio = [basic_var_name]
                    elif abs(ratio - min_ratio) < self.epsilon: # Nếu tỷ lệ bằng nhau, thêm vào danh sách ứng viên
                        candidate_leaving_vars_for_min_ratio.append(basic_var_name)
            # else: Nếu coeff_entering_in_row >= 0, biến vào không thể làm tăng giá trị biến cơ sở này (đối với min objective) hoặc làm nó âm.
            # Nếu coeff_entering_in_row > 0, tăng entering_var sẽ làm giảm basic_var_name. Không giới hạn.
            # Nếu coeff_entering_in_row = 0, entering_var không ảnh hưởng.

        if not candidate_leaving_vars_for_min_ratio:
            self._log(f"Problem may be UNBOUNDED (no non-negative ratios with negative coefficients for entering variable '{entering_var}').")
            return None

        # Quy tắc Bland: Nếu có nhiều biến cùng tỷ lệ nhỏ nhất, chọn biến có chỉ số nhỏ nhất
        candidate_leaving_vars_for_min_ratio.sort(key=lambda v_name: self.all_vars_ordered.index(v_name))
        leaving_var = candidate_leaving_vars_for_min_ratio[0]

        self._log(f"Selected Leaving (Bland): {leaving_var} (min_ratio: {min_ratio:.4g}, index: {self.all_vars_ordered.index(leaving_var)})")
        return leaving_var

    def _perform_pivot(self, entering_var: str, leaving_var: str) -> bool:
        self._log(f"Pivoting: Variable '{entering_var}' enters basis, '{leaving_var}' leaves basis.")
        
        if entering_var == leaving_var:
            self._log(f"ERROR: entering_var == leaving_var ('{entering_var}'). Cannot pivot."); return False
        
        # Kiểm tra leaving_var và entering_var có hợp lệ không
        if leaving_var not in self.dictionary:
            self._log(f"ERROR: Pivot error. Leaving var '{leaving_var}' not found in dictionary."); return False
        
        leaving_var_expr = self.dictionary[leaving_var] # Không pop() ở đây vội
        
        pivot_element_coeff = leaving_var_expr.get(entering_var)
        if pivot_element_coeff is None or abs(pivot_element_coeff) < self.epsilon:
            self._log(f"ERROR: Pivot element for '{entering_var}' in '{leaving_var}' row is zero or missing. Coeff: {pivot_element_coeff}");
            return False

        # 1. Xóa dòng của leaving_var khỏi từ điển (sẽ được thay thế bằng dòng của entering_var)
        self.dictionary.pop(leaving_var)

        # 2. Tạo dòng mới cho biến vào (entering_var)
        new_entering_var_expr: Dict[str, float] = {}
        # Hằng số: const_mới = const_cũ_dòng_rời / (-hệ_số_xoay)
        new_entering_var_expr['const'] = leaving_var_expr.get('const', 0.0) / (-pivot_element_coeff)
        # Biến rời trở thành phi cơ sở: coeff = 1 / hệ_số_xoay (toán học: -LV / -P = LV / P)
        new_entering_var_expr[leaving_var] = 1.0 / pivot_element_coeff
        # Các biến phi cơ sở khác trong dòng rời: coeff_mới = coeff_cũ / (-hệ_số_xoay)
        for var_name, coeff_val in leaving_var_expr.items():
            if var_name != 'const' and var_name != entering_var: # Không thêm chính entering_var
                new_entering_var_expr[var_name] = coeff_val / (-pivot_element_coeff)

        # 3. Cập nhật các dòng còn lại trong từ điển (bao gồm cả dòng mục tiêu)
        for other_basic_var_key in list(self.dictionary.keys()): # list() để tránh lỗi thay đổi dict khi lặp
            current_row_expr = self.dictionary[other_basic_var_key]
            # Lấy hệ số của entering_var trong dòng hiện tại (nếu có) và xóa nó khỏi biểu thức
            coeff_of_entering_in_current_row = current_row_expr.pop(entering_var, 0.0)

            if abs(coeff_of_entering_in_current_row) > self.epsilon: # Nếu entering_var có mặt trong dòng này
                # Cập nhật hằng số: const_mới = const_cũ + coeff_entering_cũ_dòng_này * const_dòng_xoay_mới
                current_row_expr['const'] = current_row_expr.get('const', 0.0) + \
                                           coeff_of_entering_in_current_row * new_entering_var_expr['const']
                # Cập nhật các hệ số khác dựa trên dòng pivot mới (new_entering_var_expr)
                for var_in_new_expr, coeff_in_new_expr in new_entering_var_expr.items():
                    if var_in_new_expr != 'const': # Chỉ xử lý các biến, không phải hằng số
                        current_row_expr[var_in_new_expr] = current_row_expr.get(var_in_new_expr, 0.0) + \
                                                            coeff_of_entering_in_current_row * coeff_in_new_expr
        
        # 4. Thêm dòng mới của entering_var vào từ điển
        self.dictionary[entering_var] = new_entering_var_expr

        # 5. Cập nhật danh sách biến cơ sở và phi cơ sở
        if leaving_var in self.basic_vars: self.basic_vars.remove(leaving_var)
        if entering_var not in self.basic_vars: self.basic_vars.append(entering_var)
        
        if entering_var in self.non_basic_vars: self.non_basic_vars.remove(entering_var)
        if leaving_var not in self.non_basic_vars: self.non_basic_vars.append(leaving_var)
        
        # Sắp xếp lại basic_vars và non_basic_vars theo all_vars_ordered để log và xử lý nhất quán
        self.basic_vars.sort(key=lambda v: self.all_vars_ordered.index(v) if v in self.all_vars_ordered else float('inf'))
        self.non_basic_vars.sort(key=lambda v: self.all_vars_ordered.index(v) if v in self.all_vars_ordered else float('inf'))

        return True

    def _extract_solution(self, final_status: str) -> Dict[str, Any]:
        self._log(f"Extracting solution from final dictionary. Status: {final_status}")
        solution: Dict[str, Any] = {
            "status": final_status,
            "variables": {}, # Sẽ chỉ chứa các biến quyết định ban đầu
            "objective_value": None
        }

        # Lấy giá trị hàm mục tiêu từ từ điển nếu tối ưu
        if final_status == "Optimal" and self.current_objective_key in self.dictionary:
            solution["objective_value"] = self.dictionary[self.current_objective_key].get('const', 0.0)
        elif final_status == "Optimal" and self.current_objective_key not in self.dictionary:
             self._log(f"Warning: Status is Optimal but objective key '{self.current_objective_key}' not in dictionary. Objective value cannot be extracted from dictionary constant.")

        # Lấy giá trị cho các biến quyết định ban đầu
        for var_name in self.decision_vars_names:
            if var_name in self.basic_vars and var_name in self.dictionary:
                solution["variables"][var_name] = self.dictionary[var_name].get('const', 0.0)
            elif var_name in self.non_basic_vars: # Biến phi cơ sở có giá trị bằng 0
                solution["variables"][var_name] = 0.0
            else:
                # Biến quyết định không có trong cơ sở cũng không trong phi cơ sở
                # Điều này không nên xảy ra nếu all_vars_ordered được quản lý đúng
                # Có thể nó là biến không được sử dụng hoặc lỗi logic. Mặc định là 0.
                solution["variables"][var_name] = 0.0
                self._log(f"Warning: Decision variable '{var_name}' was not found in basic or non-basic lists during solution extraction. Defaulting its value to 0.")

        # Log thông tin
        if solution["objective_value"] is not None:
            self._log(f"Objective value from dictionary ({self.current_objective_key}) = {solution['objective_value']:.4g}")
        self._log("Final values for decision variables:")
        for var, val in solution["variables"].items(): self._log(f"  - {var} = {val:.4g}")
        
        def _append_conclusion_md():
            if solution["status"] == "Optimal":
                non_basic_zeros = []
                for var in self.non_basic_vars:
                    if var in self.all_vars_ordered:
                        non_basic_zeros.append(f"{self._format_var_latex(var)} = 0")
                basic_vals = []
                for var in self.basic_vars:
                    if var in self.all_vars_ordered and var != self.current_objective_key:
                        val = self.dictionary.get(var, {}).get('const', 0.0)
                        val_s = f"{val:g}".replace('.', ',')
                        basic_vals.append(f"{self._format_var_latex(var)} = {val_s}")
                
                all_vals_str = ", ".join(non_basic_zeros + basic_vals)
                
                obj_val_s = "0"
                if solution["objective_value"] is not None:
                    obj_val_s = f"{solution['objective_value']:g}".replace('.', ',')
                    
                md  = f"Cho $\\quad {all_vals_str}$\n\n"
                md += f"**Giá trị tối ưu:** $z = {obj_val_s}$\n\n"
                self.step_by_step_md.append(md)


        _append_conclusion_md()
        solution["step_by_step_md"] = self.step_by_step_md
        
        return solution

    @abstractmethod
    def solve(self, max_iterations: int) -> Tuple[Optional[Dict[str, Any]], List[str]]:
        """
        Phương thức chính để giải bài toán. Phải được triển khai bởi lớp con.
        Sẽ bao gồm logic cho các pha (nếu cần) và vòng lặp Simplex chính.
        """
        pass
