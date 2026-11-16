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

## 3. Comparación de tamaños con la criptografía clásica e impacto en TLS 1.3 híbrido

| Algoritmo | Tipo | Clave pública | Clave privada | Firma o ciphertext | Nivel de seguridad | Fuente |
|---|---|---|---|---|---|---|
| RSA-3072 | Cifrado y firma clásicos | ≈ 400 bytes (módulo de 384 bytes más exponente y codificación) | ≈ 1600 bytes | 384 bytes (firma) | ≈ 128 bits clásicos, no post-cuántico | NIST (2023) |
| ECDSA P-256 | Firma clásica | 64 bytes | 32 bytes | 64 bytes en bruto; 70–72 en DER | ≈ 128 bits clásicos, no post-cuántico | NIST (2023) |
| X25519 | Intercambio de claves clásico | 32 bytes | 32 bytes | No aplica | ≈ 128 bits clásicos, no post-cuántico | Langley et al. (2016) |
| ML-KEM-768 | KEM post-cuántico | 1184 bytes | 2400 bytes | 1088 bytes (ciphertext) | Nivel NIST 3 | NIST (2024a) |
| ML-DSA-65 | Firma post-cuántica | 1952 bytes | 4032 bytes | 3309 bytes | Nivel NIST 3 | NIST (2024b) |
| SLH-DSA-128s | Firma post-cuántica basada en hash | 32 bytes | 64 bytes | 7856 bytes | Nivel NIST 1 | NIST (2024c) |

La clave pública de ML-KEM-768 es 37 veces mayor que la de X25519 (1184 frente a 32 bytes), y una firma ML-DSA-65 es 46 veces mayor que una firma ECDSA P-256 en DER (3309 frente a unos 72 bytes).

**Intercambio de claves.** En TLS 1.3, el grupo híbrido X25519MLKEM768 concatena las dos claves. El campo `key_share` del ClientHello pasa de 32 bytes a 32 + 1184 = 1216 bytes, y el del ServerHello de 32 a 32 + 1088 = 1120 bytes. Un ClientHello clásico ocupa unos pocos cientos de bytes, así que con el componente post-cuántico suele superar el tamaño de un paquete Ethernet de 1500 bytes y dividirse en dos segmentos TCP. Eso no agrega una ida y vuelta, porque la ventana de congestión inicial de TCP es de 10 segmentos, unos 14 600 bytes (Chu et al., 2013). El problema que sí apareció en la práctica fue de compatibilidad: algunos balanceadores y *middleboxes* suponían que el ClientHello siempre cabe en un solo paquete y cortaban la conexión (Westerbaan, 2024). Chrome activó el intercambio híbrido por defecto en 2024 y adoptó el nombre estandarizado X25519MLKEM768 en su versión 131 (Google, 2024).

**Firmas y certificados.** El mayor costo aparece si también se migra la autenticación. Una cadena típica envía dos certificados, cada uno con una clave pública y una firma, más la firma `CertificateVerify` del handshake. Con ML-DSA-65 eso suma 2 × (1952 + 3309) + 3309 = 13 831 bytes solo en material criptográfico, frente a unos 2 × (64 + 72) + 72 ≈ 350 bytes con ECDSA P-256. Sumando el ServerHello híbrido y la codificación de los certificados, la respuesta del servidor ronda o supera los 14 600 bytes de la ventana inicial; cuando los supera, el servidor debe esperar un acuse de recibo antes de terminar de enviar: una ida y vuelta adicional. En una red con 30 ms de latencia es casi imperceptible, pero en una red móvil con 200 ms y pérdida de paquetes se nota. Por eso la industria migró primero el intercambio de claves, que protege contra HNDL con un costo bajo, y la autenticación avanza más lento (Westerbaan, 2024).

## 4. Plan de migración para tres perfiles

Los tres planes siguen las cinco etapas que recomiendan CISA, NSA y NIST (2023): inventario, clasificación de los datos por horizonte de sensibilidad, criptografía híbrida como transición, cronograma por fases y gestión de riesgos. La prioridad se calcula con la desigualdad de Mosca: si el tiempo que los datos deben permanecer seguros (x) más el tiempo que toma migrar (y) supera el tiempo que falta para un computador cuántico relevante (z), la migración ya está atrasada (Mosca, 2018). Con z estimado entre 2030 y 2035, una migración de 3 años implica que todo dato con x mayor que unos 4 a 9 años ya está expuesto.

