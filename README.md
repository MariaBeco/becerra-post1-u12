# Post-Contenido 1: Laboratorio Qiskit y criptografía post-cuántica

Arquitectura de Computadores, Unidad 12
Maria Fernanda Becerra Coronel, código 1152509, Universidad Francisco de Paula Santander
Docente: Ing. Jonathan Rey

Este repositorio contiene las dos partes del laboratorio. La Parte 1 implementa y simula en Qiskit el estado de Bell, el algoritmo de Deutsch-Jozsa, el algoritmo de Grover para 2 qubits y Grover bajo un modelo de ruido. La Parte 2 es el análisis del impacto cuántico en ciberseguridad, en [`docs/analisis-pqc.md`](docs/analisis-pqc.md).

## Estructura

```
becerra-post1-u12/
├── README.md
├── requirements.txt
├── src/
│   ├── bell_state.py       estado de Bell |Φ+⟩ y verificación de la correlación
│   ├── deutsch_jozsa.py    Deutsch-Jozsa con oráculo constante y balanceado (n = 2)
│   ├── grover.py           Grover de 2 qubits para los 4 objetivos
│   └── grover_noise.py     Grover con ruido: comparación, profundidad y backend calibrado
├── docs/
│   └── analisis-pqc.md
└── capturas/
```

## Entorno y ejecución

Los experimentos se ejecutaron en Google Colab (Python 3.13.18, Qiskit 2.6.2 y Qiskit Aer 0.18.2) sobre el simulador `AerSimulator`, sin hardware cuántico ni cuenta de IBM Quantum. La guía pide Qiskit 1.x; las funciones usadas (`QuantumCircuit`, `AerSimulator`, `NoiseModel`, `transpile`) tienen la misma interfaz en la versión 2.

```bash
pip install -r requirements.txt
python src/bell_state.py
python src/deutsch_jozsa.py
python src/grover.py
python src/grover_noise.py              # sin ruido vs ruido despolarizante
python src/grover_noise.py profundidad  # efecto de agregar puertas CZ
python src/grover_noise.py backend      # ruido calibrado de un backend IBM simulado
```

Los scripts se ejecutan desde la raíz del repositorio y guardan los histogramas en `capturas/`.

## Cambios respecto al código de la guía

1. **Orden de los bits en el oráculo de Grover.** Qiskit escribe los resultados con el qubit 0 a la derecha: la cadena `"01"` significa q1 = 0 y q0 = 1. El oráculo de la guía para `"01"` aplica X al qubit 0, con lo que marca el estado q0 = 0, q1 = 1, que Qiskit imprime como `"10"`. Por eso, con el código original, Grover devolvía `|10⟩` al buscar `|01⟩` y viceversa, y el programa imprimía `ERROR` en esos dos casos. La función `oraculo_fase` aplica X a cada qubit según la posición correcta del bit en la cadena.
2. **f-string anidado.** `print(f"... {"CORRECTO" if ...}")` usa comillas dobles dentro de un f-string con comillas dobles, lo que es un error de sintaxis antes de Python 3.12. Se calcula el veredicto en una variable aparte.
3. **Carpeta de capturas.** Los scripts crean `capturas/` si no existe; sin eso, `savefig` falla.
4. **Verificación de Deutsch-Jozsa.** La guía solo comprueba que `"00"` aparezca para el oráculo constante. El script exige que **todos** los shots den `00`, que es lo que significa que el resultado sea determinista.
5. **Diagramas.** Bell, Deutsch-Jozsa y Grover imprimen el diagrama del circuito en texto.
6. **Experimentos adicionales para las decisiones.** `grover_noise.py profundidad` agrega pares CZ-CZ, que equivalen a la identidad, para medir cómo se acumula el error con la profundidad, y `grover_noise.py backend` usa `NoiseModel.from_backend()` con la calibración guardada de FakeBrisbane, un backend IBM simulado de 127 qubits que no requiere cuenta de IBM Quantum.

## Circuitos

### Estado de Bell

```
     ┌───┐     ┌─┐
q_0: ┤ H ├──■──┤M├───
     └───┘┌─┴─┐└╥┘┌─┐
q_1: ─────┤ X ├─╫─┤M├
          └───┘ ║ └╥┘
c: 2/═══════════╩══╩═
                0  1
```

La puerta H pone a q0 en (|0⟩ + |1⟩)/√2 y la CNOT copia ese valor en q1, lo que produce (|00⟩ + |11⟩)/√2. Los dos qubits no tienen un valor individual definido, pero al medirlos siempre coinciden.

