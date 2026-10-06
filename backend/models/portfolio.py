from pydantic import BaseModel, Field
from typing import List, Optional

class Asset(BaseModel):
    symbol: str
    expected_return: float
    risk: float
    
class PortfolioRequest(BaseModel):
    assets: List[Asset]
    k_assets: int = Field(..., description="Exactly K assets to select")
    risk_factor: float = Field(default=0.5, description="Risk aversion parameter (lambda)")
    
class PortfolioResult(BaseModel):
    selected_assets: List[str]
    expected_return: float
    risk: float
    objective_score: float
    is_valid: bool
    execution_time: float
    method: str = "Classical"
