# Impacto de la computación cuántica en la seguridad de los sistemas de información

**Arquitectura de Computadores, Unidad 12, Post-contenido (Parte 2)**
Maria Fernanda Becerra Coronel, código 1152509, Universidad Francisco de Paula Santander

## Introducción

La seguridad de casi todas las comunicaciones en internet depende de dos problemas matemáticos: factorizar enteros grandes (RSA) y calcular logaritmos discretos en curvas elípticas (ECDH, ECDSA, X25519). Ambos son intratables para un computador clásico, pero el algoritmo de Shor los resuelve en tiempo polinomial en un computador cuántico tolerante a fallos. Ese computador todavía no existe: la estimación más reciente indica que factorizar RSA-2048 requeriría menos de un millón de qubits físicos con una tasa de error de 0,1 % durante menos de una semana (Gidney, 2025), mientras que los procesadores actuales tienen del orden de mil qubits ruidosos. Sin embargo, la estrategia *harvest now, decrypt later* (HNDL) hace que el riesgo empiece hoy: un adversario puede guardar tráfico cifrado y descifrarlo cuando el hardware llegue. Este documento clasifica los algoritmos vulnerables, compara los tres estándares post-cuánticos que el NIST publicó en agosto de 2024, cuantifica su costo en bytes dentro de TLS 1.3 y propone un plan de migración para tres perfiles de organización.

## 1. Inventario de algoritmos y análisis de vulnerabilidad

| Algoritmo | Tipo | Vulnerabilidad cuántica | Algoritmo atacante | Acción recomendada |
|---|---|---|---|---|
| RSA-2048 / RSA-4096 | Cifrado y firma asimétricos | Roto completamente | Shor (factorización) | Reemplazar por ML-KEM para cifrado y ML-DSA para firma |
| ECDSA P-256 / P-384 | Firma digital | Roto completamente | Shor (logaritmo discreto en curvas) | Reemplazar por ML-DSA, o SLH-DSA para claves de larga vida |
| ECDH / X25519 | Intercambio de claves | Roto completamente | Shor | Reemplazar por ML-KEM, primero en modo híbrido |
| Ed25519 | Firma digital | Roto completamente | Shor | Reemplazar por ML-DSA |
| AES-128 | Cifrado simétrico | Debilitado: búsqueda de clave en unas 2⁶⁴ iteraciones | Grover | Migrar a AES-256 en datos de larga vida |
| AES-256 | Cifrado simétrico | Aceptable: unas 2¹²⁸ iteraciones | Grover | Mantener |
| SHA-256 | Función hash | Debilitado: preimagen en 2¹²⁸; colisiones en 2⁸⁵ en teoría | Grover; Brassard-Høyer-Tapp | Migrar a SHA-384 o SHA-512 donde se necesite resistencia a colisiones de largo plazo |
| SHA3-256 | Función hash | Debilitado igual que SHA-256 | Grover; Brassard-Høyer-Tapp | Usar SHA3-384 o mayor |

La diferencia entre las dos categorías es cualitativa. Un algoritmo **roto completamente** pierde toda su seguridad: Shor no reduce el trabajo del atacante en un factor constante, sino que convierte un problema exponencial en uno polinomial, y además afecta retroactivamente a todo lo que se cifró con él. Si una sesión TLS de 2026 se negoció con X25519, quien la haya grabado podrá recuperar la clave de sesión y leer todo su contenido. Un algoritmo **debilitado** pierde la mitad de sus bits de seguridad ante Grover, pero la seguridad restante sigue siendo suficiente si se duplica la clave. Además, Grover es difícil de paralelizar: dividir la búsqueda entre M máquinas solo reduce el tiempo en un factor √M, por lo que AES-128 sigue clasificado por el NIST como nivel de seguridad 1 (Bernstein & Lange, 2017; NIST, 2024a). La colisión de SHA-256 en 2⁸⁵ requiere además una memoria cuántica de tamaño comparable, lo que la hace menos práctica que una búsqueda clásica de colisiones.

