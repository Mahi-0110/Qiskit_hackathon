import time
import itertools
import numpy as np
from typing import List, Tuple
from models.portfolio import PortfolioRequest, PortfolioResult, Asset

def calculate_portfolio_metrics(x: np.ndarray, expected_returns: np.ndarray, cov_matrix: np.ndarray, risk_factor: float) -> Tuple[float, float, float]:
    """Calculates return, risk, and objective score for a given binary portfolio vector."""
    port_return = np.dot(expected_returns, x)
    port_risk = np.dot(x, np.dot(cov_matrix, x))
    
    # Objective to maximize: expected_return - risk_factor * risk
    objective = port_return - risk_factor * port_risk
    
    return port_return, port_risk, objective

def solve_classically(request: PortfolioRequest, cov_matrix: np.ndarray) -> PortfolioResult:
    start_time = time.time()
    
    n = len(request.assets)
    k = request.k_assets
    
    expected_returns = np.array([a.expected_return for a in request.assets])
    
    best_objective = -float('inf')
    best_x = None
    best_return = 0.0
    best_risk = 0.0
    
    # Exhaustive enumeration for small instances
    for combination in itertools.combinations(range(n), k):
        x = np.zeros(n)
        for idx in combination:
            x[idx] = 1
            
        port_return, port_risk, objective = calculate_portfolio_metrics(
            x, expected_returns, cov_matrix, request.risk_factor
        )
        
        if objective > best_objective:
            best_objective = objective
            best_x = x
            best_return = port_return
            best_risk = port_risk
            
    execution_time = time.time() - start_time
    
    selected_assets = [request.assets[i].symbol for i in range(n) if best_x[i] == 1]
    
    return PortfolioResult(
        selected_assets=selected_assets,
        expected_return=float(best_return),
        risk=float(best_risk),
        objective_score=float(best_objective),
        is_valid=True,
        execution_time=execution_time,
        method="Classical Exact"
    )
