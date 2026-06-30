# Dijkstra en Grafos de Ataque — Explicación del Proyecto

El proyecto modela ataques informáticos como un **problema de camino mínimo en grafos**.
La idea central es: si representamos una red de computadoras como un grafo donde las
aristas son vulnerabilidades reales, Dijkstra puede encontrar la **secuencia de ataque
de menor resistencia** que un atacante usaría para llegar a un activo crítico.

El proyecto tiene **dos análisis**: uno con una red sintética (para demostrar el concepto)
y uno con datos 100% reales del caso SolarWinds.

---

## 1. Análisis 1 — Red sintética con CVEs reales

### Por qué esta red

Se construyó una red corporativa ficticia pero **plausible**: tiene los mismos componentes
que tiene cualquier empresa mediana (firewall, servidores web, correo, Active Directory,
base de datos). Es sintética porque no existe una empresa real llamada `FW-VPN` o
`DB-CRITICAL`, pero su estructura refleja topologías reales documentadas en literatura
de seguridad. Se usó una red sintética para poder **controlar el experimento** y
demostrar el concepto de forma clara.

### Datos: los CVEs

Un **CVE** (Common Vulnerabilities and Exposures) es un identificador oficial de una
vulnerabilidad de seguridad en software real. Lo asigna el NIST/MITRE con el formato
`CVE-AÑO-NÚMERO`. Cada CVE tiene un puntaje **CVSS** (del 0 al 10) que mide su gravedad:

| Rango CVSS | Nivel |
|---|---|
| 9.0 – 10.0 | CRITICAL |
| 7.0 – 8.9 | HIGH |
| 4.0 – 6.9 | MEDIUM |
| 0.1 – 3.9 | LOW |

El proyecto usa **20 CVEs reales** con sus puntajes CVSS oficiales del NVD, organizados
por capa de red según el tipo de servicio que afectan:

| CVE | Nombre popular | CVSS | Capa | Qué hace |
|---|---|---|---|---|
| CVE-2018-13379 | Fortinet FortiOS SSL VPN | 9.8 | perimeter | Lee archivos de sesión sin autenticación |
| CVE-2019-19781 | Citrix ADC / Gateway | 9.8 | perimeter | Ejecución de código en el perímetro |
| CVE-2023-27997 | Fortinet FortiOS (XORtigate) | 9.8 | perimeter | Heap overflow pre-autenticación |
| CVE-2014-0160 | OpenSSL Heartbleed | 7.5 | perimeter | Filtra claves y credenciales TLS |
| CVE-2020-5902 | F5 BIG-IP | 9.8 | perimeter | RCE en el balanceador de carga |
| CVE-2021-44228 | Apache Log4j (Log4Shell) | 10.0 | web | RCE no autenticado en apps Java |
| CVE-2017-5638 | Apache Struts 2 | 10.0 | web | RCE vía cabecera HTTP maliciosa |
| CVE-2021-41773 | Apache HTTP Server 2.4.49 | 7.5 | web | Path traversal en servidor web |
| CVE-2022-22965 | Spring Framework (Spring4Shell) | 9.8 | web | RCE en apps Spring/Tomcat |
| CVE-2017-0144 | Microsoft SMBv1 (EternalBlue) | 8.1 | service | RCE en SMB, usado por WannaCry |
| CVE-2019-0708 | Microsoft RDP (BlueKeep) | 9.8 | service | Control remoto sin contraseña |
| CVE-2021-26855 | Microsoft Exchange (ProxyLogon) | 9.8 | service | RCE en servidor de correo |
| CVE-2023-21554 | Microsoft MSMQ (QueueJumper) | 9.8 | service | RCE en servicio de colas |
| CVE-2020-1472 | Microsoft Netlogon (Zerologon) | 10.0 | host | Escalada a Domain Admin |
| CVE-2021-4034 | Polkit pkexec (PwnKit) | 7.8 | host | Escalada a root en Linux |
| CVE-2021-3156 | Sudo (Baron Samedit) | 7.8 | host | Escalada a root vía sudo |
| CVE-2022-0847 | Linux Kernel (Dirty Pipe) | 7.8 | host | Sobrescritura de archivos → root |
| CVE-2012-2122 | MySQL/MariaDB auth bypass | 5.9 | data | Bypass de autenticación |
| CVE-2019-10149 | Exim MTA | 9.8 | data | RCE en servidor de correo → datos |
| CVE-2020-2555 | Oracle Coherence (WebLogic) | 9.8 | data | Deserialización insegura → RCE |

