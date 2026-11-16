# src/grover.py
# Algoritmo de Grover para 2 qubits: busca cada uno de los 4 estados posibles.
import os

import matplotlib
matplotlib.use("Agg")
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram

CAPTURAS = "capturas"


def oraculo_fase(qc, target):
    """Invierte la fase del estado target.

    Qiskit ordena los bits al reves: en la cadena "b1b0", el caracter de la
    derecha es el qubit 0. Se aplica X a cada qubit cuyo bit en target vale 0,
    asi el estado buscado se convierte en |11>, CZ le cambia la fase y las X
    se deshacen.
    """
    ceros = [q for q in range(2) if target[1 - q] == "0"]
    if ceros:
        qc.x(ceros)
    qc.cz(0, 1)
    if ceros:
        qc.x(ceros)


def difusor(qc):
    """Inversion alrededor de la media para 2 qubits."""
    qc.h([0, 1])
    qc.x([0, 1])
    qc.cz(0, 1)
    qc.x([0, 1])
    qc.h([0, 1])


def build_grover_circuit(target="11"):
    """Circuito de Grover con 1 iteracion (optima para N = 4)."""
    qc = QuantumCircuit(2, 2, name=f"grover_{target}")
    qc.h([0, 1])           # superposicion uniforme de los 4 estados
    qc.barrier()
    oraculo_fase(qc, target)
    qc.barrier()
    difusor(qc)
    qc.measure([0, 1], [0, 1])
    return qc


def grover_2qubits(target="11", shots=1024, seed=None, mostrar=False):
    qc = build_grover_circuit(target)
    if mostrar:
        print(f"Circuito para el objetivo |{target}>:")
        print(qc.draw(output="text"))
    counts = AerSimulator(seed_simulator=seed).run(qc, shots=shots).result().get_counts()

    print(f"Grover buscando |{target}> ({shots} shots):")
    for state, count in sorted(counts.items()):
        print(f"  |{state}>: {count:4d} ({count / shots * 100:.1f}%)")

    top = max(counts, key=counts.get)
    veredicto = "CORRECTO" if top == target else "ERROR"
    print(f"Estado mas probable: |{top}> - {veredicto}")

    os.makedirs(CAPTURAS, exist_ok=True)
    fig = plot_histogram(counts, title=f"Grover, objetivo |{target}>")
    fig.savefig(os.path.join(CAPTURAS, f"grover_{target}.png"), dpi=150, bbox_inches="tight")
    return counts


if __name__ == "__main__":
    shots = 1024
    for t in ["00", "01", "10", "11"]:
        counts = grover_2qubits(target=t, shots=shots, mostrar=(t == "01"))
        assert counts.get(t, 0) / shots > 0.9, f"Error: |{t}> no supero el 90%"
        print()
    print("OK: los 4 objetivos se encontraron con probabilidad > 90%")
