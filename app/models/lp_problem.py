# /app/models/lp_problem.py
from pydantic import BaseModel
from typing import Dict, List, Optional, Any

class Constraint(BaseModel):
    name: str
    coeffs_map: Dict[str, float]
    operator: str  # "<=", ">=", "=="
    rhs: float

class LPProblemDefinition(BaseModel):
    objective_type: str  # "maximize" | "minimize"
    objective_coeffs_map: Dict[str, float]
    objective_variables_ordered: List[str]
    constraints: List[Constraint] = []

class SolverResult(BaseModel):
    status: str  # "Optimal" | "Infeasible" | "Unbounded"
    objective_value: Optional[float] = None
    variables: Optional[Dict[str, float]] = None