### Perfil A: hospital universitario

- **Inventario.** El TLS del portal de pacientes (X25519 y certificados ECDSA), las VPN con las sedes, la firma ECDSA de prescripciones, las copias de respaldo cifradas y las integraciones HL7/FHIR con aseguradoras.
- **Clasificación.** La historia clínica debe ser confidencial durante 50 a 75 años, así que x ≫ z: es el caso más expuesto a HNDL. Las prescripciones requieren autenticidad en el momento de emisión, no confidencialidad de largo plazo.
- **Estrategia híbrida.** X25519MLKEM768 en el portal y en las VPN; ML-KEM-1024 para el cifrado de respaldos de largo plazo; ML-DSA-65 para firmar prescripciones (ver Decisión 3).
- **Cronograma.** Fase 1, primer semestre: inventario y activación del intercambio híbrido en el portal, donde los navegadores ya lo soportan. Fase 2, primer año: VPN entre sedes e integraciones con terceros. Fase 3, segundo año: certificados y firma de prescripciones con ML-DSA. Fase 4, tercer año: re-cifrado de respaldos y archivos históricos con claves derivadas de ML-KEM y AES-256.
- **Riesgos y mitigación.** Equipos médicos con firmware antiguo que no soportan TLS 1.3: aislarlos tras una pasarela que termine el TLS híbrido. Integraciones con aseguradoras sin soporte: el modo híbrido permite caer al algoritmo clásico sin cortar el servicio mientras se negocia el cambio.

### Perfil B: startup de comercio electrónico

- **Inventario.** TLS 1.3 con X25519 y ECDSA en la tienda y la API, tokens de sesión, cifrado AES-256 de la base de datos y la integración con la pasarela de pagos certificada PCI-DSS.
- **Clasificación.** Los datos de tarjetas tienen una vida de 5 a 7 años; los datos de compras y de clientes, algo más. Con x ≈ 7 y z ≈ 2030-2035, el riesgo existe pero es menor que en salud.
- **Estrategia híbrida.** X25519MLKEM768 en el CDN y el balanceador, que en la mayoría de los proveedores ya es una opción de configuración. AES-256 se mantiene.
- **Cronograma.** Fase 1, primer trimestre: activar el intercambio híbrido en el CDN y medir la tasa de conexiones fallidas. Fase 2, primer año: exigirlo en las conexiones entre servicios internos y con la pasarela de pagos. Fase 3, entre 2028 y 2030: certificados ML-DSA cuando los emitan las autoridades de certificación públicas.
- **Riesgos y mitigación.** Clientes con *middleboxes* antiguos: el modo híbrido mantiene la compatibilidad. Sobrecosto en el handshake: medir el tiempo hasta el primer byte antes y después de activarlo.

### Perfil C: entidad gubernamental de defensa

- **Inventario.** La PKI nacional para documentos oficiales, las VPN entre agencias, los enlaces de comunicaciones clasificadas, la firma de software y firmware de los equipos.
- **Clasificación.** Sensibilidad de 25 a 50 años. Es el caso con mayor x y el que tiene plazos obligatorios.
- **Estrategia.** CNSA 2.0 exige ML-KEM-1024, ML-DSA-87, AES-256 y SHA-384, más LMS o XMSS para la firma de firmware (NSA, 2022). El modo híbrido sirve solo como paso intermedio.
- **Cronograma según CNSA 2.0.** Firma de software y firmware: soportar y preferir PQC desde 2025, uso exclusivo en 2030. Equipos de red como VPN y enrutadores: soportar desde 2026, exclusivo en 2030. Navegadores, servidores y nube: soportar desde 2025, exclusivo en 2033. Sistemas operativos: soportar desde 2027, exclusivo en 2033 (NSA, 2022).
- **Riesgos y mitigación.** Equipos legados sin capacidad de actualización: reemplazarlos dentro del plazo. Dependencia de un solo tipo de problema matemático: mantener SLH-DSA o LMS como respaldo para las raíces de la PKI.

