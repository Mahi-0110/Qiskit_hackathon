from qiskit import QuantumCircuit
from qiskit.circuit import Parameter

def create_initial_state(n: int, k: int) -> QuantumCircuit:
    """
    Creates an initial state with exactly K ones.
    A simple approach is to just flip the first K qubits to 1.
    """
    qc = QuantumCircuit(n)
    for i in range(k):
        qc.x(i)
    return qc

def create_xy_mixer(n: int, beta: Parameter) -> QuantumCircuit:
    """
    Creates an XY mixer circuit.
    The XY mixer consists of exp(-i beta/2 (X_i X_j + Y_i Y_j)) 
    for edges in a ring graph connecting all qubits.
    """
    qc = QuantumCircuit(n)
    
    # We apply the XY mixer on a ring topology
    edges = [(i, (i + 1) % n) for i in range(n)]
    
    # Even-odd coloring to avoid overlapping gates
    even_edges = [(i, (i + 1) % n) for i in range(0, n, 2) if (i+1)%n != 0 or n%2==0]
    odd_edges = [(i, (i + 1) % n) for i in range(1, n, 2)]
    if n % 2 != 0:
        odd_edges.append((n-1, 0)) # Last edge for odd N
        
    def apply_xy_layer(edges_to_apply):
        for i, j in edges_to_apply:
            # exp(-i beta/2 (XX + YY)) = exp(-i beta/2 XX) exp(-i beta/2 YY)
            # RXX(theta) = exp(-i theta/2 XX), so theta = beta
            qc.rxx(beta, i, j)
            qc.ryy(beta, i, j)
            
    # Apply even edges then odd edges
    apply_xy_layer(even_edges)
    apply_xy_layer(odd_edges)
    
    return qc
