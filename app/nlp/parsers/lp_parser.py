# /app/nlp/parsers/lp_parser.py
import re
import logging
from typing import Dict, List, Tuple, Optional, Any

from app.nlp.data import rule_templates

logger = logging.getLogger(__name__)

def _expand_non_negativity_constraints(text: str) -> str:
    """
    Expands compact non-negativity constraints like "x1, x2 >= 0"
    into separate constraints "x1 >= 0; x2 >= 0".
    This is a common notation that the parser should handle.
    """
    # This regex is designed to find a comma-separated list of variables
    # followed by a non-negativity operator and zero.
    pattern = re.compile(
        # Group 1: Catches the comma-separated variables (e.g., "x1, x2")
        r'((?:[a-zA-Z_][a-zA-Z0-9_]*\s*,\s*)+[a-zA-Z_][a-zA-Z0-9_]*)'
        # Group 2: Catches the operator
        r'\s*(>=|≥)\s*'
        # Group 3: Catches the zero
        r'(0\.?0*|0)\s*$',
        re.IGNORECASE
    )

    def expander(match):
        vars_part, op, rhs = match.groups()
        variables = [v.strip() for v in vars_part.split(',')]
        # Returns a semicolon-separated string of individual constraints
        return '; '.join(f"{var} {op} {rhs}" for var in variables)

    # Replace all found occurrences of the pattern
    return pattern.sub(expander, text)


def parse_expression_to_coeffs_map(expr_str: str) -> Tuple[Dict[str, float], List[str]]:
    """
    Parses a mathematical expression string (e.g., "3x1 - 2.5x2") into
    a coefficient map and an ordered list of variables.
    This function remains unchanged as its logic is correct.
    """
    coeffs_map: Dict[str, float] = {}
    found_variables: List[str] = []
    
    # Regex to find terms like "+3x1", "- 2.5 x2", or "var"
    term_regex = re.compile(r'([+\-]?)\s*(\d+\.?\d*|\.\d+)?\s*\*?\s*([a-zA-Z_][a-zA-Z0-9_]*)')
    
    # Regex for lone variables like "+x" or "-y" that the first regex might miss
    lone_var_regex = re.compile(r'([+\-]?)\s*([a-zA-Z_][a-zA-Z0-9_]*)(?=\s*[+\-]|$)')

    # Normalize expression to always start with a sign
    processed_expr = expr_str.strip()
    if not processed_expr.startswith(('+', '-')):
        processed_expr = '+' + processed_expr

    # First pass for terms with explicit or implicit coefficients
    for match in term_regex.finditer(processed_expr):
        sign, coeff_str, var_name = match.groups()
        coeff = float(coeff_str) if coeff_str else 1.0
        if sign == '-': coeff *= -1
        coeffs_map[var_name] = coeffs_map.get(var_name, 0.0) + coeff
        if var_name not in found_variables: found_variables.append(var_name)
    
    # Second pass for any remaining lone variables
    remaining_expr = term_regex.sub('', processed_expr)
    for match in lone_var_regex.finditer(remaining_expr):
        sign, var_name = match.groups()
        coeff = -1.0 if sign == '-' else 1.0
        coeffs_map[var_name] = coeffs_map.get(var_name, 0.0) + coeff
        if var_name not in found_variables: found_variables.append(var_name)

    return coeffs_map, sorted(list(coeffs_map.keys()))


