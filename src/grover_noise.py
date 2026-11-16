# src/grover_noise.py
# Grover (2 qubits) con y sin ruido despolarizante, efecto de la profundidad
# y comparacion con un modelo de ruido calibrado de un backend IBM simulado.
import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from qiskit import transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error
from qiskit.visualization import plot_histogram

from grover import build_grover_circuit

CAPTURAS = "capturas"


def build_noise_model(p1q=0.001, p2q=0.01):
    """Ruido despolarizante: p1q por puerta de 1 qubit (h, x) y p2q por
    puerta de 2 qubits (cz), del orden del hardware superconductor NISQ."""
    noise_model = NoiseModel()
    noise_model.add_all_qubit_quantum_error(depolarizing_error(p1q, 1), ["h", "x"])
    noise_model.add_all_qubit_quantum_error(depolarizing_error(p2q, 2), ["cz"])
    return noise_model


def grover_noise_experiment(target="11", shots=1024, seed=None):
    qc = build_grover_circuit(target)

    counts_ideal = AerSimulator(seed_simulator=seed).run(qc, shots=shots).result().get_counts()
    noisy_sim = AerSimulator(noise_model=build_noise_model(), seed_simulator=seed)
    counts_noisy = noisy_sim.run(qc, shots=shots).result().get_counts()

    p_ideal = counts_ideal.get(target, 0) / shots
    p_noisy = counts_noisy.get(target, 0) / shots

    print(f"Grover |{target}> sin ruido: {p_ideal * 100:.1f}%")
    print(f"Grover |{target}> con ruido: {p_noisy * 100:.1f}%")
    print(f"Degradacion: {(p_ideal - p_noisy) * 100:.1f} puntos porcentuales")
    print("Conteos con ruido:", dict(sorted(counts_noisy.items())))

    os.makedirs(CAPTURAS, exist_ok=True)
    fig, axs = plt.subplots(1, 2, figsize=(10, 4))
    plot_histogram(counts_ideal, ax=axs[0], title="Sin ruido")
    plot_histogram(counts_noisy, ax=axs[1], title="Con ruido (despolarizante)")
    fig.tight_layout()
    fig.savefig(os.path.join(CAPTURAS, "grover_noise_comparison.png"), dpi=150)
    plt.close(fig)
    return p_ideal, p_noisy


def grover_profundidad(target="11", shots=4096, pares=(0, 5, 10, 20, 50, 100), seed=None):
    """Agrega pares CZ-CZ antes de medir. Cada par equivale a la identidad, asi
    que el resultado ideal no cambia, pero cada CZ suma un 1% de error: mide
    como se acumula el error al hacer el circuito mas profundo."""
    noisy_sim = AerSimulator(noise_model=build_noise_model(), seed_simulator=seed)
    print(f"Pares CZ-CZ extra | CZ totales | Exito |{target}> con ruido")
    for k in pares:
        qc = build_grover_circuit(target)
        qc.remove_final_measurements()
        for _ in range(k):
            qc.cz(0, 1)
            qc.cz(0, 1)
        qc.measure_all()
        counts = noisy_sim.run(qc, shots=shots).result().get_counts()
        p = counts.get(target, 0) / shots
        print(f"{k:17d} | {2 + 2 * k:10d} | {p * 100:5.1f}%")


def grover_backend_falso(target="11", shots=1024, seed=None):
    """Compara contra NoiseModel.from_backend con la calibracion guardada de un
    backend IBM simulado (no necesita cuenta de IBM Quantum)."""
    from qiskit_ibm_runtime.fake_provider import FakeBrisbane

    backend = FakeBrisbane()
    noise = NoiseModel.from_backend(backend)
    qc = transpile(build_grover_circuit(target), backend=backend,
                   optimization_level=1, seed_transpiler=7)
    sim = AerSimulator(noise_model=noise, seed_simulator=seed)
    counts = sim.run(qc, shots=shots).result().get_counts()
    p = counts.get(target, 0) / shots
    ops = qc.count_ops()
    print(f"Backend simulado: {backend.name} ({backend.num_qubits} qubits)")
    print(f"Puertas tras transpilar: {dict(ops)}")
    print(f"Grover |{target}> con ruido calibrado: {p * 100:.1f}%")
    print("Conteos:", dict(sorted(counts.items())))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("modo", nargs="?", default="comparar",
                        choices=["comparar", "profundidad", "backend"])
    args = parser.parse_args()
    if args.modo == "comparar":
        grover_noise_experiment()
    elif args.modo == "profundidad":
        grover_profundidad()
    else:
        grover_backend_falso()