## 5. Decisiones técnicas de la Parte 2

### Decisión 3: ¿qué algoritmo NIST es el correcto para firmar las prescripciones del Perfil A?

ML-KEM queda descartado de entrada. Es un mecanismo de encapsulamiento de claves: sirve para que dos partes acuerden un secreto compartido, pero no produce una firma que un tercero pueda verificar con una clave pública. Firmar una prescripción requiere probar quién la emitió y que no cambió, y eso solo lo ofrecen ML-DSA y SLH-DSA (NIST, 2024a).

Entre los dos esquemas de firma, el volumen y la latencia favorecen a ML-DSA-65. Su firma ocupa 3309 bytes, frente a los 7856 de SLH-DSA-128s, es decir, 2,4 veces menos espacio por prescripción almacenada y transmitida. La diferencia en tiempo de firma es mayor todavía: en las mediciones de Cloudflare al nivel de AES-128, ML-DSA firma unas 4,8 veces más lento que Ed25519, mientras que SLH-DSA-128s tarda unas 8000 veces más (Westerbaan, 2024). Con miles de prescripciones al día firmadas en el momento en que el médico las emite, SLH-DSA-128s introduciría una espera visible en el portal; ML-DSA no.

El argumento conservador a favor de SLH-DSA no se aplica a este caso. La amenaza HNDL afecta la confidencialidad: un dato cifrado hoy puede leerse en el futuro. Una firma, en cambio, demuestra la autenticidad en el momento de la emisión. Si dentro de 30 años se rompiera ML-DSA, el atacante podría falsificar firmas nuevas, pero eso no cambia que la prescripción original fue verificada y registrada cuando se emitió. El horizonte de 50 a 75 años de la historia clínica obliga a cifrarla con ML-KEM, no a firmar cada prescripción con el esquema más lento. Se recomienda ML-DSA-65 como algoritmo principal y SLH-DSA para los certificados raíz del hospital, que se firman pocas veces, deben durar décadas y son los que más se benefician de una asunción de seguridad independiente de los retículos.

### Decisión 4: ¿modo híbrido permanente o etapa de transición para el Perfil B?

El modo híbrido conviene desde ahora porque su costo es bajo y su beneficio es alto. En la Sección 3 se calculó que X25519MLKEM768 agrega 1184 bytes al ClientHello y 1088 al ServerHello; eso cabe dentro de la ventana inicial de TCP de unos 14 600 bytes y no agrega idas y vueltas en una conexión normal. Además, la startup no necesita desarrollar nada: los navegadores y los CDN ya lo negocian por defecto (Google, 2024). Esperar a que la migración sea obligatoria no ahorraría casi nada y dejaría expuesto al HNDL el tráfico de los próximos años, cuyos datos de clientes siguen siendo sensibles durante 5 a 7 años.

La doble protección es valiosa porque los dos riesgos son independientes. Un computador cuántico rompería X25519, pero no ML-KEM. Un avance de criptoanálisis clásico contra MLWE rompería ML-KEM, pero no X25519. El riesgo del segundo caso no es teórico: SIKE, candidato de la cuarta ronda del mismo proceso del NIST, se rompió en 2022 con un computador portátil en unas horas, con un ataque clásico (Castryck & Decru, 2023). ML-KEM tiene menos de una década de escrutinio público como estándar, mientras que las curvas elípticas acumulan más de 30 años. Mientras esa diferencia exista, combinar los dos garantiza que la sesión siga segura si cualquiera de ellos resiste.

Sin embargo, el modo híbrido no debe ser permanente. Duplica el código criptográfico que hay que mantener y auditar, y el componente clásico perderá su valor cuando un computador cuántico relevante sea una amenaza real. Lo razonable es planear el paso a ML-KEM puro cuando los algoritmos acumulen suficiente escrutinio y los estándares lo indiquen, con CNSA 2.0 como referencia: uso exclusivo de PQC en servidores y nube hacia 2033 (NSA, 2022). Como el Perfil B tiene datos de vida corta y menos exigencias regulatorias que el Perfil C, puede hacer ese cambio más tarde y con menor urgencia que una entidad de defensa.

