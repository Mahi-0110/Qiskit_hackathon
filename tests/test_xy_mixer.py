import unittest
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from backend.quantum.xy_mixer import create_initial_state, create_xy_mixer

class TestXYMixer(unittest.TestCase):
    def test_hamming_weight_preservation(self):
        n = 4
        k = 2
        
        # Initial state should have Hamming weight 2
        qc = QuantumCircuit(n)
        qc.compose(create_initial_state(n, k), inplace=True)
        
        # Verify initial state
        sv_initial = Statevector.from_instruction(qc)
        probs_initial = sv_initial.probabilities_dict()
        
        for bitstring, prob in probs_initial.items():
            if prob > 1e-6:
                self.assertEqual(bitstring.count('1'), k, "Initial state does not have correct Hamming weight")
        
        # Apply XY mixer
        # We need a parameter value for beta
        mixer = create_xy_mixer(n, 1.5)
        # We need to bind the parameter since create_xy_mixer takes a Parameter object or float
        # Wait, create_xy_mixer takes a beta. Let's make sure it's bound.
        from qiskit.circuit import Parameter
        beta = Parameter('beta')
        mixer = create_xy_mixer(n, beta)
        bound_mixer = mixer.assign_parameters({beta: 1.5})
        
        qc.compose(bound_mixer, inplace=True)
        
        # Verify mixed state
        sv_mixed = Statevector.from_instruction(qc)
        probs_mixed = sv_mixed.probabilities_dict()
        
        valid_states = 0
        for bitstring, prob in probs_mixed.items():
            if prob > 1e-6:
                self.assertEqual(bitstring.count('1'), k, f"State {bitstring} has incorrect Hamming weight")
                valid_states += 1
                
        # Mixer should have spread amplitude to multiple valid states
        self.assertGreater(valid_states, 1, "Mixer did not spread amplitude to other valid states")

if __name__ == '__main__':
    unittest.main()