### Deutsch-Jozsa (oráculo balanceado)

```
     ┌───┐      ░            ░ ┌───┐┌─┐
q_0: ┤ H ├──────░───■────────░─┤ H ├┤M├───
     ├───┤      ░   │        ░ ├───┤└╥┘┌─┐
q_1: ┤ H ├──────░───┼────■───░─┤ H ├─╫─┤M├
     ├───┤┌───┐ ░ ┌─┴─┐┌─┴─┐ ░ └───┘ ║ └╥┘
q_2: ┤ X ├┤ H ├─░─┤ X ├┤ X ├─░───────╫──╫─
     └───┘└───┘ ░ └───┘└───┘ ░       ║  ║
c: 2/════════════════════════════════╩══╩═
                                     0  1
```

El ancilla q2 empieza en |−⟩ = H|1⟩. Así, el oráculo no cambia el ancilla sino la fase de cada entrada: (−1)^f(x). Las H finales hacen interferir las cuatro entradas. Si f es constante, todas tienen la misma fase y la interferencia deja solo |00⟩; si f es balanceada, las fases se cancelan en |00⟩ y la probabilidad de medirlo es exactamente 0.

### Grover (objetivo |01⟩)

```
     ┌───┐ ░               ░ ┌───┐┌───┐   ┌───┐┌───┐┌─┐
q_0: ┤ H ├─░───────■───────░─┤ H ├┤ X ├─■─┤ X ├┤ H ├┤M├───
     ├───┤ ░ ┌───┐ │ ┌───┐ ░ ├───┤├───┤ │ ├───┤├───┤└╥┘┌─┐
q_1: ┤ H ├─░─┤ X ├─■─┤ X ├─░─┤ H ├┤ X ├─■─┤ X ├┤ H ├─╫─┤M├
     └───┘ ░ └───┘   └───┘ ░ └───┘└───┘   └───┘└───┘ ║ └╥┘
c: 2/════════════════════════════════════════════════╩══╩═
                                                     0  1
```

Después de las H, los 4 estados tienen amplitud 1/2. El oráculo invierte el signo del objetivo, que queda en −1/2, y la media de las amplitudes baja a 1/4. El difusor refleja cada amplitud respecto de esa media: los estados no marcados pasan de 1/2 a 2·(1/4) − 1/2 = 0, y el marcado de −1/2 a 2·(1/4) + 1/2 = 1. Con N = 4, una iteración lleva la probabilidad del objetivo exactamente al 100 %. El número óptimo de iteraciones es ⌊(π/4)·√N⌋ = ⌊1,57⌋ = 1; una segunda iteración haría que la amplitud se pasara del máximo y bajara.

## Resultados

### Estado de Bell y Deutsch-Jozsa

| Experimento | Resultado (1024 shots) | Interpretación |
|---|---|---|
| Estado de Bell | `|00⟩`: 500 (48,8 %), `|11⟩`: 524 (51,2 %), `|01⟩` y `|10⟩`: 0 | Cada qubit por separado es aleatorio, pero los dos coinciden siempre: correlación perfecta por entrelazamiento. La diferencia frente a 50/50 está dentro de la variación estadística esperada, de unos ±16 conteos con 1024 shots. |
| Deutsch-Jozsa, oráculo constante | `{'00': 1024}` | Todos los shots dan 00: la función es constante. |
| Deutsch-Jozsa, oráculo balanceado | `{'11': 1024}` | Ningún shot da 00: la función f(x) = x0 ⊕ x1 es balanceada. |

**Por qué basta una evaluación del oráculo.** Un algoritmo clásico debe evaluar f en entradas concretas. Con n = 2 hay 4 entradas; si las dos primeras dan el mismo valor, todavía puede ser balanceada, así que en el peor caso necesita 2ⁿ⁻¹ + 1 = 3 evaluaciones. Deutsch-Jozsa evalúa el oráculo una sola vez sobre la superposición de las 4 entradas, y el resultado de las 4 queda codificado en las fases. La interferencia final concentra toda la amplitud en |00⟩ si f es constante y la anula por completo si es balanceada, por eso el resultado es determinista y no estadístico.

### Grover sin ruido