## Conclusiones

La computación cuántica rompe por completo la criptografía asimétrica actual y solo debilita la simétrica, por lo que la migración se concentra en reemplazar RSA y las curvas elípticas. Los estándares del NIST de 2024 cubren las dos necesidades: ML-KEM para establecer claves y ML-DSA o SLH-DSA para firmar. Su principal costo no es el cómputo sino el tamaño: claves 37 veces mayores en el intercambio y firmas 46 veces mayores en la autenticación. Ese costo es pequeño en el intercambio de claves, que ya se despliega en modo híbrido, y significativo en los certificados, donde puede agregar una ida y vuelta al handshake. La urgencia de cada organización depende del horizonte de sus datos: un hospital con historias clínicas de 75 años debe empezar de inmediato, una tienda en línea puede apoyarse en lo que ya ofrecen su CDN y los navegadores, y una entidad de defensa debe seguir los plazos obligatorios de CNSA 2.0.

## Referencias

Bernstein, D. J., & Lange, T. (2017). Post-quantum cryptography. *Nature, 549*(7671), 188–194. https://doi.org/10.1038/nature23461

Bos, J., Ducas, L., Kiltz, E., Lepoint, T., Lyubashevsky, V., Schanck, J. M., Schwabe, P., Seiler, G., & Stehlé, D. (2018). CRYSTALS-Kyber: A CCA-secure module-lattice-based KEM. En *2018 IEEE European Symposium on Security and Privacy* (pp. 353–367). IEEE. https://doi.org/10.1109/EuroSP.2018.00032

Castryck, W., & Decru, T. (2023). An efficient key recovery attack on SIDH. En *Advances in Cryptology – EUROCRYPT 2023* (pp. 423–447). Springer. https://doi.org/10.1007/978-3-031-30589-4_15

Chu, J., Dukkipati, N., Cheng, Y., & Mathis, M. (2013). *Increasing TCP's initial window* (RFC 6928). Internet Engineering Task Force. https://doi.org/10.17487/RFC6928

Cybersecurity and Infrastructure Security Agency, National Security Agency, & National Institute of Standards and Technology. (2023). *Quantum-readiness: Migration to post-quantum cryptography* [Hoja informativa]. https://www.cisa.gov/resources-tools/resources/quantum-readiness-migration-post-quantum-cryptography

Gidney, C. (2025). *How to factor 2048 bit RSA integers with less than a million noisy qubits* (arXiv:2505.15917). arXiv. https://arxiv.org/abs/2505.15917

Google. (2024, septiembre). *A new path for Kyber on the web*. Google Online Security Blog. https://security.googleblog.com/

Langley, A., Hamburg, M., & Turner, S. (2016). *Elliptic curves for security* (RFC 7748). Internet Engineering Task Force. https://doi.org/10.17487/RFC7748

Mosca, M. (2018). Cybersecurity in an era with quantum computers: Will we be ready? *IEEE Security & Privacy, 16*(5), 38–41. https://doi.org/10.1109/MSP.2018.3761723

National Institute of Standards and Technology. (2023). *Digital signature standard (DSS)* (FIPS 186-5). https://doi.org/10.6028/NIST.FIPS.186-5

National Institute of Standards and Technology. (2024a). *Module-lattice-based key-encapsulation mechanism standard* (FIPS 203). https://doi.org/10.6028/NIST.FIPS.203

National Institute of Standards and Technology. (2024b). *Module-lattice-based digital signature standard* (FIPS 204). https://doi.org/10.6028/NIST.FIPS.204

National Institute of Standards and Technology. (2024c). *Stateless hash-based digital signature standard* (FIPS 205). https://doi.org/10.6028/NIST.FIPS.205

National Security Agency. (2022). *Announcing the Commercial National Security Algorithm Suite 2.0*. https://media.defense.gov/2022/Sep/07/2003071834/-1/-1/0/CSA_CNSA_2.0_ALGORITHMS_.PDF

Westerbaan, B. (2024, 5 de marzo). *The state of the post-quantum Internet*. The Cloudflare Blog. https://blog.cloudflare.com/pq-2024/
