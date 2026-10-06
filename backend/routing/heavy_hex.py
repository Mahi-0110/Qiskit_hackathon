import time
from qiskit import QuantumCircuit, transpile
from qiskit.transpiler import CouplingMap
from models.circuit import CircuitMetrics, RoutingResult

def get_heavy_hex_coupling_map(distance: int = 3) -> CouplingMap:
    """
    Creates a heavy-hex coupling map of a given distance.
    Distance 3 has 17 qubits. Distance 5 has 43 qubits.
    """
    try:
        return CouplingMap.from_heavy_hex(distance)
    except AttributeError:
        # Fallback if from_heavy_hex is not available in the specific qiskit version
        # Manually create a 17-qubit heavy hex lattice
        edges = [
            (0, 1), (1, 0), (1, 2), (2, 1), (2, 3), (3, 2), (3, 4), (4, 3),
            (1, 5), (5, 1), (3, 6), (6, 3), (5, 7), (7, 5), (6, 8), (8, 6),
            (7, 9), (9, 7), (8, 10), (10, 8), (9, 11), (11, 9), (10, 11), (11, 10),
            (9, 12), (12, 9), (11, 13), (13, 11), (12, 14), (14, 12), (13, 15), (15, 13),
            (14, 16), (16, 14), (15, 16), (16, 15)
        ]
        return CouplingMap(edges)

def extract_circuit_metrics(qc: QuantumCircuit) -> CircuitMetrics:
    # Decompose into basis gates to get accurate gate counts
    # But usually transpiled circuits are already in basis gates.
    ops = qc.count_ops()
    qubit_count = qc.num_qubits
    gate_count = sum(ops.values()) - ops.get('measure', 0) - ops.get('barrier', 0)
    
    # 2-qubit gates are typically cx, cz, ecr, cp, rxx, ryy, rzz
    two_qubit_gates = ['cx', 'cz', 'ecr', 'cp', 'rxx', 'ryy', 'rzz', 'swap', 'iswap']
    two_qubit_gate_count = sum([ops.get(g, 0) for g in two_qubit_gates])
    
    circuit_depth = qc.depth()
    
    return CircuitMetrics(
        qubit_count=qubit_count,
        gate_count=gate_count,
        two_qubit_gate_count=two_qubit_gate_count,
        circuit_depth=circuit_depth
    )

def route_circuit(qc: QuantumCircuit) -> RoutingResult:
    start_time = time.time()
    
    # Calculate pre-routing metrics
    # To get a fair comparison, transpile to the same basis gates but ALL-TO-ALL topology
    basis_gates = ['rz', 'sx', 'x', 'cx']
    logical_qc = transpile(qc, basis_gates=basis_gates, optimization_level=1)
    logical_metrics = extract_circuit_metrics(logical_qc)
    
    # Get Heavy-Hex map (e.g. distance 3, 17 qubits, or 5 if N is larger)
    distance = 3 if qc.num_qubits <= 17 else 5
    cmap = get_heavy_hex_coupling_map(distance)
    
    # Transpile to Heavy-Hex
    routed_qc = transpile(qc, basis_gates=basis_gates, coupling_map=cmap, optimization_level=2)
    routed_metrics = extract_circuit_metrics(routed_qc)
    
    routing_time = time.time() - start_time
    
    # Estimate SWAPs: 1 SWAP is roughly 3 CX gates
    # We can estimate SWAPs added by routing by comparing CX counts
    # It's an approximation. SABRE routing inserts SWAPs.
    logical_cx = logical_qc.count_ops().get('cx', 0)
    routed_cx = routed_qc.count_ops().get('cx', 0)
    swap_count = max(0, (routed_cx - logical_cx) // 3)
    
    depth_overhead = routed_metrics.circuit_depth / max(1, logical_metrics.circuit_depth)
    gate_overhead = routed_metrics.gate_count / max(1, logical_metrics.gate_count)
    
    return RoutingResult(
        logical_metrics=logical_metrics,
        routed_metrics=routed_metrics,
        swap_count=swap_count,
        depth_overhead=depth_overhead,
        gate_overhead=gate_overhead,
        routing_time=routing_time
    )