| Objetivo | Conteo del objetivo (de 1024) | Probabilidad | Estado más probable |
|---|---|---|---|
| `|00⟩` | 1024 | 100,0 % | `|00⟩`, CORRECTO |
| `|01⟩` | 1024 | 100,0 % | `|01⟩`, CORRECTO |
| `|10⟩` | 1024 | 100,0 % | `|10⟩`, CORRECTO |
| `|11⟩` | 1024 | 100,0 % | `|11⟩`, CORRECTO |

Los cuatro objetivos se encuentran con el 100 % de los shots, como predice el cálculo de amplitudes de la sección anterior.

### Grover con ruido

**Comparación con y sin ruido** (`grover_noise.py`, objetivo `|11⟩`, 1024 shots, p1q = 0,1 % y p2q = 1 %):

| Simulación | Éxito en `|11⟩` | Conteos |
|---|---|---|
| Sin ruido | 100,0 % | `{'11': 1024}` |
| Ruido despolarizante | 97,8 % | `{'00': 7, '01': 9, '10': 7, '11': 1001}` |
| Ruido calibrado de FakeBrisbane (`backend`) | 93,3 % | `{'00': 5, '01': 32, '10': 32, '11': 955}` |

La degradación con ruido despolarizante es de 2,2 puntos, menor que los 10 puntos del ejemplo de la guía. El valor medido es el que corresponde a las tasas configuradas: el circuito tiene 10 puertas de 1 qubit y 2 CZ, así que la probabilidad de que ocurra al menos un error es 1 − 0,999¹⁰ · 0,99² ≈ 3 %. Un error despolarizante deja el estado completamente mezclado, y en ese caso todavía se mide `|11⟩` con probabilidad 1/4, así que la pérdida esperada es 3 % · 3/4 ≈ 2,2 puntos, justo lo medido. Para perder 10 puntos con este circuito, el error de la CZ tendría que ser de alrededor del 6 %.

**Efecto de la profundidad** (`grover_noise.py profundidad`, 4096 shots): se agregan antes de medir pares CZ-CZ, que juntos equivalen a no hacer nada, de modo que el resultado ideal sigue siendo 100 %.

| Pares CZ-CZ extra | CZ totales | Éxito medido en `|11⟩` | Predicción 1/4 + 3/4 · 0,99^CZ · 0,999¹⁰ |
|---|---|---|---|
| 0 | 2 | 98,1 % | 97,8 % |
| 5 | 12 | 90,9 % | 90,8 % |
| 10 | 22 | 84,9 % | 84,5 % |
| 20 | 42 | 74,4 % | 73,7 % |
| 50 | 102 | 51,8 % | 51,6 % |
| 100 | 202 | 35,2 % | 34,8 % |

La fila de 0 pares repite el experimento anterior con otros 4096 shots, por eso da 98,1 % en vez de 97,8 %. Los valores medidos coinciden con la predicción con diferencias menores a un punto, lo que confirma que el error se acumula como se describe. La probabilidad de éxito no baja de forma lineal sino exponencial con el número de CZ, y tiende al 25 % que se obtendría adivinando uno de los 4 estados al azar.

## Decisión 1: ¿el resultado de Grover con ruido sigue siendo útil, o requiere corrección de errores?

**Decisión: para este circuito de 2 qubits el resultado es útil sin corrección de errores; para circuitos de decenas de qubits y cientos de puertas de 2 qubits, la corrección de errores es indispensable.**

Con el ruido configurado, `|11⟩` obtuvo 1001 de 1024 shots (97,8 %), y el siguiente estado, `|01⟩`, solo 9. La diferencia es de más de cien veces, muy por encima de la variación estadística de 1024 shots, de unos ±3 conteos para estados con probabilidad cercana al 1 %. La respuesta se identifica con total confianza. Incluso con el modelo calibrado de un procesador IBM, más pesimista, `|11⟩` obtuvo el 93,3 %.

El problema aparece al escalar. El experimento de profundidad muestra que el error no se suma de forma lineal: la parte del estado que sobrevive sin errores se multiplica por 0,99 en cada CZ. Con 102 CZ el éxito bajó al 51,8 % y con 202 CZ al 35,2 %, muy cerca del 25 % de una elección al azar; la columna de predicción de la tabla reproduce esos valores con la fórmula 1/4 + 3/4 · 0,99^CZ. Un Grover real de 10 qubits necesita unas ⌊(π/4)·√1024⌋ = 25 iteraciones, y cada iteración incluye un Z controlado por 9 qubits que se descompone en decenas de puertas de 2 qubits: el circuito suma del orden de mil CZ. Con 0,99¹⁰⁰⁰ ≈ 4 · 10⁻⁵, el resultado sería indistinguible de elegir uno de los 1024 estados al azar.