def parse_lp_problem_from_string(text: str) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """
    Parses a full LP problem string. This function is now stricter and more robust.
    """
    logs = [f"LpParser: Starting to parse string: '{text[:100]}...'"]
    
    try:
        # Normalize newlines to semicolons to use a single separator
        text_cleaned = text.replace('\n', ';').strip()
        
        # --- Objective Parsing ---
        objective_match = re.search(rule_templates.LP_PATTERNS['objective_keywords'], text_cleaned, re.IGNORECASE)
        if not objective_match:
            logs.append("Error: Objective keyword (maximize/minimize) not found.")
            return None, logs
            
        objective_type_str = objective_match.group(1).lower()
        
        constraints_start_match = re.search(rule_templates.LP_PATTERNS['subject_to_keywords'], text_cleaned, re.IGNORECASE)
        # Also treat "and" as a constraint separator (English "x+y>=4 and x+3y>=6")
        and_match = re.search(r'\band\b', text_cleaned, re.IGNORECASE)
        
        if constraints_start_match:
            objective_part = text_cleaned[objective_match.end():constraints_start_match.start()].strip()
            constraints_part = text_cleaned[constraints_start_match.end():].strip()
        elif and_match:
            # "and" splits objective from constraints: "2x + 3y and x + y >= 4"
            # But "and" might also be mid-constraints list. Find the first "and" after objective.
            obj_raw = text_cleaned[objective_match.end():].strip()
            and_in_obj = re.search(r'\band\b', obj_raw, re.IGNORECASE)
            if and_in_obj:
                objective_part = obj_raw[:and_in_obj.start()].strip()
                constraints_part = obj_raw[and_in_obj.end():].strip()
                # Replace remaining "and" with ";" for multiple constraints
                constraints_part = re.sub(r'\band\b', ';', constraints_part, flags=re.IGNORECASE)
            else:
                objective_part = obj_raw
                constraints_part = ""
        else:
            # FALLBACK: look for comma-separated constraints inline with objective
            # Pattern: objective expression, then comma, then expression with operator
            # "max 2x+4y, x+2y <= 100, 2x+y <= 100" — constraints start at first comma before <=/>=/=
            obj_raw = text_cleaned[objective_match.end():].strip()
            # Try to find where constraints begin: first comma followed by something with an operator
            comma_constraint = re.search(r',\s*(.+?(?:<=|>=|==|<|>|≤|≥))', obj_raw)
            if comma_constraint:
                cut = obj_raw.index(',', comma_constraint.start())
                objective_part = obj_raw[:cut].strip()
                constraints_part = obj_raw[cut+1:].strip()
            else:
                objective_part = obj_raw
                constraints_part = ""

        # Cắt bớt phần sau dấu ; đầu tiên (do newline→;) để lấy phần objective trước constraint
        # Ví dụ: ": 3x + 2y;" → cần bỏ leading ":" và trailing ";"
        objective_part = objective_part.lstrip(':;, \t').rstrip(';, \t')
        # Nếu còn dấu ; ở giữa (nghĩa là constraints đã bị nhét vào objective_part), cắt tại ; đầu tiên
        if ';' in objective_part:
            objective_part = objective_part.split(';')[0].strip()

        # Lọc chỉ giữ lại các thành phần toán học hợp lệ (biến, số, phép tính)
        # Giữ lại cụm: Z =, f(x) =, số, biến chữ latin, phép -, +
        # Strip the "Z = ", "f(x) =", "chi phí:" prefix from objective expression
        objective_expr = re.sub(r"^[a-zA-ZÀ-ỹ0-9\s_\(\)]+\s*[=:]\s*", "", objective_part, flags=re.IGNORECASE).strip()
        # If strip removed everything (no = or : found), use objective_part itself
        if not objective_expr:
            objective_expr = objective_part.strip()
        
        # CRITICAL FIX: Remove trailing Vietnamese/English words that are NOT math terms
        # e.g. "3x1 + 5x2 với ràng buộc" → strip "với ràng buộc"
        objective_expr = re.sub(r'\s+(với|subject|điều kiện|where|when|st|s\.t).*$', '', objective_expr, flags=re.IGNORECASE).strip()
        
        # Remove non-math trailing garbage: everything after the last valid math char sequence
        objective_expr = re.sub(r'[^a-zA-Z0-9\s\+\-\*\.].*$', '', objective_expr).strip()
        

        obj_coeffs_map, obj_vars = parse_expression_to_coeffs_map(objective_expr)
        if not obj_coeffs_map:
            logs.append(f"Error: Could not parse objective expression: '{objective_expr}'")
            return None, logs

        # CRITICAL FIX: Detect objective type correctly for both English and Vietnamese  
        maximize_keywords = {"max", "maximize", "tối đa hóa", "tối đa"}
        minimize_keywords = {"min", "minimize", "tối thiểu hóa", "tối thiểu"}
        obj_type_clean = objective_type_str.strip().lower()
        if any(kw in obj_type_clean for kw in maximize_keywords) or obj_type_clean in maximize_keywords:
            obj_type_final = "maximize"
        elif any(kw in obj_type_clean for kw in minimize_keywords) or obj_type_clean in minimize_keywords:
            obj_type_final = "minimize"
        else:
            # fallback: check for 'max' substring
            obj_type_final = "maximize" if "max" in obj_type_clean else "minimize"
        
        problem_data = {
            "objective_type": obj_type_final,
            "objective_coeffs_map": obj_coeffs_map,
            "objective_variables_ordered": obj_vars,
            "constraints": []
        }
        logs.append(f"Parsed objective function: {problem_data['objective_type']} (from '{objective_type_str}')")

        # --- Constraint Parsing (Improved Logic) ---
        if constraints_part:
            # 0. Pre-strip: remove trailing solver/method phrases that are NOT constraints
            #    e.g. "bằng phương pháp 2 pha", "using simplex", "by two-phase method"
            method_strip_pattern = re.compile(
                r'[;,.\s]*(b\u1eb1ng|using|by|v\u1edbi|d\u00f9ng|s\u1eed\s+d\u1ee5ng)\s+'
                r'(ph\u01b0\u01a1ng\s+ph\u00e1p\s+)?'
                r'(2\s*pha|hai\s+pha|\u0111\u01a1n\s+h\u00ecnh|simplex|bland|auxiliary|'
                r'pulp|h\u00ecnh\s+h\u1ecdc|geometric|\u0111\u1ed1i\s+ng\u1eabu|dual)[^;]*$',
                re.IGNORECASE
            )
            constraints_part = method_strip_pattern.sub('', constraints_part).strip()

            # 1. Expand compact non-negativity constraints first
            constraints_part = _expand_non_negativity_constraints(constraints_part)
            
            # 2. Split into individual constraint lines using punctuation or flow words
            constraint_lines = [line.strip() for line in re.split(r'[;.,]|\bvà\b|\bvs\b|\bcòn\b|\band\b', constraints_part, flags=re.IGNORECASE) if line.strip()]
            
            parsed_constraints = []
            for i, line in enumerate(constraint_lines):
                # Strip leading bullet dash (e.g. "- x + y <= 10" → "x + y <= 10")
                line = re.sub(r'^[-•]\s+', '', line).strip()
                if not line:
                    continue
                # Use the single-line constraint pattern from rule_templates
                constr_match = rule_templates.LP_PATTERNS["single_constraint_line"].match(line)
                
                if not constr_match:
                    # If the line contains no comparison operator, it's likely trailing text
                    # (e.g. "bằng phương pháp 2 pha") — skip silently instead of aborting.
                    has_operator = re.search(r'<=|>=|==|<|>|≤|≥', line)
                    if not has_operator:
                        logs.append(f"Warning: Skipping non-constraint line '{line}' (no comparison operator found).")
                        continue
                    logs.append(f"Error: Could not parse constraint line '{line}'. Aborting parsing of the entire problem.")
                    return None, logs
                
                lhs_str, op, rhs_str = constr_match.group(1).strip(), constr_match.group(2), constr_match.group(3)
                
                try:
                    rhs_val = float(rhs_str)
                    lhs_coeffs, _ = parse_expression_to_coeffs_map(lhs_str)
                    if not lhs_coeffs:
                        logs.append(f"Error: No coefficients found on the left-hand side of constraint '{line}'.")
                        return None, logs

                    parsed_constraints.append({
                        "name": f"c{i+1}", 
                        "coeffs_map": lhs_coeffs,
                        "operator": op.replace("=", "==").replace("<==", "<=").replace(">==", ">="), 
                        "rhs": rhs_val
                    })
                    logs.append(f"Successfully parsed constraint: {line}")
                except (ValueError, TypeError) as e:
                    logs.append(f"Error converting right-hand side to a number in constraint '{line}': {e}")
                    return None, logs
            
            problem_data["constraints"] = parsed_constraints
        
        logs.append(f"Parsing complete. Found {len(problem_data['constraints'])} constraints.")
        return problem_data, logs

    except Exception as e:
        logger.error(f"A critical error occurred in lp_parser: {e}", exc_info=True)
        logs.append(f"An unexpected critical error occurred during parsing: {e}")
        return None, logs
