# Dijkstra en Grafos de Ataque — Explicación del Proyecto

## 1. Datos

### ¿Qué es un CVE?

Un **CVE** (Common Vulnerabilities and Exposures) es un identificador oficial y público de una vulnerabilidad de seguridad en software real. Cuando se descubre un fallo en un programa, se reporta al NIST/MITRE, que le asigna un ID único con el formato `CVE-AÑO-NÚMERO`.

Cada CVE tiene asociado un puntaje **CVSS** (Common Vulnerability Scoring System): un número del 0 al 10 que mide qué tan grave es el fallo, calculado en base a factores como:

- Vector de acceso (¿desde internet o solo local?)
- Complejidad de explotación
- Privilegios requeridos
- Impacto en confidencialidad, integridad y disponibilidad

| Rango CVSS | Nivel |
|---|---|
| 9.0 – 10.0 | CRITICAL |
| 7.0 – 8.9  | HIGH |
| 4.0 – 6.9  | MEDIUM |
| 0.1 – 3.9  | LOW |

### Dataset del proyecto

El proyecto usa **20 CVEs reales** con sus puntajes CVSS oficiales del NVD. Están organizados por capa de red según el tipo de servicio que afectan:

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

Los CVEs pueden obtenerse en tiempo real desde la API pública del NVD (`services.nvd.nist.gov`). Si no hay conexión, el pipeline usa el dataset embebido anterior.

---

## 2. El Grafo de Ataque

### ¿Qué modela?

Una infraestructura corporativa real donde un atacante externo intenta llegar a la base de datos crítica. La red se organiza en **6 capas**, de afuera hacia adentro:

```
INTERNET → Perímetro → Web/App → Servicios → Hosts/SO → Datos
```

### Nodos

Cada nodo representa un host o servicio concreto de la red:

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

### Aristas y pesos

Cada arista entre dos nodos representa una **vulnerabilidad CVE explotable**: estando en el nodo origen, explotar ese CVE permite al atacante avanzar al nodo destino.

El peso de cada arista es el **CVSS invertido**:

```
w = 10 - CVSS
```

Esta inversión es necesaria porque Dijkstra minimiza costos, y queremos que las vulnerabilidades más críticas (CVSS alto) sean las más "baratas" para el atacante:

| CVSS | Peso w | Interpretación |
|---|---|---|
| 10.0 | 0.1 | Trivial para el atacante |
| 9.8 | 0.2 | Casi sin esfuerzo |
| 8.1 | 1.9 | Fácil de explotar |
| 7.5 | 2.5 | Moderado |
| 5.9 | 4.1 | Requiere más trabajo |

El mínimo es 0.1 (no 0) para que Dijkstra funcione correctamente con pesos estrictamente positivos.

### ¿Quién define qué nodos se conectan?

Hay dos mecanismos:

**1. Regla de capas (automático)**

Solo se conectan capas consecutivas. El código recorre la cadena en orden y conecta cada nodo destino con al menos un nodo origen de la capa anterior. El CVE asignado a cada arista se elige aleatoriamente del pool de CVEs de la capa destino:

```
Perimeter → Web:  FW-VPN  ──(CVE-2021-44228, w=0.1)──► APP-02
                  GW-EDGE ──(CVE-2022-22965, w=0.2)──► APP-02
                  FW-VPN  ──(CVE-2017-5638,  w=0.1)──► WEB-01
```

**2. Atajos manuales (hardcodeados)**

Conexiones adicionales basadas en rutas de ataque reales conocidas, para que existan caminos alternativos y los cuellos de botella tengan sentido:

```python
("FW-VPN",    "WEB-01")       # firewall → servidor web
("GW-EDGE",   "APP-02")       # gateway  → app server
("WEB-01",    "SMB-FILES")    # web      → archivos compartidos
("APP-02",    "MAIL-EX")      # app      → correo
("SMB-FILES", "DC-01")        # archivos → controlador de dominio
("RDP-JUMP",  "DC-01")        # RDP      → controlador de dominio
("MAIL-EX",   "WS-ADMIN")     # correo   → workstation admin
("DC-01",     "DB-CRITICAL")  # dominio  → base de datos
("WS-ADMIN",  "DB-CRITICAL")  # admin    → base de datos
```

La aleatoriedad usa `seed=42` para garantizar reproducibilidad: el grafo resultante es siempre el mismo.

### Resumen del rol de cada tabla

| Elemento | Define |
|---|---|
| Nodos / capas | La estructura de la red (fija, hardcodeada) |
| Atajos manuales | Qué nodos específicos se conectan entre capas |
| CVEs | El peso (dificultad) de cada arista, no la topología |
