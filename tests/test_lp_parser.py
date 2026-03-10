import sys
import os

# Set up path to import app modules
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.nlp.parsers.lp_parser import parse_lp_problem_from_string

def get_test_cases():
    with open('test_inputs.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract only lines with > "..." format
    test_cases = []
    import re
    matches = re.findall(r'>\s*"(.*?)"|>\s*\*(.*?)\*(.*?)"(.*?)"', content)
    for match in matches:
        if match[0]: test_cases.append(match[0])
        elif match[3]: test_cases.append(match[3])
    return test_cases

tests = get_test_cases()
if len(tests) >= 10:
    print("\n--- TEST Case 10 (From File) ---")
    print("Input:", tests[9])
    res, logs = parse_lp_problem_from_string(tests[9])
    print(f"Result: {res}")
    for l in logs: print(f"  {l}")

if len(tests) >= 22:
    print("\n--- TEST Case 22 (From File) ---")
    print("Input:", tests[21])
    res, logs = parse_lp_problem_from_string(tests[21])
    print(f"Result: {res}")
    for l in logs: print(f"  {l}")
