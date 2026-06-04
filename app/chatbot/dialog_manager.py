# /app/chatbot/dialog_manager.py
import logging
import json
import os
import re
import random
from typing import Dict, Any, List, Optional, AsyncGenerator
from pathlib import Path

from app.nlp import (
    parse_lp_problem_from_string,
    NlpParser,
    OpenAiClient
)
from app.solver.dispatcher import dispatch_solver

logger = logging.getLogger(__name__)

class DialogManager:
    def __init__(self, user_id: str = "default_user"):
        self.user_id = user_id
        self.logs: List[str] = []
        self.rule_based_nlp = NlpParser()
        self.lp_formula_parser = parse_lp_problem_from_string
        self.openai_client = OpenAiClient()
        self.sample_problems = self._load_sample_problems()
        self.reset_state()

    def _load_sample_problems(self) -> List[Dict[str, Any]]:
        """Tải các bài toán mẫu từ tệp JSON."""
        try:
            # Đường dẫn đến tệp JSON: app/nlp/data/sample_problems.json
            base_path = Path(__file__).resolve().parent.parent # app/ chatbot/ -> app/
            json_path = base_path / "nlp" / "data" / "sample_problems.json"
            
            with open(json_path, 'r', encoding='utf-8') as f:
                problems = json.load(f)
                self._log(f"Đã tải thành công {len(problems)} bài toán mẫu.")
                return problems
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self._log(f"Lỗi: Không thể tải tệp bài toán mẫu. {e}")
            return []

    def _log(self, message: str):
        entry = f"DM ({self.user_id}): {message}"
        self.logs.append(entry)
        logger.info(entry)

    def reset_state(self):
        """Reset trạng thái hội thoại về ban đầu."""
        self.state: Dict[str, Any] = {
            "history": [],
            "current_problem_definition": {}, # Dạng coeffs_map
            "last_solution_context": None, # Chứa cả problem, solution, logs
            "expectation": None, # Trạng thái chờ đợi hành động từ user
            "pending_action": None # Hành động đang chờ xác nhận
        }
        self._log("Trạng thái hội thoại đã được reset.")

    def _is_problem_defined(self, p: Optional[Dict] = None) -> bool:
        """Kiểm tra xem đã có bài toán hoàn chỉnh chưa."""
        if p is None:
            p = self.state.get("current_problem_definition", {})
        return bool(p and p.get("objective_type") and p.get("objective_coeffs_map"))

    @staticmethod
    def build_internal_from_structured(data: Dict[str, Any]) -> Dict[str, Any]:
        """Dựng internal_def (định dạng coeffs_map) từ dữ liệu FORM có cấu trúc —
        bỏ qua hoàn toàn parser/LLM để nhập chính xác 100%.

        data = {
          "objective_type": "maximize"|"minimize",
          "variables": ["x1","x2"],
          "objective_coeffs": [c1, c2, ...],
          "constraints": [{"coeffs": [...], "op": "<="|">="|"==", "rhs": r}, ...]
        }
        """
        variables = [str(v).strip() for v in data.get("variables", []) if str(v).strip()]
        if not variables:
            raise ValueError("Thiếu danh sách biến.")
        obj_coeffs = data.get("objective_coeffs", [])
        obj_map = {v: float(obj_coeffs[i]) for i, v in enumerate(variables) if i < len(obj_coeffs)}
        if not obj_map:
            raise ValueError("Thiếu hệ số hàm mục tiêu.")

        constraints = []
        for i, c in enumerate(data.get("constraints", [])):
            coeffs = c.get("coeffs", [])
            cmap = {v: float(coeffs[j]) for j, v in enumerate(variables) if j < len(coeffs)}
            op = str(c.get("op", "<=")).strip()
            if op not in ("<=", ">=", "=="):
                op = {"=": "==", "≤": "<=", "≥": ">="}.get(op, "<=")
            constraints.append({
                "name": f"c{i + 1}",
                "coeffs_map": cmap,
                "operator": op,
                "rhs": float(c.get("rhs", 0.0)),
            })

        objective_type = str(data.get("objective_type", "maximize")).strip().lower()
        if objective_type in ("max", "maximize"):
            objective_type = "maximize"
        elif objective_type in ("min", "minimize"):
            objective_type = "minimize"

        return {
            "objective_type": objective_type,
            "objective_coeffs_map": obj_map,
            "objective_variables_ordered": variables,
            "constraints": constraints,
        }

    # ── Chế độ Luyện tập (tutor) ───────────────────────────────────────────────
    @staticmethod
    def _gen_practice_problem() -> Dict[str, Any]:
        """Sinh ngẫu nhiên bài LP 2 biến, max với hệ số & vế phải DƯƠNG → luôn bị
        chặn, có nghiệm tối ưu hữu hạn > 0 (phù hợp để luyện tay)."""
        rng = random.Random()
        n_con = rng.choice([2, 3])
        return {
            "objective_type": "maximize",
            "variables": ["x1", "x2"],
            "objective_coeffs": [rng.randint(2, 9), rng.randint(2, 9)],
            "constraints": [
                {"coeffs": [rng.randint(1, 5), rng.randint(1, 5)], "op": "<=", "rhs": rng.randint(8, 30)}
                for _ in range(n_con)
            ],
        }

    def new_practice_problem(self) -> Dict[str, Any]:
        """Tạo một bài luyện tập mới: sinh đề, giải sẵn (giấu đáp án trong state),
        trả về phần hiển thị + danh sách biến để sinh viên nhập nghiệm.
        Ưu tiên đề có NGHIỆM NGUYÊN (dễ tính tay) — thử tối đa 25 lần."""
        from app.solver.dispatcher import dispatch_solver
        best = None
        for _ in range(25):
            problem = self._gen_practice_problem()
            internal = self.build_internal_from_structured(problem)
            fmt = self._convert_internal_to_solver_format(internal)
            sol, _ = dispatch_solver(problem_data=dict(fmt), solver_name="pulp_cbc")
            if not sol or sol.get("status") != "Optimal":
                continue
            zv = sol.get("objective_value")
            if zv is None or zv <= 0:
                continue
            record = (problem, internal, sol)
            vals = list(sol.get("variables", {}).values())
            nice = all(abs(v - round(v)) < 0.02 for v in vals) and abs(zv - round(zv)) < 0.02
            if nice:
                best = record
                break
            if best is None:
                best = record
        if best is None:
            # cực hiếm: fallback một đề mặc định khả thi
            problem = {"objective_type": "maximize", "variables": ["x1", "x2"],
                       "objective_coeffs": [3, 2],
                       "constraints": [{"coeffs": [1, 1], "op": "<=", "rhs": 4},
                                        {"coeffs": [1, 0], "op": "<=", "rhs": 3}]}
            internal = self.build_internal_from_structured(problem)
            sol, _ = dispatch_solver(problem_data=dict(self._convert_internal_to_solver_format(internal)), solver_name="pulp_cbc")
            best = (problem, internal, sol)

        problem, internal, sol = best
        self.state["practice"] = {
            "problem": problem,
            "internal": internal,
            "solution": {
                "status": (sol or {}).get("status"),
                "objective_value": (sol or {}).get("objective_value"),
                "variables": (sol or {}).get("variables", {}),
            },
        }
        return {
            "display_html": self._format_problem_summary(internal),
            "variables": problem["variables"],
        }

    def grade_practice(self, answers: Dict[str, Any]) -> Dict[str, Any]:
        """Chấm nghiệm sinh viên nhập so với đáp án đã giải sẵn, kèm lời giải mẫu."""
        pr = self.state.get("practice")
        if not pr:
            return {"error": "Chưa có bài luyện tập. Hãy tạo bài mới."}
        sol = pr["solution"]
        exp_vars = {k: v for k, v in sol.get("variables", {}).items() if not str(k).startswith("_")}
        exp_z = sol.get("objective_value")
        tol = 0.05  # nới dung sai để sinh viên làm tròn thoải mái

        def _f(v):
            try:
                return float(v)
            except (TypeError, ValueError):
                return 0.0

        var_results = {}
        all_ok = True
        for v, ev in exp_vars.items():
            gv = _f(answers.get(v))
            ok = abs(gv - float(ev)) <= tol
            var_results[v] = {"got": gv, "expected": float(ev), "ok": ok}
            all_ok = all_ok and ok
        gz = _f(answers.get("z"))
        z_ok = exp_z is not None and abs(gz - float(exp_z)) <= tol
        correct = all_ok and z_ok

        # Lời giải mẫu (đơn hình từng bước) để sinh viên đối chiếu
        from app.solver.algorithms.simplex import solve_with_simple_dictionary
        try:
            wsol, _ = solve_with_simple_dictionary(self._convert_internal_to_solver_format(pr["internal"]))
            steps = wsol.get("step_by_step_md", [])
        except Exception:
            steps = []

        return {
            "correct": correct,
            "z": {"got": gz, "expected": exp_z, "ok": z_ok},
            "variables": var_results,
            "solution_steps": steps,
        }

    @staticmethod
    def _is_non_negativity(c: Dict) -> bool:
        """True nếu ràng buộc là dạng phi âm 'x >= 0' (một biến, hệ số dương, vế phải 0).
        Đây là ràng buộc DẤU ngầm định của QHTT dạng chuẩn — mọi solver đã tự giả định
        x_i >= 0, nên không cần đưa vào hệ ràng buộc (tránh sinh biến bù thừa w_i và
        khớp với cách trình bày trong lecture)."""
        cm = {k: v for k, v in c.get("coeffs_map", {}).items() if abs(v) > 1e-9}
        if len(cm) != 1:
            return False
        coeff = next(iter(cm.values()))
        op = str(c.get("operator", ""))
        rhs = c.get("rhs", 0.0)
        return op in (">=", ">") and abs(rhs) < 1e-9 and coeff > 0

    def _convert_internal_to_solver_format(self, internal_def: Dict) -> Optional[Dict[str, Any]]:
        """Chuyển đổi từ định dạng coeffs_map nội bộ sang Định dạng A cho solver."""
        try:
            constraints_in = internal_def.get("constraints", [])
            # Biến quyết định: gộp từ hàm mục tiêu + TẤT CẢ ràng buộc (kể cả 'x >= 0')
            # để không đánh mất biến nào khỏi mô hình.
            all_vars = set(internal_def.get("objective_variables_ordered", []))
            for c in constraints_in:
                all_vars.update(c.get("coeffs_map", {}).keys())
            ordered_vars = sorted(list(all_vars))

            # Loại bỏ ràng buộc phi âm khỏi hệ ràng buộc của solver (ngầm định).
            functional = [c for c in constraints_in if not self._is_non_negativity(c)]

            return {
                "objective": internal_def["objective_type"],
                "coeffs": [internal_def["objective_coeffs_map"].get(v, 0.0) for v in ordered_vars],
                "variables_names_for_title_only": ordered_vars,
                "constraints": [{
                    "name": f"c{i+1}",
                    "lhs": [c["coeffs_map"].get(v, 0.0) for v in ordered_vars],
                    "op": c["operator"], "rhs": c["rhs"]
                } for i, c in enumerate(functional)]
            }
        except Exception as e:
            self._log(f"Lỗi khi chuyển đổi định dạng cho solver: {e}")
            return None

    def _detect_solver(self, text: str, default: str = "simple_dictionary") -> str:
        """Centralized solver detection from Vietnamese/English text.
        
        Available solvers:
          simple_dictionary  — Simplex cơ bản (đơn hình từ điển)
          simplex_bland     — Simplex quy tắc Bland
          auxiliary          — 2-pha (bài toán phụ trợ)
          dual_simplex       — Đối ngẫu Simplex
          dual_primal_two_phase — Đối ngẫu – Nguyên thủy 2 pha
          geometric          — Hình học (vẽ đồ thị)
          pulp_cbc           — PuLP CBC (chỉ kết quả cuối)
        """
        m = text.lower()
        # ── Order matters: check specific patterns BEFORE generic ones ──
        
        # 1. Dual-Primal Two Phase (most specific dual variant)
        if ("nguyên thủy" in m or "primal" in m or
            ("đối ngẫu" in m and ("2 pha" in m or "hai pha" in m or "two" in m))):
            return "dual_primal_two_phase"
        
        # 2. Dual Simplex
        if "đối ngẫu" in m or "dual" in m:
            return "dual_simplex"
        
        # 3. Two-phase / Auxiliary
        if ("2 pha" in m or "hai pha" in m or "2pha" in m or
            "two phase" in m or "two-phase" in m or
            "phụ trợ" in m or "auxiliary" in m or "bổ trợ" in m):
            return "auxiliary"
        
        # 4. Bland
        if "bland" in m:
            return "simplex_bland"
        
        # 5. Geometric — KHÔNG dùng "hình" trần vì nó nằm trong "đơn hình", "mô hình".
        #    Chỉ nhận các cụm rõ nghĩa hình học.
        if ("hình học" in m or "geometric" in m or "geo " in m or
            "vẽ" in m or "đồ thị" in m or "đồ_thị" in m):
            return "geometric"

        # 6. Simplex (basic) — must come AFTER bland/dual checks
        if "đơn hình" in m or "simplex" in m or "simple" in m:
            return "simple_dictionary"
        
        # 7. PuLP
        if "pulp" in m or "cbc" in m:
            return "pulp_cbc"
        
        return default

    def _map_solver_name(self, user_input: str) -> str:
        """Alias for backward compatibility."""
        return self._detect_solver(user_input)

    def _extract_log_chunk_for_step(self, step_number: int) -> Optional[str]:
        """Trích xuất khối log cho một iteration cụ thể."""
        context = self.state.get("last_solution_context")
        if not context: return None
        logs = context.get("logs", [])
        if not logs: return None

        log_str = "\n".join(logs)
        pattern = re.compile(rf"--- Iteration {step_number}[^\n]* ---\n(.*?)(?=\n--- Iteration|\Z)", re.DOTALL)
        match = pattern.search(log_str)
        
        if match:
            self._log(f"Đã tìm thấy log cho bước {step_number}.")
            return match.group(0).strip()
        else:
            self._log(f"Không tìm thấy log cho bước {step_number}.")
            return None

    # --- Các hàm xử lý (Handler Functions) ---

    async def _handle_intent_request_step_explanation(self, entities: Dict):
        """Xử lý yêu cầu giải thích một bước giải."""
        if not self.state.get("last_solution_context"):
            yield {"type": "complete", "result": self._finalize_response({"text_response": "Mình chưa có lời giải nào trong bộ nhớ để giải thích. Bạn hãy giải một bài toán trước nhé."})}
            return

        try:
            step_number = int(entities.get("step_number", "0"))
            if step_number <= 0: raise ValueError
        except (ValueError, TypeError):
            yield {"type": "complete", "result": self._finalize_response({"text_response": "Mình không hiểu bạn muốn giải thích bước nào. Vui lòng nói rõ, ví dụ: 'giải thích bước 2'."})}
            return

        log_chunk = self._extract_log_chunk_for_step(step_number)
        
        if not log_chunk:
            yield {"type": "complete", "result": self._finalize_response({"text_response": f"Mình không tìm thấy thông tin chi tiết cho bước {step_number} trong lần giải vừa rồi. Có thể bài toán được giải bằng phương pháp không có bước lặp, hoặc đã kết thúc sớm hơn."})}
            return
            
        # Streaming explanation
        explanation_full = ""
        async for chunk in self.openai_client.explain_simplex_step_stream(log_chunk):
            explanation_full += chunk
            yield {"type": "chunk", "content": chunk}
            
        yield {"type": "complete", "result": self._finalize_response({
            "text_response": explanation_full or "Xin lỗi, mình chưa thể giải thích bước này.",
            "allow_html": True,
            "suggestions": [f"Giải thích bước {step_number + 1}", "Trở về bài toán"]
        })}

    async def _handle_intent_request_specific_solver(self, entities: Dict, original_message: str = ""):
        """Xử lý yêu cầu giải bài toán với một solver cụ thể — giải ngay, không hỏi confirm."""
        if not self._is_problem_defined():
            yield {"type": "complete", "result": self._finalize_response({
                "text_response": "Mình chưa có bài toán nào để giải. Bạn vui lòng cung cấp bài toán trước nhé.",
                "suggestions": ["Giải bài toán mẫu"]
            })}
            return

        # Lấy tên solver từ entity; nếu rỗng thì fallback vào toàn bộ message gốc
        solver_name_entity = entities.get("solver_name", "")
        solver_to_use = self._map_solver_name(solver_name_entity or original_message)
        self._log(f"Giải ngay với solver: '{solver_to_use}' (entity='{solver_name_entity}')")

        async for event in self._solve_current_problem(solver_to_use):
            yield event


    async def _handle_list_sample_problems(self):
        """Liệt kê các bài toán mẫu cho người dùng chọn."""
        if not self.sample_problems:
            yield {"type": "complete", "result": self._finalize_response({"text_response": "Xin lỗi, mình chưa có sẵn bài toán mẫu nào cả."})}
            return
        
        response_lines = ["Mình có một vài bài toán mẫu đây, bạn muốn thử bài nào?"]
        suggestions = []
        for i, problem in enumerate(self.sample_problems):
            response_lines.append(f"<b>{i+1}. {problem['name']}</b>: {problem['story']}")
            suggestions.append(f"Chọn bài toán {i+1}")
            
        self.state["expectation"] = "awaiting_sample_choice"
        yield {"type": "complete", "result": self._finalize_response({
            "text_response": "<br>".join(response_lines),
            "allow_html": True,
            "suggestions": suggestions
        })}

    async def _handle_sample_choice(self, user_message: str):
        """Xử lý khi người dùng chọn một bài toán mẫu."""
        choice_match = re.search(r'\d+', user_message)
        
        if not choice_match:
            # User sent non-numeric input → exit awaiting_sample_choice, reroute to normal flow
            self.state['expectation'] = None
            # Yield a special marker so handle_message knows to re-process this message normally
            yield {"type": "_reroute"}
            return
        
        try:
            choice_index = int(choice_match.group(0)) - 1
            
            if 0 <= choice_index < len(self.sample_problems):
                chosen_problem = self.sample_problems[choice_index]
                self._log(f"Người dùng đã chọn bài toán mẫu: {chosen_problem['name']}")
                # Parse bài toán từ chuỗi và giải
                parsed_lp, _ = self.lp_formula_parser(chosen_problem['full_problem_string'])
                if not parsed_lp:
                    # Bài toán mẫu không parse được — báo lỗi thay vì gán None vào state
                    self._log(f"Lỗi: Không thể phân tích bài toán mẫu '{chosen_problem['name']}'.")
                    yield {"type": "complete", "result": self._finalize_response({
                        "text_response": f"Xin lỗi, dữ liệu bài toán mẫu '{chosen_problem['name']}' bị lỗi và không thể phân tích. Bạn vui lòng chọn bài toán khác hoặc tự nhập đề bài nhé."
                    })}
                    return
                self.state['current_problem_definition'] = parsed_lp
                self.state['expectation'] = None # Xóa trạng thái chờ
                # Dùng solver ưu tiên từ JSON để hiện step-by-step tableaus
                preferred_solver = chosen_problem.get('preferred_solver', 'simple_dictionary')
                async for event in self._solve_current_problem(preferred_solver):
                    yield event
                return
            else:
                suggestions = [f"Chọn bài toán {i+1}" for i in range(len(self.sample_problems))]
                yield {"type": "complete", "result": self._finalize_response({
                    "text_response": f"Vui lòng chọn số từ 1 đến {len(self.sample_problems)}.",
                    "suggestions": suggestions
                })}
        except (ValueError, IndexError):
            yield {"type": "complete", "result": self._finalize_response({"text_response": "Lựa chọn không hợp lệ. Bạn vui lòng chọn lại từ danh sách nhé."})}

    async def _solve_current_problem(self, solver_name: str, preamble: Optional[str] = None):
        """Hàm tổng hợp để giải bài toán hiện tại trong state."""
        internal_def = self.state["current_problem_definition"]
        solver_format = self._convert_internal_to_solver_format(internal_def)
        if not solver_format:
            yield {"type": "complete", "result": self._finalize_response({"text_response": "Rất tiếc, có lỗi khi chuẩn bị dữ liệu để giải.", "allow_html": False})}
            return

        self._log(f"Bắt đầu giải bằng solver '{solver_name}'...")
        # [PERFORMANCE FIX] Chạy tác vụ toán học nặng trên Threadpool để không chặn Event Loop (FastAPI)
        from starlette.concurrency import run_in_threadpool
        solution, logs = await run_in_threadpool(
            dispatch_solver, 
            solver_format, 
            solver_name=solver_name
        )
        
        # Lưu lại toàn bộ ngữ cảnh của lần giải này
        context = {"problem_definition": internal_def, "solution": solution, "logs": logs}
        self.state["last_solution_context"] = context

        response_parts = []
        if preamble: response_parts.append(f"<p>{preamble}</p>")
        response_parts.append(self._format_problem_summary(internal_def))
        summary_html = "".join(response_parts) + "\n\n"
        # Stream summary as HTML chunk
        yield {"type": "chunk", "content": summary_html}
        
        # Inject step-by-step tableaus (LaTeX \[...\] blocks + markdown conclusion)
        step_by_step_md = solution.get("step_by_step_md", []) if solution else []
        tableaus_md = ""
        if step_by_step_md:
            tableaus_md = "\n\n".join(step_by_step_md)
            self._log(f"Đã có {len(step_by_step_md)} bước Tableaus để hiển thị.")
            # Stream tableaus as raw markdown/LaTeX (will be rendered on complete)
            yield {"type": "chunk_escaped", "content": tableaus_md + "\n\n---\n\n"}
        
        # Streaming LLM Explanation
        llm_text = ""
        async for chunk in self.openai_client.format_solver_solution_stream(internal_def, solution):
            llm_text += chunk
            yield {"type": "chunk_escaped", "content": chunk}
        
        # Fallback if LLM failed
        if not llm_text:
             self._log("Fallback do gọi API LLM bị lỗi")
             fallback_html = self._format_solution_response(solution, solver_format, solver_name)
             yield {"type": "chunk", "content": fallback_html}
             llm_text = fallback_html
        
        # Image (if geometric solver)
        image_html = ""
        if solution and solution.get("plot_image_base64"):
             img_src = solution["plot_image_base64"]
             image_html = f"\n\n<div style='text-align: center;'><img src='{img_src}' alt='Biểu đồ' style='max-width: 100%; border-radius: 8px;' /></div>"
        
        # Suggestions — show ALL other solvers the user can switch to
        SOLVER_SUGGESTIONS = {
            "simple_dictionary": "Giải bằng đơn hình",
            "simplex_bland": "Dùng Bland",
            "auxiliary": "Giải bằng 2 pha",
            "dual_simplex": "Giải đối ngẫu",
            "dual_primal_two_phase": "Đối ngẫu-nguyên thủy",
            "geometric": "Giải bằng hình học",
        }
        suggestions = []
        if solution and solution.get("status") == "Optimal":
            if solver_name not in ["geometric"]:
                suggestions.append("Giải thích bước 1")
            for s_key, s_label in SOLVER_SUGGESTIONS.items():
                if s_key == solver_name:
                    continue
                # Geometric only for 2-variable problems
                if s_key == "geometric" and len(solver_format.get("variables_names_for_title_only", [])) != 2:
                    continue
                suggestions.append(s_label)
            suggestions.append("So sánh các phương pháp")
        suggestions.append("Bắt đầu bài toán mới")

        # Final assembled content: summary (HTML) + tableaus (LaTeX/MD) + LLM (MD) + image
        final_text = summary_html + tableaus_md
        if tableaus_md:
            final_text += "\n\n---\n\n"
        final_text += llm_text + image_html

        yield {"type": "complete", "result": self._finalize_response({
            "text_response": final_text,
            "problem_context": context,
            "allow_html": True,
            "suggestions": suggestions
        })}

    async def _handle_generate_exercise(self, user_message: str):
        """Sinh một bài tập LP mới qua LLM, parse và đặt làm bài toán hiện tại để
        người dùng có thể giải ngay."""
        if not self.openai_client.client:
            yield {"type": "complete", "result": self._finalize_response({
                "text_response": "Tính năng tạo bài tập cần kết nối AI (hiện chưa sẵn sàng). "
                                 "Bạn có thể chọn **bài toán mẫu** hoặc tự nhập đề nhé.",
                "suggestions": ["Giải bài toán mẫu", "Bắt đầu bài toán mới"],
            })}
            return

        exercise_text = await self.openai_client.generate_exercise(user_message)
        if not exercise_text:
            yield {"type": "complete", "result": self._finalize_response({
                "text_response": "Xin lỗi, mình chưa tạo được bài tập lúc này. Bạn thử lại nhé.",
                "suggestions": ["Tạo bài tập khác", "Giải bài toán mẫu"],
            })}
            return

        # Tách NGỮ CẢNH (văn xuôi) khỏi MÔ HÌNH hình thức. Chỉ parse phần hình thức
        # (từ "Maximize"/"Minimize") — nếu parse cả văn xuôi, parser sẽ bắt nhầm cụm
        # "tối đa hóa lợi nhuận" trong prose thành hàm mục tiêu (vd ra {'l': 1.0}).
        mk = re.search(r'(?i)\b(maximize|minimize)\b', exercise_text)
        context = exercise_text[:mk.start()].strip() if mk else ""
        formal = exercise_text[mk.start():].strip() if mk else exercise_text
        parsed_lp, _ = self.lp_formula_parser(formal)

        display = "📝 **Bài tập luyện tập mới:**\n\n"
        if parsed_lp:
            self.state['current_problem_definition'] = parsed_lp
            self.state['expectation'] = None
            suggestions = ["Giải bằng đơn hình", "Giải bằng hình học", "Tạo bài tập khác"]
            # Hiển thị ngữ cảnh + mô hình ĐÃ CHUẨN HÓA (đồng nhất, tránh LLM viết "10×1").
            if context:
                display += context + "\n\n"
            display += self._format_problem_summary(parsed_lp)
            allow_html = True
        else:
            self._log("Không parse được bài tập vừa sinh — vẫn hiển thị text thô.")
            suggestions = ["Tạo bài tập khác", "Bắt đầu bài toán mới"]
            display += exercise_text
            allow_html = False

        yield {"type": "complete", "result": self._finalize_response({
            "text_response": display,
            "suggestions": suggestions,
            "allow_html": allow_html,
        })}

    async def _handle_compare_methods(self):
        """So sánh kết quả của nhiều phương pháp giải trên cùng bài toán hiện tại."""
        internal = self.state.get("current_problem_definition")
        if not internal:
            yield {"type": "complete", "result": self._finalize_response({
                "text_response": "Bạn cần nhập hoặc chọn một bài toán trước khi so sánh các phương pháp nhé.",
                "suggestions": ["Nhập bài toán mẫu", "Tạo bài tập"],
            })}
            return

        solver_format = self._convert_internal_to_solver_format(internal)
        if not solver_format:
            yield {"type": "complete", "result": self._finalize_response({
                "text_response": "Rất tiếc, có lỗi khi chuẩn bị dữ liệu để so sánh.",
            })}
            return

        from starlette.concurrency import run_in_threadpool
        n_vars = len(solver_format.get("variables_names_for_title_only", []))
        methods = [
            ("simple_dictionary", "Đơn hình (từ điển)"),
            ("simplex_bland", "Đơn hình Bland"),
            ("auxiliary", "Hai pha"),
            ("dual_simplex", "Đối ngẫu"),
            ("dual_primal_two_phase", "Hai pha đối ngẫu"),
            ("geometric", "Hình học"),
            ("pulp_cbc", "PuLP CBC"),
        ]
        rows = []
        opt_values = []
        for skey, slabel in methods:
            if skey == "geometric" and n_vars != 2:
                rows.append((slabel, "Không áp dụng (chỉ 2 biến)", "—"))
                continue
            try:
                sol, _ = await run_in_threadpool(dispatch_solver, dict(solver_format), solver_name=skey)
            except Exception as e:
                self._log(f"So sánh: solver '{skey}' lỗi: {e}")
                rows.append((slabel, "Lỗi", "—"))
                continue
            status = (sol or {}).get("status", "—")
            obj = (sol or {}).get("objective_value")
            if status == "Optimal" and obj is not None:
                opt_values.append(round(float(obj), 4))
                rows.append((slabel, "Tối ưu", f"{obj:g}".replace('.', ',')))
            else:
                # NotDualFeasible của dual_simplex trên bài không phù hợp là ĐÚNG (không phải lỗi)
                nice = {"NotDualFeasible": "Không phù hợp (cần dual-feasible)",
                        "Infeasible": "Vô nghiệm", "Unbounded": "Không giới nội"}.get(status, status)
                rows.append((slabel, nice, "—"))

        table = "## So sánh các phương pháp giải\n\n"
        table += "| Phương pháp | Trạng thái | Giá trị tối ưu $z^{*}$ |\n|---|---|---|\n"
        for label, status, val in rows:
            table += f"| {label} | {status} | {val} |\n"

        distinct = set(opt_values)
        if len(distinct) == 1 and opt_values:
            table += f"\n✅ Các phương pháp áp dụng được đều cho cùng nghiệm tối ưu $z^{{*}} = {f'{opt_values[0]:g}'.replace('.', ',')}$ — kết quả nhất quán."
        elif len(distinct) > 1:
            table += "\n⚠️ Có chênh lệch giữa các phương pháp — cần kiểm tra lại đề bài."

        yield {"type": "complete", "result": self._finalize_response({
            "text_response": table,
            "allow_html": False,
            "suggestions": ["Giải bằng đơn hình", "Giải bằng hình học", "Bắt đầu bài toán mới"],
        })}

    async def handle_message(self, user_message: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Hàm chính điều phối luồng hội thoại (async generator, yield từng event)."""
        self._log(f"Đang xử lý tin nhắn: '{user_message}' (Trạng thái chờ: {self.state['expectation']})")
        self.state["history"].append({"role": "user", "content": user_message})

        # Ưu tiên 1: Xử lý theo trạng thái chờ mong đợi
        if self.state["expectation"] == "awaiting_confirmation":
            self.state["expectation"] = None # Reset trạng thái chờ
            if "không" in user_message.lower() or "thôi" in user_message.lower():
                self.state["pending_action"] = None
                yield {"type": "complete", "result": self._finalize_response({"text_response": "Được rồi, nếu bạn cần gì khác cứ nói nhé!", "suggestions": ["Bắt đầu bài toán mới"]})}
                return
            else: # Mặc định là đồng ý
                pending = self.state.pop("pending_action")
                if pending and pending['action'] == 'solve':
                    async for event in self._solve_current_problem(pending['solver']):
                        yield event
                    return

        if self.state["expectation"] == "awaiting_sample_choice":
            rerouted = False
            async for event in self._handle_sample_choice(user_message):
                if event.get("type") == "_reroute":
                    rerouted = True
                    break  # Don't return — fall through to normal flow below
                yield event
            if not rerouted:
                return

        # Ưu tiên 2: Các lệnh đặc biệt
        if user_message.lower() in ["bắt đầu lại", "reset", "làm mới", "bài toán mới"]:
             self.reset_state()
             yield {"type": "complete", "result": self._finalize_response({"text_response": "Đã làm mới! Mình có thể giúp gì cho bạn tiếp theo?", "suggestions": ['Giải bài toán mẫu', 'Kể một câu chuyện bài toán', 'Biến bù là gì?']})}
             return
        
        if "bài toán mẫu" in user_message.lower():
             async for event in self._handle_list_sample_problems():
                 yield event
             return

        # Tạo bài tập mới (sinh đề luyện tập). Tránh nhầm với "bài toán mẫu" (danh sách mẫu).
        _m_low = user_message.lower()
        if ("bài tập" in _m_low or "ra đề" in _m_low or "tạo đề" in _m_low) and "mẫu" not in _m_low:
             async for event in self._handle_generate_exercise(user_message):
                 yield event
             return

        # So sánh các phương pháp giải trên bài toán hiện tại
        if ("so sánh" in _m_low) and self._is_problem_defined():
             async for event in self._handle_compare_methods():
                 yield event
             return
        
        if "câu chuyện" in user_message.lower():
             self.state['expectation'] = 'awaiting_story'
             yield {"type": "complete", "result": self._finalize_response({"text_response": "Tuyệt vời! Hãy kể cho mình nghe vấn đề của bạn bằng ngôn ngữ tự nhiên nhé. Mình sẽ cố gắng chuyển nó thành một bài toán LP."})}
             return
        
        if self.state['expectation'] == 'awaiting_story':
             # Xử lý câu chuyện... (Logic này có thể được thêm vào sau)
             pass

        # Ưu tiên 2b: SHORTCUT cho yêu cầu giải bằng solver cụ thể khi đã có bài toán
        # Bắt sớm trước lp_parser để tránh rơi vào pipeline parse → LLM → NLP intent
        _SOLVER_REQUEST_RE = re.compile(
            r"(giải\s*(bằng|lại\s*bằng|cho\s*tôi\s*bằng|theo)?\s*"
            r"|dùng\s*|sử\s*dụng\s*|thử\s*|chuyển\s*(sang)?\s*"
            r"|vẽ\s*(hình|đồ\s*thị)?\s*"
            r"|phương\s*pháp\s*)"
            r"(đơn\s*hình|simplex|bland|2\s*pha|hai\s*pha|two.?phase|đối\s*ngẫu|dual"
            r"|nguyên\s*thủy|primal|hình\s*học|geo|phụ\s*trợ|auxiliary|bổ\s*trợ|pulp|cbc)",
            re.IGNORECASE
        )
        if _SOLVER_REQUEST_RE.search(user_message) and self._is_problem_defined():
            detected = self._detect_solver(user_message, default=None)
            if detected:
                self._log(f"Shortcut: solver '{detected}' từ '{user_message}'")
                async for event in self._solve_current_problem(detected):
                    yield event
                return

        _LP_KEYWORDS = re.compile(
            r"(maximiz|minimiz|tối đa|tối thiểu|maximize|minimize|subject to|ràng buộc|lợi nhuận|chi phí|lợi suất|hàm mục tiêu)",
            re.IGNORECASE
        )

        # Ưu tiên 3: Phân tích bài toán LP
        # Chiến lược: tin nhắn NGẮN (<120 ký tự) → lp_parser trước (giỏi parse math notation)
        #             tin nhắn DÀI (≥120 ký tự, story) → LLM extraction trước (tránh parse sai biến)
        is_story_like = len(user_message) >= 120 and _LP_KEYWORDS.search(user_message)

        if is_story_like and self.openai_client.client:
            # ── PATH A: Story/câu chuyện → LLM extraction trước ──
            self._log(f"Tin nhắn dài ({len(user_message)} chars) + LP keywords → dùng LLM extraction trước")
            yield {"type": "chunk", "content": "<p><i>🔍 Đang nhận diện bài toán từ mô tả tự nhiên...</i></p>"}
            
            structured_text = await self.openai_client.extract_lp_as_structured(user_message)
            if structured_text:
                self._log(f"LLM returned structured LP:\n{structured_text}")
                parsed_lp, logs = self.lp_formula_parser(structured_text)
                if parsed_lp and self._is_problem_defined(parsed_lp):
                    self._log("LLM extraction → lp_parser: THÀNH CÔNG!")
                    self.state["current_problem_definition"] = parsed_lp
                    solver_to_use = self._detect_solver(user_message)
                    self._log(f"Story solver: '{solver_to_use}'")
                    async for event in self._solve_current_problem(solver_to_use):
                        yield event
                    return
                else:
                    self._log(f"LLM extraction → lp_parser thất bại. Logs: {logs}")
            
            # Fallback: thử lp_parser trực tiếp (có thể story chứa math notation rõ ràng)
            parsed_lp, parse_logs = self.lp_formula_parser(user_message)
            if parsed_lp and self._is_problem_defined(parsed_lp):
                # Validate: bài toán phải có ít nhất 1 constraint thực sự
                constraints = parsed_lp.get("constraints", [])
                non_trivial = [c for c in constraints if c.get("rhs", 0) != 0 or any(abs(v) > 0 for v in c.get("coeffs_map", {}).values())]
                if len(non_trivial) >= 1:
                    self.state["current_problem_definition"] = parsed_lp
                    solver_to_use = self._detect_solver(user_message)
                    async for event in self._solve_current_problem(solver_to_use):
                        yield event
                    return
                else:
                    self._log("lp_parser returned trivial constraints — rejected")
        else:
            # ── PATH B: Tin nhắn ngắn (math notation) → lp_parser trước ──
            parsed_lp, parse_logs = self.lp_formula_parser(user_message)
            self._log(f"lp_parser result: {'OK' if parsed_lp else 'None'}, logs: {parse_logs}")
            
            if parsed_lp and self._is_problem_defined(parsed_lp):
                self._log(f"Đã phân tích thành công bài toán. Logs: {parse_logs}")
                self.state["current_problem_definition"] = parsed_lp
                solver_to_use = self._detect_solver(user_message)
                async for event in self._solve_current_problem(solver_to_use):
                    yield event
                return

            # Fallback: tin nhắn ngắn nhưng lp_parser thất bại → thử LLM
            if _LP_KEYWORDS.search(user_message) and self.openai_client.client:
                self._log("lp_parser thất bại trên tin nhắn ngắn. Thử LLM extraction...")
                yield {"type": "chunk", "content": "<p><i>🔍 Đang nhận diện bài toán...</i></p>"}
                structured_text = await self.openai_client.extract_lp_as_structured(user_message)
                if structured_text:
                    parsed_lp2, logs2 = self.lp_formula_parser(structured_text)
                    if parsed_lp2 and self._is_problem_defined(parsed_lp2):
                        self.state["current_problem_definition"] = parsed_lp2
                        solver_to_use = self._detect_solver(user_message)
                        async for event in self._solve_current_problem(solver_to_use):
                            yield event
                        return

        # Ưu tiên 4: Phân tích ý định từ câu nói
        nlp_result = self.rule_based_nlp.parse_intent_and_entities(user_message)
        intent = nlp_result.get("intent", "unknown")
        entities = nlp_result.get("entities", {})

        if intent == "request_step_explanation":
            async for event in self._handle_intent_request_step_explanation(entities):
                yield event
            return
        
        if intent == "request_specific_solver":
            async for event in self._handle_intent_request_specific_solver(entities, user_message):
                yield event
            return

        if intent == "request_theoretical_concept":
            concept = entities.get("concept_name", "khái niệm đó")
            yield {"type": "chunk", "content": ""}
            explanation = await self.openai_client.explain_lp_concept(concept) or f"Mình chưa có thông tin về '{concept}'."
            yield {"type": "complete", "result": self._finalize_response({"text_response": explanation, "allow_html": True, "suggestions": ["Quy tắc Bland là gì?", "Biến nhân tạo là gì?"]})}
            return
        
        # Mặc định: Dùng LLM để trò chuyện
        if self.openai_client.client:
            response_full = ""
            async for chunk in self.openai_client.handle_general_conversation_stream(user_message, self.state["history"]):
                response_full += chunk
                yield {"type": "chunk", "content": chunk}
            yield {"type": "complete", "result": self._finalize_response({"text_response": response_full or "Xin lỗi, mình chưa hiểu ý bạn. Bạn có thể nói rõ hơn được không?", "suggestions": ["Giải bài toán mẫu"]})}
            return
        else:
            yield {"type": "complete", "result": self._finalize_response({"text_response": "Chào bạn, mình là trợ lý Quy hoạch tuyến tính. Mình có thể giúp gì cho bạn?", "suggestions": ["Giải bài toán mẫu"]})}
            return

    # --- Các hàm định dạng (Formatting Functions) ---
    def _format_problem_summary(self, internal_def: Dict) -> str:
        """Tạo bản tóm tắt bài toán bằng HTML."""
        obj_type = internal_def.get('objective_type', 'N/A').capitalize()
        obj_expr = self._format_coeffs_map_for_display(internal_def.get('objective_coeffs_map', {}))
        summary_html = f"<b>Bài toán của bạn:</b><ul><li><b>Mục tiêu:</b> {obj_type} Z = {obj_expr}</li>"
        
        if internal_def.get("constraints"):
            summary_html += "<li><b>Các ràng buộc:</b><ul style='padding-left: 20px;'>"
            for c in internal_def["constraints"]:
                lhs = self._format_coeffs_map_for_display(c['coeffs_map'])
                op = c.get('operator', '=').replace('==', '=')
                rhs = c.get('rhs', 0)
                summary_html += f"<li>{lhs} {op} {rhs}</li>"
            summary_html += "</ul></li>"
        summary_html += "</ul><hr style='margin: 12px 0; border-color: #e2e8f0;'>"
        return summary_html
        
    def _format_solution_response(self, solution: dict, problem_data: dict, solver_name: str) -> str:
        """Định dạng câu trả lời kết quả, có xử lý hình ảnh."""
        if not solution:
            return f"<p><b>Kết quả từ phương pháp '{solver_name}':</b></p><p>Rất tiếc, đã có lỗi xảy ra và bộ giải không trả về kết quả.</p>"

        status = solution.get("status", "Unknown")
        header = f"<p><b>Kết quả từ phương pháp '{solver_name}':</b></p>"
        body = ""
        
        if status == "Optimal":
            obj_val = solution.get("objective_value", 0)
            vars_map = solution.get("variables", {})
            vars_str = ", ".join([f"<b>{k}</b> = {v:.3f}" for k, v in vars_map.items() if not k.startswith('_')])
            body = f"🎉 <b>Lời giải tối ưu đã được tìm thấy!</b><br>• <b>Giá trị mục tiêu:</b> {obj_val:.3f}<br>• <b>Giá trị các biến:</b> {vars_str}"
        elif status == "Infeasible":
            body = "Trạng thái bài toán: <b>Vô nghiệm</b>. Các ràng buộc có thể đang mâu thuẫn với nhau."
        elif status == "Unbounded":
            body = "Trạng thái bài toán: <b>Không bị chặn</b>. Hàm mục tiêu có thể tiến tới vô cùng."
        else:
            body = f"Trạng thái bài toán: <b>{status}</b>. Không tìm thấy lời giải tối ưu."
            
        image_html = ""
        if solution.get("plot_image_base64"):
            img_src = solution["plot_image_base64"]
            image_html = f"<br><br><div style='text-align: center;'><img src='{img_src}' alt='Biểu đồ giải bằng hình học' style='max-width: 100%; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);' /></div>"
            
        return header + body + image_html

    def _format_coeffs_map_for_display(self, coeffs_map: Dict[str, float]) -> str:
        if not coeffs_map: return "0"
        terms = []
        is_first = True
        for var, coeff in sorted(coeffs_map.items()):
            if abs(coeff) < 1e-9: continue
            
            sign = ""
            if not is_first:
                sign = " + " if coeff > 0 else " - "
            elif coeff < 0:
                sign = "-"

            abs_coeff = abs(coeff)
            coeff_part = str(round(abs_coeff, 2)) if abs(round(abs_coeff, 2) - 1.0) > 1e-9 or var == '' else ""
            
            terms.append(f"{sign}{coeff_part}{var}")
            is_first = False
        return "".join(terms).strip()

    def _finalize_response(self, response: Dict) -> Dict:
        """Đóng gói và trả về phản hồi cuối cùng."""
        response.setdefault("text_response", "Mình chưa rõ ý bạn, bạn có thể nói khác đi được không?")
        response.setdefault("suggestions", ["Giải bài toán mẫu", "Bắt đầu bài toán mới"])
        response.setdefault("allow_html", False)
        
        self.state["history"].append({"role": "assistant", "content": response["text_response"]})
        self.state["last_bot_message"] = response["text_response"]
        return response
