from pydantic import BaseModel
from typing import List, Dict

class QAOAParameters(BaseModel):
    p: int = 1
    shots: int = 1024
    optimizer_name: str = "COBYLA"
    use_xy_mixer: bool = True
    
class QAOAResult(BaseModel):
    best_portfolio: List[str]
    expected_return: float
    risk: float
    objective_score: float
    is_valid: bool
    execution_time: float
    approximation_ratio: float
    distribution: Dict[str, int]
    valid_states: int
    invalid_states: int
