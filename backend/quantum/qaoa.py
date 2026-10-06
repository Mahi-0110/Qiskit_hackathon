import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector
from qiskit_aer.primitives import Sampler
from scipy.optimize import minimize
from typing import List, Tuple, Dict, Any
import time

from optimization.qubo import build_objective_matrix, get_cost_hamiltonian
from quantum.xy_mixer import create_initial_state, create_xy_mixer
from models.portfolio import PortfolioRequest
from models.qaoa import QAOAResult

def create_qaoa_circuit(n: int, k: int, p: int, cost_hamiltonian) -> Tuple[QuantumCircuit, ParameterVector, ParameterVector]:
    gammas = ParameterVector('gamma', p)
    betas = ParameterVector('beta', p)
    
    qc = QuantumCircuit(n)
    
    # 1. Initial State
    initial_state = create_initial_state(n, k)
    qc.compose(initial_state, inplace=True)
    
    # 2. QAOA Layers
    for i in range(p):
        # Cost Operator: exp(-i gamma H_C)
        # H_C is a SparsePauliOp
        for pauli, coeff in zip(cost_hamiltonian.paulis, cost_hamiltonian.coeffs):
            pauli_str = str(pauli)
            # Find indices where Z is applied
            z_indices = [idx for idx, p_char in enumerate(pauli_str[::-1]) if p_char == 'Z']
            
            if len(z_indices) == 1:
                qc.rz(2 * gammas[i] * np.real(coeff), z_indices[0])
            elif len(z_indices) == 2:
                qc.rzz(2 * gammas[i] * np.real(coeff), z_indices[0], z_indices[1])
                
        # Mixer Operator: exp(-i beta H_M)
        mixer = create_xy_mixer(n, betas[i])
        qc.compose(mixer, inplace=True)
        
    qc.measure_all()
    return qc, gammas, betas

def run_qaoa(request: PortfolioRequest, cov_matrix: np.ndarray, p: int = 1, shots: int = 1024) -> QAOAResult:
    start_time = time.time()
    n = len(request.assets)
    k = request.k_assets
    
    Q = build_objective_matrix(request, cov_matrix)
    cost_hamiltonian = get_cost_hamiltonian(Q)
    
    qc, gammas, betas = create_qaoa_circuit(n, k, p, cost_hamiltonian)
    sampler = Sampler()
    
    def objective_func(params):
        # params = [gamma_0, ..., gamma_{p-1}, beta_0, ..., beta_{p-1}]
        gamma_vals = params[:p]
        beta_vals = params[p:]
        
        # Bind parameters
        bound_qc = qc.assign_parameters({gammas: gamma_vals, betas: beta_vals})
        
        # Execute
        result = sampler.run([bound_qc], shots=shots).result()
        quasi_dists = result.quasi_dists[0]
        
        # Calculate expected cost (we want to minimize -Cost, which maximizes original objective)
        expected_energy = 0
        for bit_int, prob in quasi_dists.items():
            # bit_int to binary array
            bitstr = format(bit_int, f'0{n}b')
            x = np.array([int(b) for b in bitstr[::-1]])  # qiskit little-endian
            
            # Verify K constraint for exact energy formulation (penalty applied if invalid, but XY mixer should preserve it)
            if np.sum(x) == k:
                # Energy = - (mu^T x - lambda x^T Sigma x)
                energy = - (np.dot([a.expected_return for a in request.assets], x) - request.risk_factor * np.dot(x, np.dot(cov_matrix, x)))
            else:
                energy = 1000  # Penalty for invalid states
                
            expected_energy += prob * energy
            
        return expected_energy

    # Optimize
    initial_params = np.concatenate([np.ones(p)*0.1, np.ones(p)*0.1])
    res = minimize(objective_func, initial_params, method='COBYLA', options={'maxiter': 50})
    
    # Run with optimal params
    optimal_gammas = res.x[:p]
    optimal_betas = res.x[p:]
    final_qc = qc.assign_parameters({gammas: optimal_gammas, betas: optimal_betas})
    
    result = sampler.run([final_qc], shots=shots).result()
    quasi_dists = result.quasi_dists[0]
    
    distribution = {}
    valid_states = 0
    invalid_states = 0
    best_objective = -float('inf')
    best_x = None
    
    expected_returns = np.array([a.expected_return for a in request.assets])
    
    for bit_int, prob in quasi_dists.items():
        count = int(prob * shots)
        bitstr = format(bit_int, f'0{n}b')[::-1] # Reverse to match asset order
        distribution[bitstr] = count
        
        x = np.array([int(b) for b in bitstr])
        
        if np.sum(x) == k:
            valid_states += count
            port_return = np.dot(expected_returns, x)
            port_risk = np.dot(x, np.dot(cov_matrix, x))
            objective = port_return - request.risk_factor * port_risk
            
            if objective > best_objective:
                best_objective = objective
                best_x = x
        else:
            invalid_states += count
            
    execution_time = time.time() - start_time
    
    if best_x is not None:
        selected_assets = [request.assets[i].symbol for i in range(n) if best_x[i] == 1]
        best_return = np.dot(expected_returns, best_x)
        best_risk = np.dot(best_x, np.dot(cov_matrix, best_x))
    else:
        selected_assets = []
        best_return = 0
        best_risk = 0
        best_objective = 0
        
    return QAOAResult(
        best_portfolio=selected_assets,
        expected_return=float(best_return),
        risk=float(best_risk),
        objective_score=float(best_objective),
        is_valid=(best_x is not None),
        execution_time=execution_time,
        approximation_ratio=0.0, # Will be set by controller comparing with classical
        distribution=distribution,
        valid_states=valid_states,
        invalid_states=invalid_states
    ), final_qc
