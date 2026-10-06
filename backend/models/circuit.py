from pydantic import BaseModel
from typing import List, Dict, Optional

class CircuitMetrics(BaseModel):
    qubit_count: int
    gate_count: int
    two_qubit_gate_count: int
    circuit_depth: int
    
class RoutingResult(BaseModel):
    logical_metrics: CircuitMetrics
    routed_metrics: CircuitMetrics
    swap_count: int
    depth_overhead: float
    gate_overhead: float
    routing_time: float