Los CVEs pueden obtenerse en tiempo real desde la API pública del NVD. Si no hay
conexión, el pipeline usa el dataset embebido anterior.

### Cómo se arma el grafo

La red está organizada en **6 capas**, de afuera hacia adentro:

```
INTERNET → Perímetro → Web/App → Servicios → Hosts/SO → Datos
```

**Nodos** — cada uno representa un host o servicio concreto:

| Nodo | Capa | Qué representa |
|---|---|---|
| `INTERNET` | internet | El atacante externo. Punto de partida |
| `FW-VPN` | perimeter | Firewall / concentrador VPN |
| `GW-EDGE` | perimeter | Gateway de borde (router de frontera) |
| `WEB-01` | web | Servidor web público |
| `APP-02` | web | Servidor de aplicaciones |
| `SMB-FILES` | service | Servidor de archivos compartidos (SMB) |
| `RDP-JUMP` | service | Servidor de acceso remoto (RDP) |
| `MAIL-EX` | service | Servidor de correo Exchange |
| `DC-01` | host | Controlador de dominio (Active Directory) |
| `WS-ADMIN` | host | Workstation del administrador de sistemas |
| `DB-CRITICAL` | data | Base de datos crítica. Objetivo final |

**Aristas** — hay dos mecanismos que definen qué nodos se conectan:

*Regla de capas (automático)*: solo se conectan capas consecutivas. Para cada nodo
destino se elige aleatoriamente un CVE del pool de su capa y se crea la arista:

```
FW-VPN  ──(CVE-2021-44228, w=0.1)──► APP-02
GW-EDGE ──(CVE-2022-22965, w=0.2)──► APP-02
FW-VPN  ──(CVE-2017-5638,  w=0.1)──► WEB-01
```

*Atajos manuales (hardcodeados)*: conexiones adicionales basadas en rutas de ataque
reales conocidas, para que existan caminos alternativos:

```
FW-VPN    → WEB-01        APP-02    → MAIL-EX
WEB-01    → SMB-FILES     SMB-FILES → DC-01
RDP-JUMP  → DC-01         MAIL-EX   → WS-ADMIN
DC-01     → DB-CRITICAL   WS-ADMIN  → DB-CRITICAL
```

La aleatoriedad usa `seed=42` para garantizar reproducibilidad.

### Los pesos

Cada arista tiene peso `w = 10 - CVSS`. Esta inversión es necesaria porque Dijkstra
minimiza costos: queremos que las vulnerabilidades más críticas (CVSS alto) tengan el
**menor costo** para el atacante, representando el camino de menor resistencia.

| CVSS | Peso w | Interpretación |
|---|---|---|
| 10.0 | 0.1 | Trivial para el atacante |
| 9.8 | 0.2 | Casi sin esfuerzo |
| 8.1 | 1.9 | Fácil de explotar |
| 7.5 | 2.5 | Moderado |
| 5.9 | 4.1 | Requiere más trabajo |

El mínimo es 0.1 (no 0) para que Dijkstra funcione con pesos estrictamente positivos.

Los CVEs definen el **peso** de cada arista, no la topología. La topología es
conocimiento experto hardcodeado; los CVEs solo ponen el precio a cada conexión.

---

## 2. Análisis 2 — Caso real: SolarWinds Compromise

### Por qué SolarWinds

SolarWinds Compromise (2019-2020) es uno de los ataques más documentados de la historia.
El grupo APT29 comprometió la cadena de suministro de SolarWinds Orion, afectando a
18,000 organizaciones incluyendo agencias del gobierno de EE.UU. MITRE ATT&CK lo
documentó exhaustivamente como campaña G0118, registrando cada técnica que el atacante
usó en el mundo real. Esto lo hace ideal para un análisis con datos 100% reales.

### Datos: MITRE ATT&CK

En lugar de CVEs, este análisis usa el framework **MITRE ATT&CK**: una base de
conocimiento pública que cataloga técnicas de ataque reales observadas en campo. Cada
técnica tiene un ID con el formato `TXXXX` o `TXXXX.XXX` (subtécnica).

