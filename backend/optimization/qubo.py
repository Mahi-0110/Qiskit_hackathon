import numpy as np
from qiskit.quantum_info import Pauli, SparsePauliOp
from models.portfolio import PortfolioRequest

def build_objective_matrix(request: PortfolioRequest, cov_matrix: np.ndarray) -> np.ndarray:
    """
    Builds the objective matrix Q for the problem: maximize x^T Q x
    Where objective is: mu^T x - lambda * x^T Sigma x
    Since x_i in {0,1}, x_i = x_i^2. So we can put mu_i on the diagonal of Q.
    Q_ii = mu_i - lambda * Sigma_ii
    Q_ij = - lambda * Sigma_ij for i != j
    """
    n = len(request.assets)
    Q = np.zeros((n, n))
    
    expected_returns = np.array([a.expected_return for a in request.assets])
    risk_factor = request.risk_factor
    
    for i in range(n):
        for j in range(n):
            if i == j:
                Q[i, j] = expected_returns[i] - risk_factor * cov_matrix[i, i]
            else:
                Q[i, j] = - risk_factor * cov_matrix[i, j]
                
    return Q

def get_cost_hamiltonian(Q: np.ndarray) -> SparsePauliOp:
    """
    Converts the objective matrix Q (maximize x^T Q x) to an Ising Hamiltonian.
    x_i = (I - Z_i) / 2
    Cost = sum_{i,j} Q_ij x_i x_j
    We want to MAXIMIZE Cost, which is equivalent to MINIMIZING -Cost.
    So the Hamiltonian H corresponds to -Cost.
    
    H = - sum_{i,j} Q_ij ((I - Z_i)/2) ((I - Z_j)/2)
    H = -1/4 sum_{i,j} Q_ij (I - Z_i - Z_j + Z_i Z_j)
    """
    n = Q.shape[0]
    paulis = []
    coeffs = []
    
    # We will build the Hamiltonian for -Cost to minimize it with QAOA
    
    # Constant term (usually can be ignored for QAOA, but good for exact energy)
    offset = 0.0
    
    # Linear terms Z_i
    z_coeffs = np.zeros(n)
    
    # Quadratic terms Z_i Z_j
    for i in range(n):
        for j in range(n):
            val = -0.25 * Q[i, j]
            if i == j:
                # Z_i Z_i = I
                offset += val
                offset += -val * 2 # from -Z_i -Z_i
                z_coeffs[i] -= val * (-2) # Actually it's -0.25 * Q[i,i] * (I - 2 Z_i + I) = -0.25 * Q[i,i] * (2 I - 2 Z_i) = -0.5 Q[i,i] (I - Z_i)
            else:
                offset += val
                z_coeffs[i] -= val
                z_coeffs[j] -= val
                
                # Z_i Z_j
                if i < j:
                    # Q is symmetric, so we combine Q_ij and Q_ji
                    zz_val = val * 2
                    
                    z_str = ['I'] * n
                    z_str[n - 1 - i] = 'Z'  # Qiskit uses little-endian
                    z_str[n - 1 - j] = 'Z'
                    paulis.append("".join(z_str))
                    coeffs.append(zz_val)

    # Re-evaluate logic:
    # x_i = (I - Z_i)/2
    # sum_{i,j} Q_ij x_i x_j = sum_i Q_ii x_i + sum_{i!=j} Q_ij x_i x_j
    # -Cost = - [ sum_i Q_ii (I - Z_i)/2 + sum_{i<j} 2 Q_ij (I - Z_i)/2 (I - Z_j)/2 ]
    #       = - sum_i 0.5 Q_ii I + sum_i 0.5 Q_ii Z_i 
    #         - sum_{i<j} 0.5 Q_ij (I - Z_i - Z_j + Z_i Z_j)
    
    offset_exact = - sum([0.5 * Q[i,i] for i in range(n)]) - sum([0.5 * Q[i,j] for i in range(n) for j in range(i+1, n)])
    
    z_coeffs_exact = np.zeros(n)
    for i in range(n):
        z_coeffs_exact[i] += 0.5 * Q[i,i]
        for j in range(n):
            if i != j:
                z_coeffs_exact[i] += 0.25 * (Q[i,j] + Q[j,i])
                
    paulis_exact = []
    coeffs_exact = []
    
    if offset_exact != 0:
        paulis_exact.append("I" * n)
        coeffs_exact.append(offset_exact)
        
    for i in range(n):
        if z_coeffs_exact[i] != 0:
            z_str = ['I'] * n
            z_str[n - 1 - i] = 'Z'
            paulis_exact.append("".join(z_str))
            coeffs_exact.append(z_coeffs_exact[i])
            
    for i in range(n):
        for j in range(i+1, n):
            zz_val = -0.25 * (Q[i,j] + Q[j,i])
            if zz_val != 0:
                z_str = ['I'] * n
                z_str[n - 1 - i] = 'Z'
                z_str[n - 1 - j] = 'Z'
                paulis_exact.append("".join(z_str))
                coeffs_exact.append(zz_val)

    return SparsePauliOp(paulis_exact, coeffs_exact)

def get_penalty_hamiltonian(n: int, k: int, penalty_factor: float) -> SparsePauliOp:
    """
    Constructs the Hamiltonian for the penalty term P * (sum_i x_i - K)^2
    To minimize this, it's added to the cost Hamiltonian.
    x_i = (I - Z_i)/2
    sum_i x_i - K = sum_i (I - Z_i)/2 - K = n/2 - K - 1/2 sum_i Z_i
    (n/2 - K - 1/2 sum_i Z_i)^2 = (n/2 - K)^2 - (n/2 - K) sum_i Z_i + 1/4 (sum_i Z_i)^2
    = (n/2 - K)^2 - (n/2 - K) sum_i Z_i + 1/4 sum_i Z_i^2 + 1/4 sum_{i!=j} Z_i Z_j
    Since Z_i^2 = I:
    = (n/2 - K)^2 I + n/4 I - (n/2 - K) sum_i Z_i + 1/2 sum_{i<j} Z_i Z_j
    """
    offset = penalty_factor * ((n/2 - k)**2 + n/4)
    z_coeff = penalty_factor * -(n/2 - k)
    zz_coeff = penalty_factor * 0.5
    
    paulis = []
    coeffs = []
    
    if offset != 0:
        paulis.append("I" * n)
        coeffs.append(offset)
        
    for i in range(n):
        if z_coeff != 0:
            z_str = ['I'] * n
            z_str[n - 1 - i] = 'Z'
            paulis.append("".join(z_str))
            coeffs.append(z_coeff)
            
        for j in range(i+1, n):
            if zz_coeff != 0:
                z_str = ['I'] * n
                z_str[n - 1 - i] = 'Z'
                z_str[n - 1 - j] = 'Z'
                paulis.append("".join(z_str))
                coeffs.append(zz_coeff)
                
    return SparsePauliOp(paulis, coeffs)
