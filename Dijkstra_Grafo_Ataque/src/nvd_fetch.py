"""
nvd_fetch.py — Obtención de CVEs reales desde la National Vulnerability Database.

Estrategia:
  1. Intentar la API pública del NVD (services.nvd.nist.gov/rest/json/cves/2.0)
     filtrando por severidad y palabras clave de productos típicos de una red
     corporativa (web server, SMB, RDP, VPN, base de datos…).
  2. Si la API falla (sin internet / rate-limit), usar un dataset EMBEBIDO de
     CVEs reales y conocidos con su CVSS v3 real (Log4Shell, EternalBlue, …).

Cada CVE se normaliza a un dict:
  { id, cvss, severity, product, vector_layer, description }

`vector_layer` clasifica la vulnerabilidad en una capa de la cadena de ataque
(perímetro → servicio → host → activo crítico) para poder cablear el grafo.
"""

import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"

# Productos/keywords que representan capas de una infraestructura típica.
# El orden define la "profundidad" en la cadena de ataque.
LAYER_KEYWORDS = {
    "perimeter": ["vpn", "firewall", "fortinet", "citrix", "ssl-vpn"],
    "web":       ["apache", "nginx", "tomcat", "log4j", "struts", "http server"],
    "service":   ["smb", "rdp", "remote desktop", "exchange", "samba"],
    "host":      ["windows", "linux kernel", "sudo", "privilege escalation"],
    "data":      ["mysql", "postgresql", "mssql", "oracle database", "mongodb"],
}

# ── Dataset embebido (CVEs reales, CVSS v3 real) ────────────────────────────────
# Fuente de los puntajes: registros oficiales NVD. Se usa como fallback offline.
EMBEDDED_CVES = [
    {"id": "CVE-2018-13379", "cvss": 9.8, "product": "Fortinet FortiOS SSL VPN",      "vector_layer": "perimeter", "description": "Path traversal en SSL VPN permite leer ficheros de sesión sin autenticar."},
    {"id": "CVE-2019-19781", "cvss": 9.8, "product": "Citrix ADC / Gateway",          "vector_layer": "perimeter", "description": "Directory traversal permite ejecución remota de código en el perímetro."},
    {"id": "CVE-2023-27997", "cvss": 9.8, "product": "Fortinet FortiOS",              "vector_layer": "perimeter", "description": "Heap overflow pre-auth en SSL-VPN (XORtigate)."},
    {"id": "CVE-2021-44228", "cvss": 10.0, "product": "Apache Log4j (Log4Shell)",     "vector_layer": "web",       "description": "JNDI lookup permite RCE no autenticado en aplicaciones Java."},
    {"id": "CVE-2017-5638",  "cvss": 10.0, "product": "Apache Struts 2",              "vector_layer": "web",       "description": "RCE vía Content-Type en el parser Jakarta Multipart."},
    {"id": "CVE-2021-41773", "cvss": 7.5,  "product": "Apache HTTP Server 2.4.49",    "vector_layer": "web",       "description": "Path traversal y RCE en servidor web mal configurado."},
    {"id": "CVE-2022-22965", "cvss": 9.8,  "product": "Spring Framework (Spring4Shell)","vector_layer": "web",     "description": "RCE por data binding en aplicaciones Spring sobre Tomcat."},
    {"id": "CVE-2017-0144",  "cvss": 8.1,  "product": "Microsoft SMBv1 (EternalBlue)", "vector_layer": "service",  "description": "RCE en SMBv1 explotado por WannaCry/NotPetya."},
    {"id": "CVE-2019-0708",  "cvss": 9.8,  "product": "Microsoft RDP (BlueKeep)",      "vector_layer": "service",  "description": "RCE pre-auth en Remote Desktop Services, gusano potencial."},
    {"id": "CVE-2021-26855", "cvss": 9.8,  "product": "Microsoft Exchange (ProxyLogon)","vector_layer": "service", "description": "SSRF que permite autenticación y RCE en Exchange."},
    {"id": "CVE-2020-1472",  "cvss": 10.0, "product": "Microsoft Netlogon (Zerologon)","vector_layer": "host",     "description": "Escalada a Domain Admin por fallo criptográfico en Netlogon."},
    {"id": "CVE-2021-4034",  "cvss": 7.8,  "product": "Polkit pkexec (PwnKit)",        "vector_layer": "host",     "description": "Escalada local a root en pkexec presente por defecto en Linux."},
    {"id": "CVE-2021-3156",  "cvss": 7.8,  "product": "Sudo (Baron Samedit)",          "vector_layer": "host",     "description": "Heap overflow en sudo permite escalada local a root."},
    {"id": "CVE-2022-0847",  "cvss": 7.8,  "product": "Linux Kernel (Dirty Pipe)",     "vector_layer": "host",     "description": "Sobrescritura de ficheros de solo lectura → escalada a root."},
    {"id": "CVE-2012-2122",  "cvss": 5.9,  "product": "MySQL/MariaDB auth bypass",     "vector_layer": "data",     "description": "Bypass de autenticación por comparación de hash defectuosa."},
    {"id": "CVE-2019-10149", "cvss": 9.8,  "product": "Exim MTA",                      "vector_layer": "data",     "description": "RCE en servidor de correo, pivote hacia almacenamiento."},
    {"id": "CVE-2020-2555",  "cvss": 9.8,  "product": "Oracle Coherence (WebLogic)",   "vector_layer": "data",     "description": "Deserialización insegura → RCE sobre la capa de datos."},
    {"id": "CVE-2023-21554", "cvss": 9.8,  "product": "Microsoft MSMQ (QueueJumper)",  "vector_layer": "service",  "description": "RCE pre-auth en el servicio de colas de mensajes."},
    {"id": "CVE-2014-0160",  "cvss": 7.5,  "product": "OpenSSL (Heartbleed)",          "vector_layer": "perimeter","description": "Fuga de memoria expone claves y credenciales en TLS."},
    {"id": "CVE-2020-5902",  "cvss": 9.8,  "product": "F5 BIG-IP TMUI",                "vector_layer": "perimeter","description": "RCE en la interfaz de gestión del balanceador."},
]