La fuente de datos es el bundle **STIX 2.1** de ATT&CK Enterprise (~40 MB de JSON),
descargado directamente desde el repositorio oficial de MITRE en GitHub. Este bundle
contiene todas las técnicas, grupos, campañas y sus relaciones documentadas.

Del bundle se extraen solo las técnicas que ATT&CK documenta como usadas por SolarWinds,
organizadas en 15 tácticas ordenadas según la kill chain del atacante:

```
reconnaissance → resource-development → initial-access → execution →
persistence → privilege-escalation → defense-impairment → stealth →
credential-access → discovery → lateral-movement → collection →
command-and-control → exfiltration → impact
```

### Cómo se arma el grafo

**Nodos** — cada nodo es una técnica ATT&CK real usada por SolarWinds. Por ejemplo:

| ID | Nombre | Táctica | Qué hizo SolarWinds |
|---|---|---|---|
| `T1195.002` | Supply Chain Compromise | initial-access | Insertó SUNBURST en el software de Orion |
| `T1078` | Valid Accounts | initial-access / persistence | Usó credenciales legítimas robadas |
| `T1027` | Obfuscated Files | defense-impairment | Ofuscó el malware SUNBURST para evadir detección |
| `T1558.003` | Kerberoasting | credential-access | Robó tickets Kerberos para moverse lateralmente |
| `T1021.001` | Remote Desktop Protocol | lateral-movement | Se movió entre sistemas vía RDP |
| `T1071.001` | Web Protocols | command-and-control | Usó HTTP para comunicación C2 encubierta |

Más dos nodos de frontera: `ATTACKER` (atacante externo) e `IMPACT` (objetivo logrado).

**Aristas** — solo existen entre técnicas de tácticas consecutivas que SolarWinds
**realmente usó**. Si la campaña usó técnicas A (en táctica i) y B (en táctica i+1),
existe una arista A→B. Esto representa la progresión real del atacante: primero
usaron initial-access, luego execution, luego persistence, etc.

### Los pesos

La fórmula de peso ya no es `10 - CVSS`. Ahora refleja **qué tan defendible es cada
técnica** según los datos reales del bundle STIX:

```
w = max(0.05, n_mitigaciones / max_mitigaciones_en_campaña)
```

Donde `n_mitigaciones` es el número de mitigaciones que ATT&CK documenta para esa
técnica. La lógica es:

- Más mitigaciones documentadas = más controles de defensa = **mayor costo** para el atacante (w alto)
- 0 mitigaciones = técnica sin contramedidas documentadas = **peso 0.05** (camino de mínima resistencia)

Dijkstra sobre estos pesos halla la ruta de **menor resistencia defensiva**: la secuencia
de técnicas con menos controles documentados. **No se usan pesos por CVE/CVSS** — la
asociación CVE↔técnica para una campaña no está en el bundle STIX y requería juicio manual
no reproducible (además contenía mapeos incorrectos). Todos los pesos derivan solo de
mitigaciones documentadas en ATT&CK.

Ejemplos de pesos reales calculados:

| Técnica | Nombre | Peso w | Fuente |
|---|---|---|---|
| `T1078.003` | Local Accounts | 0.50 | Mitigaciones: 4/8 |
| `T1606.001` | Web Cookies | 0.25 | Mitigaciones: 2/8 |
| `T1550.004` | Web Session Cookie | 0.125 | Mitigaciones: 1/8 |
| `T1016.001` | Internet Conn. Discovery | 0.05 | Mitigaciones: 0/8 |
| `T1048.002` | Exfiltración cifrada | 0.50 | Mitigaciones: 4/8 |

### Resumen de diferencias entre los dos análisis

| Aspecto | Análisis 1 (sintético) | Análisis 2 (SolarWinds) |
|---|---|---|
| **Red** | Ficticia pero plausible | Técnicas reales de ATT&CK |
| **Nodos** | Hosts/servicios (`FW-VPN`, `APP-02`…) | Técnicas de ataque (`T1078`, `T1027`…) |
| **Aristas** | Regla de capas + atajos manuales | Progresión táctica real documentada |
| **Pesos** | `10 - CVSS` | `max(0.05, mitigaciones / max)` (solo mitigaciones STIX) |
| **Datos** | CVEs del NVD | Bundle STIX de MITRE ATT&CK |
| **Objetivo** | Demostrar el concepto | Responder pregunta de investigación real |
