# Quantum Portfolio Optimizer

A complete, functional hackathon prototype demonstrating constrained portfolio optimization using the Quantum Approximate Optimization Algorithm (QAOA) with an XY mixer and IBM heavy-hex routing analysis.

## Overview

This project solves a constrained portfolio-selection problem: selecting exactly K assets from a larger pool to maximize expected return while minimizing risk. 

To enforce the exact-K constraint directly in the quantum state exploration, we implement an **XY mixer** which preserves the Hamming weight (number of selected assets) of the quantum states. Finally, the generated logical QAOA circuit is transpiled to an **IBM-style Heavy-Hex topology** to analyze real-world routing overhead (added SWAP gates and increased depth).

## Features

- **Classical Baseline**: Exact exhaustive solver for ground-truth comparison.
- **QUBO / Ising Formulation**: Construction of the objective cost Hamiltonian.
- **QAOA with XY Mixer**: Full implementation of QAOA parameter optimization using a custom XY mixer to maintain valid portfolio configurations.
- **Heavy-Hex Routing Analysis**: Transpilation of the logical QAOA circuit to an IBM Heavy-Hex coupling map to extract hardware-aware metrics.
- **Interactive Dashboard**: A React frontend to run experiments and visualize results.

## Technologies Used

- **Frontend**: React, TypeScript, Vite, Tailwind CSS, Recharts
- **Backend**: Python, FastAPI
- **Quantum**: Qiskit, Qiskit Aer (Simulator)

## Installation

### Backend Setup

1. Navigate to the `backend` directory.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate # Linux/Mac
   ```
3. Install dependencies:
   ```bash
   pip install fastapi uvicorn pydantic qiskit qiskit-aer qiskit-optimization qiskit-ibm-runtime numpy pandas scipy networkx python-dotenv matplotlib rustworkx
   ```

### Frontend Setup

1. Navigate to the `frontend` directory.
2. Install dependencies:
   ```bash
   npm install
   ```

## Running the Application

1. **Start Backend**:
   ```bash
   cd backend
   .\venv\Scripts\activate
   uvicorn main:app --reload --port 8000
   ```

2. **Start Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Open Browser**:
   Navigate to `http://localhost:5173`

## Usage (Demo Mode)

1. Open the web interface.
2. Adjust the number of assets (K) and QAOA depth (p).
3. Click **"Run Quantum Portfolio Optimizer"**.
4. View the "Experiment Results" tab for the Approximation Ratio, Valid States %, Estimated SWAPs, and comparative charts between logical and routed circuits.

## Mathematical Formulation

The objective is to maximize: `Return - λ * Risk`
Which translates to minimizing the cost Hamiltonian corresponding to `- (μ^T x - λ x^T Σ x)`.
Since the XY Mixer preserves the constraint `Σ x_i = K`, no penalty terms are added to the cost Hamiltonian.