En consecuencia, la prioridad de la migración está en la criptografía asimétrica. La simétrica se resuelve con un cambio de parámetros.

## 2. Estándares NIST PQC 2024

### 2.1 Problema matemático y uso

| Estándar | Origen | Tipo | Problema subyacente | Reemplaza a | Fuente |
|---|---|---|---|---|---|
| ML-KEM (FIPS 203) | CRYSTALS-Kyber | Encapsulamiento de claves (KEM) | Module Learning With Errors (MLWE) sobre retículos | ECDH, X25519 y cifrado RSA para establecer claves | NIST (2024a) |
| ML-DSA (FIPS 204) | CRYSTALS-Dilithium | Firma digital | MLWE y Module-SIS sobre retículos | ECDSA, Ed25519 y firmas RSA | NIST (2024b) |
| SLH-DSA (FIPS 205) | SPHINCS+ | Firma digital sin estado basada en hash | Resistencia de funciones hash (SHA-2 o SHAKE) | ECDSA y RSA cuando se prioriza una asunción conservadora | NIST (2024c) |

ML-KEM y ML-DSA se basan en que es difícil recuperar un vector secreto a partir de productos con una matriz pública a los que se les sumó un pequeño error aleatorio. Esa estructura hace que sus operaciones sean rápidas, pero también que su seguridad dependa de un problema estudiado intensamente solo desde hace unos 20 años. SLH-DSA, en cambio, solo supone que la función hash subyacente es segura, una asunción mucho más antigua y mínima: si SHA-2 cayera, casi toda la criptografía actual caería con ella. El precio es que sus firmas son grandes y la firma es lenta. Por eso el NIST lo presenta como alternativa de respaldo frente a un eventual avance de criptoanálisis contra los retículos (NIST, 2024c).

### 2.2 Tamaños por nivel de seguridad

| Parámetro | Nivel NIST | Clave pública (bytes) | Clave privada (bytes) | Ciphertext o firma (bytes) |
|---|---|---|---|---|
| ML-KEM-512 | 1 (≈ AES-128) | 800 | 1632 | 768 (ciphertext) |
| ML-KEM-768 | 3 (≈ AES-192) | 1184 | 2400 | 1088 (ciphertext) |
| ML-KEM-1024 | 5 (≈ AES-256) | 1568 | 3168 | 1568 (ciphertext) |
| ML-DSA-44 | 2 | 1312 | 2560 | 2420 (firma) |
| ML-DSA-65 | 3 | 1952 | 4032 | 3309 (firma) |
| ML-DSA-87 | 5 | 2592 | 4896 | 4627 (firma) |
| SLH-DSA-128s | 1 | 32 | 64 | 7856 (firma) |
| SLH-DSA-128f | 1 | 32 | 64 | 17 088 (firma) |
| SLH-DSA-256s | 5 | 64 | 128 | 29 792 (firma) |

Fuentes: NIST (2024a) para ML-KEM, NIST (2024b) para ML-DSA y NIST (2024c) para SLH-DSA. La clave secreta compartida que produce ML-KEM es de 32 bytes en los tres niveles.

### 2.3 Velocidad relativa

| Algoritmo (nivel ≈ AES-128) | Firma (CPU relativa a Ed25519) | Verificación (CPU relativa a Ed25519) |
|---|---|---|
| Ed25519 | 1 | 1 |
| RSA-2048 | 70 | 0,3 |
| ML-DSA-44 | 4,8 | 0,5 |
| SLH-DSA-128s | 8000 | 2,8 |
| SLH-DSA-128f | 550 | 7 |

Fuente: Westerbaan (2024), con mediciones de Cloudflare; los valores varían según la plataforma.

La tabla muestra que ML-DSA verifica más rápido que Ed25519 y firma unas 5 veces más lento, lo que es aceptable para un servidor. SLH-DSA-128s, en cambio, tarda unas 8000 veces más que Ed25519 en firmar. ML-KEM es también rápido: su encapsulamiento cuesta del orden de decenas de microsegundos, comparable con X25519, de modo que su costo real en TLS no es el cómputo sino los bytes (Bos et al., 2018).