Por eso, ejecutar directamente sobre qubits físicos es razonable mientras el número de puertas de 2 qubits multiplicado por su tasa de error se mantenga muy por debajo de 1: con un 1 % de error, unas pocas decenas de CZ. Además, p2q = 1 % está en el límite del umbral del código de superficie, donde agregar qubits de corrección casi no ayuda. Algoritmos con utilidad práctica, como Shor sobre RSA-2048 o la simulación química de moléculas grandes, necesitan miles de millones de puertas, y solo son posibles con qubits lógicos protegidos por corrección de errores y con tasas físicas claramente por debajo del umbral.

## Decisión 2: ¿qué tan representativo es el modelo de ruido despolarizante frente al hardware NISQ real?

**Decisión: el modelo despolarizante es adecuado para este laboratorio, pero para predecir el resultado en un procesador IBM concreto se debe usar `NoiseModel.from_backend()` con su calibración más reciente.**

El modelo despolarizante trata todos los errores como equivalentes: con cierta probabilidad, el estado se reemplaza por uno completamente mezclado, igual en cualquier qubit y en cualquier momento. El hardware real no funciona así, y el experimento `backend` lo muestra. Con la calibración de FakeBrisbane, el éxito fue del 93,3 %, frente al 97,8 % del modelo despolarizante, y los errores no se repartieron por igual: `|01⟩` y `|10⟩` recibieron 32 conteos cada uno y `|00⟩` solo 5. Es el patrón de errores de un solo bit, que el modelo despolarizante no produce (allí los tres estados erróneos recibieron entre 7 y 9).

Ese patrón tiene tres causas que el modelo simple ignora. Primero, el error de lectura: en esa calibración, la mediana es del 2 % por qubit, así que leer correctamente los dos qubits solo ocurre el 96 % de las veces, aunque las puertas no tengan error. Segundo, la relajación T1: un qubit en |1⟩ tiende a decaer a |0⟩ (mediana de T1 de 232 µs y de T2 de 150 µs), y como el objetivo es `|11⟩`, los decaimientos de un qubit producen justamente `|01⟩` o `|10⟩`. Tercero, la duración de las puertas: tras transpilar, el circuito usa 2 puertas ECR de 2 qubits, que tardan 660 ns, once veces más que una puerta SX de 1 qubit (60 ns), y durante ese tiempo los qubits acumulan más decoherencia. Las tasas también cambian entre qubits y entre pares acoplados.

Aun así, el modelo despolarizante es apropiado aquí. El objetivo pedagógico es mostrar de forma controlada y reproducible que el ruido degrada el resultado y cómo se acumula con la profundidad, y para eso un solo parámetro por tipo de puerta permite razonar el resultado a mano, como en la fórmula de la tabla de profundidad. Un modelo calibrado ata el experimento a un dispositivo y a una calibración que cambia cada día. Pero si el objetivo fuera anticipar el resultado en un procesador IBM específico antes de ejecutarlo, el modelo simple subestimaría el error (en este caso, en 4,5 puntos) y no reproduciría su forma; la elección correcta sería `NoiseModel.from_backend()` con los datos de calibración más recientes de ese backend.

## Capturas

| Captura | Contenido |
|---|---|
| `capturas/cap01_instalacion.png` | Versiones de Python, Qiskit y Aer |
| `capturas/cap02_bell.png` | Checkpoint 1: estado de Bell y verificación |
| `capturas/bell_histogram.png` | Histograma del estado de Bell |
| `capturas/cap03_deutsch_jozsa.png` | Checkpoint 2: Deutsch-Jozsa con ambos oráculos |
| `capturas/cap04_grover.png` | Checkpoint 3: Grover para los 4 objetivos |
| `capturas/grover_00.png`, `grover_01.png`, `grover_10.png`, `grover_11.png` | Histogramas de Grover |
| `capturas/cap05_grover_ruido.png` | Checkpoint 4: Grover con y sin ruido |
| `capturas/grover_noise_comparison.png` | Histogramas con y sin ruido lado a lado |
| `capturas/cap06_ruido_profundidad.png` | Decisión 1: efecto de la profundidad |
| `capturas/cap07_ruido_backend.png` | Decisión 2: ruido calibrado de FakeBrisbane |
| `capturas/cap08_decision1.png` | Checkpoint 5: Decisión 1 |
| `capturas/cap09_decision2.png` | Checkpoint 5: Decisión 2 |
