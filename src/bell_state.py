# src/bell_state.py
# Prepara el estado de Bell |Phi+> = (|00> + |11>)/sqrt(2) y verifica la correlacion.
import os

import matplotlib
matplotlib.use("Agg")                 # guarda imagenes sin necesitar pantalla
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram

CAPTURAS = "capturas"


def bell_state_experiment(shots=1024, seed=None):
    """Prepara el estado de Bell |Phi+>, lo mide y verifica la correlacion."""
    qc = QuantumCircuit(2, 2, name="bell")   # 2 qubits, 2 bits clasicos

    qc.h(0)              # Hadamard en q0: superposicion (|0> + |1>)/sqrt(2)
    qc.cx(0, 1)          # CNOT con control q0 y objetivo q1: entrelazamiento
    qc.measure([0, 1], [0, 1])

    print("Circuito:")
    print(qc.draw(output="text"))

    simulator = AerSimulator(seed_simulator=seed)
    counts = simulator.run(qc, shots=shots).result().get_counts()

    print(f"Resultados Bell |Phi+> ({shots} shots):")
    for state, count in sorted(counts.items()):
        print(f"  |{state}> : {count:4d} ({count / shots * 100:.1f}%)")

    # Solo deben aparecer |00> y |11>: los dos qubits siempre coinciden
    assert "01" not in counts and "10" not in counts, \
        "ERROR: aparecieron estados no entrelazados"
    print("OK: correlacion perfecta verificada")

    os.makedirs(CAPTURAS, exist_ok=True)
    fig = plot_histogram(counts, title="Estado de Bell |Phi+>")
    fig.savefig(os.path.join(CAPTURAS, "bell_histogram.png"), dpi=150, bbox_inches="tight")
    print(f"Histograma guardado en {CAPTURAS}/bell_histogram.png")
    return counts


if __name__ == "__main__":
    bell_state_experiment()
