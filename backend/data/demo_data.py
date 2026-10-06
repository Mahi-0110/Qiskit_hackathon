from models.portfolio import Asset

def get_demo_assets():
    return [
        Asset(symbol="AAPL", expected_return=0.15, risk=0.12),
        Asset(symbol="MSFT", expected_return=0.14, risk=0.10),
        Asset(symbol="NVDA", expected_return=0.25, risk=0.22),
        Asset(symbol="GOOGL", expected_return=0.12, risk=0.11),
        Asset(symbol="AMZN", expected_return=0.11, risk=0.13),
        Asset(symbol="META", expected_return=0.18, risk=0.19),
        Asset(symbol="TSLA", expected_return=0.20, risk=0.25),
        Asset(symbol="JPM", expected_return=0.08, risk=0.06),
    ]

def get_demo_covariance():
    import numpy as np
    # Synthetic covariance matrix
    # Diagonal = risk^2
    # Off-diagonal = risk_i * risk_j * correlation_ij
    assets = get_demo_assets()
    n = len(assets)
    cov = np.zeros((n, n))
    
    # Base correlation matrix (synthetic)
    # High tech correlation, JPM less correlated
    correlations = np.array([
        [1.0, 0.7, 0.6, 0.7, 0.6, 0.6, 0.4, 0.2],
        [0.7, 1.0, 0.6, 0.8, 0.7, 0.6, 0.4, 0.2],
        [0.6, 0.6, 1.0, 0.6, 0.5, 0.7, 0.5, 0.1],
        [0.7, 0.8, 0.6, 1.0, 0.7, 0.7, 0.4, 0.2],
        [0.6, 0.7, 0.5, 0.7, 1.0, 0.6, 0.4, 0.1],
        [0.6, 0.6, 0.7, 0.7, 0.6, 1.0, 0.4, 0.1],
        [0.4, 0.4, 0.5, 0.4, 0.4, 0.4, 1.0, 0.1],
        [0.2, 0.2, 0.1, 0.2, 0.1, 0.1, 0.1, 1.0],
    ])
    
    for i in range(n):
        for j in range(n):
            cov[i,j] = assets[i].risk * assets[j].risk * correlations[i,j]
            
    return cov
