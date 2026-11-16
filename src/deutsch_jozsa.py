# src/deutsch_jozsa.py
# Algoritmo de Deutsch-Jozsa para n = 2 con un oraculo constante y uno balanceado.
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator


def oracle_constante(n):
    """Oraculo constante f(x) = 0: no modifica ningun qubit."""
    return QuantumCircuit(n + 1, name="Uf_const")   # incluye el qubit ancilla


def oracle_balanceada(n):
    """Oraculo balanceado f(x) = x0 XOR x1 XOR ...: CNOT de cada qubit al ancilla."""
    qc = QuantumCircuit(n + 1, name="Uf_bal")
    for i in range(n):
        qc.cx(i, n)
    return qc


def deutsch_jozsa(oracle_qc, n, shots=1024, seed=None, mostrar=False):
    """Ejecuta Deutsch-Jozsa con el oraculo dado y devuelve los conteos."""
    qc = QuantumCircuit(n + 1, n)

    qc.x(n)                    # ancilla en |1>
    qc.h(range(n + 1))         # entradas en superposicion y ancilla en |->
    qc.barrier()
    qc.compose(oracle_qc, inplace=True)   # una sola evaluacion del oraculo
    qc.barrier()
    qc.h(range(n))             # interferencia sobre los qubits de entrada
    qc.measure(range(n), range(n))        # el ancilla no se mide

    if mostrar:
        print(f"Circuito con el oraculo {oracle_qc.name}:")
        print(qc.draw(output="text"))
    sim = AerSimulator(seed_simulator=seed)
    return sim.run(qc, shots=shots).result().get_counts()


if __name__ == "__main__":
    n = 2
    shots = 1024
    counts_c = deutsch_jozsa(oracle_constante(n), n, shots)
    counts_b = deutsch_jozsa(oracle_balanceada(n), n, shots, mostrar=True)

    print(f"Constante:  {counts_c}")    # esperado: {'00': 1024}
    print(f"Balanceada: {counts_b}")    # esperado: ningun '00'

    # El resultado es determinista: todos los shots dan el mismo valor
    assert counts_c == {"0" * n: shots}, "Error: el oraculo constante no devolvio siempre 00"
    assert "0" * n not in counts_b, "Error: el oraculo balanceado devolvio 00"
    print("OK: Deutsch-Jozsa clasifica correctamente con 1 evaluacion del oraculo")
    print(f"Un algoritmo clasico necesitaria hasta 2^(n-1) + 1 = {2 ** (n - 1) + 1} evaluaciones")