def _severity(cvss: float) -> str:
    if cvss >= 9.0:  return "CRITICAL"
    if cvss >= 7.0:  return "HIGH"
    if cvss >= 4.0:  return "MEDIUM"
    return "LOW"


def _classify_layer(text: str) -> str:
    t = text.lower()
    for layer, kws in LAYER_KEYWORDS.items():
        if any(kw in t for kw in kws):
            return layer
    return "host"  # capa por defecto


def fetch_from_nvd(results_per_layer: int = 6, timeout: int = 20) -> list:
    """Descarga CVEs reales del NVD por capa. Devuelve [] si algo falla."""
    collected = []
    seen = set()
    try:
        for layer, kws in LAYER_KEYWORDS.items():
            kw = kws[0]
            params = urllib.parse.urlencode({
                "keywordSearch": kw,
                "cvssV3Severity": "HIGH",
                "resultsPerPage": results_per_layer,
            })
            url = f"{NVD_API}?{params}"
            req = urllib.request.Request(url, headers={"User-Agent": "AttackGraphDijkstra/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read().decode())
            for item in data.get("vulnerabilities", []):
                cve = item["cve"]
                cid = cve["id"]
                if cid in seen:
                    continue
                metrics = cve.get("metrics", {})
                v31 = metrics.get("cvssMetricV31") or metrics.get("cvssMetricV30")
                if not v31:
                    continue
                score = v31[0]["cvssData"]["baseScore"]
                desc = next((d["value"] for d in cve.get("descriptions", []) if d["lang"] == "en"), "")
                collected.append({
                    "id": cid,
                    "cvss": float(score),
                    "severity": _severity(float(score)),
                    "product": kw.title(),
                    "vector_layer": layer,
                    "description": desc[:160],
                })
                seen.add(cid)
            time.sleep(6)  # respetar rate-limit del NVD sin API key
        return collected
    except Exception as e:
        print(f"  [NVD] API no disponible ({type(e).__name__}: {e}). Usando dataset embebido.")
        return []


def load_cves(use_live: bool = True, cache_path: str | None = None) -> tuple[list, str]:
    """
    Devuelve (lista_de_cves, fuente). fuente ∈ {'nvd-live','embedded'}.
    Cachea el resultado live en `cache_path` para reproducibilidad.
    """
    cves = []
    source = "embedded"
    if use_live:
        print("  [NVD] Consultando API live del NVD…")
        cves = fetch_from_nvd()
        if cves:
            source = "nvd-live"
            print(f"  [NVD] {len(cves)} CVEs reales descargados.")

    if not cves:
        cves = [dict(c, severity=_severity(c["cvss"])) for c in EMBEDDED_CVES]
        source = "embedded"
        print(f"  [NVD] Usando {len(cves)} CVEs reales embebidos.")

    if cache_path:
        Path(cache_path).parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump({"source": source, "cves": cves}, f, indent=2, ensure_ascii=False)

    return cves, source


if __name__ == "__main__":
    cves, src = load_cves(use_live=True, cache_path="data/cves_cache.json")
    print(f"\nFuente: {src}  |  Total: {len(cves)}")
    for c in cves[:5]:
        print(f"  {c['id']:18} CVSS {c['cvss']:<4} [{c['vector_layer']:9}] {c['product']}")
