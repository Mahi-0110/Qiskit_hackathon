import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Play, Activity, Cpu, Briefcase, Zap, GitBranch, AlertCircle, CheckCircle2 } from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line
} from 'recharts';

const API_BASE = 'http://localhost:8000/api';

function App() {
  const [loading, setLoading] = useState(false);
  const [demoData, setDemoData] = useState<any>(null);
  const [results, setResults] = useState<any>(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [kAssets, setKAssets] = useState(3);
  const [pDepth, setPDepth] = useState(1);

  useEffect(() => {
    fetchDemoData();
  }, []);

  const fetchDemoData = async () => {
    try {
      const res = await axios.get(`${API_BASE}/demo`);
      setDemoData(res.data);
    } catch (err) {
      console.error("Failed to load demo data", err);
    }
  };

  const runDemo = async () => {
    if (!demoData) return;
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/qaoa/run`, {
        portfolio: {
          assets: demoData.assets,
          k_assets: kAssets,
          risk_factor: 0.5
        },
        qaoa_params: {
          p: pDepth,
          shots: 1024,
          optimizer_name: "COBYLA",
          use_xy_mixer: true
        }
      });
      setResults(res.data);
      setActiveTab('results');
    } catch (err) {
      console.error("Failed to run demo", err);
      alert("Error running simulation. Check backend logs.");
    } finally {
      setLoading(false);
    }
  };

  const COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#f43f5e', '#84cc16'];

  const renderDashboard = () => (
    <div className="space-y-6">
      <div className="glass-panel p-6">
        <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
          <Briefcase className="text-primary" /> Portfolio Configuration
        </h2>
        
        {demoData && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div>
              <p className="text-slate-400 mb-2">Available Assets</p>
              <div className="flex flex-wrap gap-2">
                {demoData.assets.map((a: any, i: number) => (
                  <span key={i} className="px-3 py-1 bg-surface border border-slate-600 rounded-full text-sm">
                    {a.symbol}
                  </span>
                ))}
              </div>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-slate-400 mb-1">Select K Assets (Constraint)</label>
                <input 
                  type="range" min="1" max={demoData.assets.length} value={kAssets} 
                  onChange={(e) => setKAssets(parseInt(e.target.value))}
                  className="w-full accent-primary"
                />
                <div className="text-right text-lg font-mono">{kAssets}</div>
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">QAOA Depth (p)</label>
                <input 
                  type="range" min="1" max="5" value={pDepth} 
                  onChange={(e) => setPDepth(parseInt(e.target.value))}
                  className="w-full accent-secondary"
                />
                <div className="text-right text-lg font-mono">{pDepth}</div>
              </div>
            </div>
          </div>
        )}
        
        <button 
          onClick={runDemo} 
          disabled={loading || !demoData}
          className="w-full py-4 rounded-lg bg-gradient-to-r from-primary to-secondary text-white font-bold text-lg hover:opacity-90 transition disabled:opacity-50 flex justify-center items-center gap-2"
        >
          {loading ? (
            <><Activity className="animate-spin" /> Simulating Quantum Circuit...</>
          ) : (
            <><Play /> Run Quantum Portfolio Optimizer</>
          )}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-panel p-6">
          <h3 className="text-xl font-bold mb-4 flex items-center gap-2"><Zap className="text-accent" /> XY Mixer Concept</h3>
          <p className="text-slate-300 mb-4">
            A standard X mixer would independently flip qubits, moving from a valid portfolio (e.g., exactly 3 assets) to an invalid one (e.g., 4 or 2 assets).
          </p>
          <div className="bg-slate-900 p-4 rounded-lg font-mono text-center text-sm border border-slate-700">
            <div className="text-green-400 mb-1">Valid (K=3)</div>
            <div className="text-white text-lg">1 1 1 0 0 0 0 0</div>
            <div className="my-2 text-slate-500">↓ XY Interaction (swap) ↓</div>
            <div className="text-white text-lg">1 1 0 1 0 0 0 0</div>
            <div className="text-green-400 mt-1">Valid (K=3)</div>
          </div>
          <p className="text-slate-400 text-sm mt-4">
            The XY mixer preserves the Hamming weight (number of 1s), ensuring every state explored by QAOA satisfies the strict cardinality constraint without requiring penalty terms in the cost Hamiltonian.
          </p>
        </div>
        
        <div className="glass-panel p-6">
          <h3 className="text-xl font-bold mb-4 flex items-center gap-2"><Cpu className="text-primary" /> IBM Heavy-Hex Topology</h3>
          <p className="text-slate-300 mb-4">
            Quantum circuits mapped to real hardware must route logical qubits to physical qubits connected by the device's coupling map. IBM devices use a heavy-hex lattice.
          </p>
          <div className="flex justify-center items-center p-4 bg-slate-900 rounded-lg border border-slate-700 h-32">
             <div className="text-center text-slate-500">
                <GitBranch size={48} className="mx-auto mb-2 opacity-50" />
                Connectivity Graph (Simulation)
             </div>
          </div>
          <p className="text-slate-400 text-sm mt-4">
            We transpile the logical QAOA circuit to an IBM-style heavy-hex topology to analyze the routing overhead (SWAP gates and increased depth).
          </p>
        </div>
      </div>
    </div>
  );

  const renderResults = () => {
    if (!results) return null;

    const { classical, qaoa, routing } = results;

    const distData = Object.entries(qaoa.distribution)
      .map(([key, value]) => ({ bitstring: key, count: value as number }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 15); // Top 15

    return (
      <div className="space-y-6">
        {/* Metric Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="glass-panel p-4 text-center">
            <div className="text-slate-400 text-sm mb-1">Approximation Ratio</div>
            <div className="text-3xl font-bold text-accent">{(qaoa.approximation_ratio * 100).toFixed(1)}%</div>
          </div>
          <div className="glass-panel p-4 text-center">
            <div className="text-slate-400 text-sm mb-1">Depth Overhead</div>
            <div className="text-3xl font-bold text-secondary">{(routing.depth_overhead).toFixed(1)}x</div>
          </div>
          <div className="glass-panel p-4 text-center">
            <div className="text-slate-400 text-sm mb-1">Valid QAOA States</div>
            <div className="text-3xl font-bold text-primary">{(qaoa.valid_states / (qaoa.valid_states + qaoa.invalid_states) * 100).toFixed(0)}%</div>
          </div>
          <div className="glass-panel p-4 text-center">
            <div className="text-slate-400 text-sm mb-1">Estimated SWAPs</div>
            <div className="text-3xl font-bold text-amber-500">{routing.swap_count}</div>
          </div>
        </div>

        {/* Comparison Table */}
        <div className="glass-panel p-6">
          <h3 className="text-xl font-bold mb-4">Solution Comparison</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="py-2 text-slate-400">Metric</th>
                  <th className="py-2 text-slate-400">Classical Exact</th>
                  <th className="py-2 text-slate-400">QAOA (XY Mixer)</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-slate-800">
                  <td className="py-3 font-medium">Selected Assets</td>
                  <td className="py-3 text-slate-300">{classical.selected_assets.join(', ')}</td>
                  <td className="py-3 text-slate-300">{qaoa.best_portfolio.join(', ')}</td>
                </tr>
                <tr className="border-b border-slate-800">
                  <td className="py-3 font-medium">Expected Return</td>
                  <td className="py-3 text-accent">{(classical.expected_return * 100).toFixed(2)}%</td>
                  <td className="py-3 text-accent">{(qaoa.expected_return * 100).toFixed(2)}%</td>
                </tr>
                <tr className="border-b border-slate-800">
                  <td className="py-3 font-medium">Risk</td>
                  <td className="py-3 text-amber-400">{(classical.risk * 100).toFixed(2)}%</td>
                  <td className="py-3 text-amber-400">{(qaoa.risk * 100).toFixed(2)}%</td>
                </tr>
                <tr className="border-b border-slate-800">
                  <td className="py-3 font-medium">Objective Score</td>
                  <td className="py-3 font-mono">{classical.objective_score.toFixed(4)}</td>
                  <td className="py-3 font-mono">{qaoa.objective_score.toFixed(4)}</td>
                </tr>
                <tr>
                  <td className="py-3 font-medium">Constraint Status</td>
                  <td className="py-3"><span className="flex items-center text-green-400 gap-1"><CheckCircle2 size={16}/> Valid</span></td>
                  <td className="py-3">
                    {qaoa.is_valid ? 
                      <span className="flex items-center text-green-400 gap-1"><CheckCircle2 size={16}/> Valid</span> : 
                      <span className="flex items-center text-red-400 gap-1"><AlertCircle size={16}/> Invalid</span>
                    }
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="glass-panel p-6">
            <h3 className="text-xl font-bold mb-4">QAOA Measurement Distribution</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={distData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="bitstring" stroke="#94a3b8" angle={-45} textAnchor="end" height={60} />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#475569' }} />
                  <Bar dataKey="count" fill="#8b5cf6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <p className="text-sm text-slate-400 text-center mt-2">Top measured bitstrings from QAOA sampling.</p>
          </div>

          <div className="glass-panel p-6">
            <h3 className="text-xl font-bold mb-4">Hardware Routing Impact</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={[
                  { name: 'Gate Count', Logical: routing.logical_metrics.gate_count, Routed: routing.routed_metrics.gate_count },
                  { name: 'Circuit Depth', Logical: routing.logical_metrics.circuit_depth, Routed: routing.routed_metrics.circuit_depth },
                  { name: '2Q Gates', Logical: routing.logical_metrics.two_qubit_gate_count, Routed: routing.routed_metrics.two_qubit_gate_count }
                ]}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="name" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#475569' }} />
                  <Legend />
                  <Bar dataKey="Logical" fill="#3b82f6" name="Logical Circuit (All-to-All)" />
                  <Bar dataKey="Routed" fill="#ef4444" name="Routed Circuit (Heavy-Hex)" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <p className="text-sm text-slate-400 text-center mt-2">Comparison of circuit metrics before and after transpilation to IBM Heavy-Hex topology.</p>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen p-6 md:p-12">
      <div className="max-w-6xl mx-auto">
        <header className="mb-8">
          <h1 className="text-4xl md:text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-primary via-secondary to-accent mb-2">
            Quantum Portfolio Optimizer
          </h1>
          <p className="text-xl text-slate-400">
            Constrained Portfolio Optimization using QAOA, XY Mixers and IBM Heavy-Hex Routing
          </p>
        </header>

        <div className="flex gap-4 mb-6 border-b border-slate-700 pb-2">
          <button 
            className={`px-4 py-2 font-medium transition ${activeTab === 'dashboard' ? 'text-primary border-b-2 border-primary' : 'text-slate-400 hover:text-slate-200'}`}
            onClick={() => setActiveTab('dashboard')}
          >
            Dashboard
          </button>
          <button 
            className={`px-4 py-2 font-medium transition ${activeTab === 'results' ? 'text-primary border-b-2 border-primary' : 'text-slate-400 hover:text-slate-200'} ${!results ? 'opacity-50 cursor-not-allowed' : ''}`}
            onClick={() => results && setActiveTab('results')}
          >
            Experiment Results
          </button>
        </div>

        {activeTab === 'dashboard' ? renderDashboard() : renderResults()}

        <footer className="mt-12 text-center text-slate-500 text-sm border-t border-slate-800 pt-6">
          <p className="mb-2">This prototype is for educational and research demonstration purposes only. It is not financial advice and does not recommend actual investments.</p>
          <p>Built with Qiskit, FastAPI, and React for the Quantum Hackathon.</p>
        </footer>
      </div>
    </div>
  );
}

export default App;
