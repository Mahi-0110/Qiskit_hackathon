from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np

from models.portfolio import PortfolioRequest, PortfolioResult
from models.qaoa import QAOAParameters, QAOAResult
from models.circuit import RoutingResult
from optimization.classical import solve_classically
from quantum.qaoa import run_qaoa, create_qaoa_circuit
from optimization.qubo import build_objective_matrix, get_cost_hamiltonian
from routing.heavy_hex import route_circuit
from data.demo_data import get_demo_assets, get_demo_covariance

app = FastAPI(title="Quantum Portfolio Optimizer API")

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DemoResponse(BaseModel):
    assets: list
    covariance: list

class FullDemoRequest(BaseModel):
    portfolio: PortfolioRequest
    qaoa_params: QAOAParameters

class FullDemoResponse(BaseModel):
    classical: PortfolioResult
    qaoa: QAOAResult
    routing: RoutingResult

@app.get("/api/demo", response_model=DemoResponse)
def get_demo():
    assets = get_demo_assets()
    cov = get_demo_covariance().tolist()
    return DemoResponse(assets=assets, covariance=cov)

@app.post("/api/portfolio/optimize-classical", response_model=PortfolioResult)
def optimize_classical(request: PortfolioRequest):
    if len(request.assets) < request.k_assets:
        raise HTTPException(status_code=400, detail="K cannot be greater than number of assets.")
    
    # In a real app, cov_matrix would be passed or calculated. Using demo for now.
    cov = get_demo_covariance() 
    if len(request.assets) != cov.shape[0]:
        # Handle subset or custom data (simplification for hackathon)
        n = len(request.assets)
        cov = np.eye(n) * 0.1 # Fallback
        
    result = solve_classically(request, cov)
    return result

@app.post("/api/qaoa/run", response_model=FullDemoResponse)
def run_full_demo(request: FullDemoRequest):
    port_req = request.portfolio
    qaoa_params = request.qaoa_params
    
    if len(port_req.assets) < port_req.k_assets:
        raise HTTPException(status_code=400, detail="K cannot be greater than number of assets.")
        
    # We will use demo cov matrix if sizes match, otherwise identity fallback
    cov = get_demo_covariance()
    if len(port_req.assets) != cov.shape[0]:
        n = len(port_req.assets)
        cov = np.eye(n) * 0.1
        
    # 1. Classical Baseline
    classical_res = solve_classically(port_req, cov)
    
    # 2. QAOA Run
    qaoa_res, qc = run_qaoa(port_req, cov, p=qaoa_params.p, shots=qaoa_params.shots)
    
    # Calculate Approximation Ratio
    if classical_res.objective_score > 0 and qaoa_res.objective_score > 0:
        qaoa_res.approximation_ratio = qaoa_res.objective_score / classical_res.objective_score
    elif classical_res.objective_score <= 0:
        qaoa_res.approximation_ratio = 1.0 # Edge case handling
        
    # 3. Routing Metrics
    routing_res = route_circuit(qc)
    
    return FullDemoResponse(
        classical=classical_res,
        qaoa=qaoa_res,
        routing=routing_res
    )

@app.get("/api/health")
def health_check():
    return {"status": "ok"}
