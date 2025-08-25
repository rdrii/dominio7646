import subprocess
import sys
import os
import time

# ================================
# 1️⃣ Verifica e instala pacotes
# ================================
def checar_e_instalar_pacote(pacote):
    try:
        __import__(pacote)
        print(f"[OK] Pacote '{pacote}' já está instalado.")
    except ImportError:
        print(f"[INFO] Pacote '{pacote}' não encontrado. Instalando...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pacote])
        print(f"[OK] Pacote '{pacote}' instalado com sucesso!")

pacotes_necessarios = ["requests"]
for pacote in pacotes_necessarios:
    checar_e_instalar_pacote(pacote)

import requests
import csv

# ================================
# 2️⃣ Configurações e constantes
# ================================
DOMAINS_FILE = "dominios.txt"
OUTPUT_FILE = "resultado.csv"
REQUEST_DELAY = 2  # segundos entre requisições

# ================================
# 3️⃣ Função para consultar domínios .br
# ================================
def consultar_br(domain):
    """Consulta domínios .br via RDAP"""
    url = f"https://rdap.registro.br/domain/{domain}"
    info = {
        "Dominio": domain,
        "Origem": "Registro.br",
        "Expiração": "",
        "Servidor DNS": "",
        "Disponibilidade": "",
        "Dono/Entidade": ""
    }
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 404:
            info["Disponibilidade"] = "Domínio disponível"
            return info
        resp.raise_for_status()
        data = resp.json()
        info["Disponibilidade"] = "Registrado"

        # Expiração
        for ev in data.get("events", []):
            if ev.get("eventAction", "").lower() == "expiration":
                info["Expiração"] = ev.get("eventDate")
                break

        # Name servers
        ns_list = []
        for ns in data.get("nameservers", []):
            if ns.get("ldhName"):
                ns_list.append(ns.get("ldhName"))
        info["Servidor DNS"] = ", ".join(ns_list)

        # Dono/Entidade
        entities = data.get("entities", [])
        donos = []
        for ent in entities:
            if ent.get("roles"):
                donos.append(ent.get("handle", "Desconhecido"))
        info["Dono/Entidade"] = ", ".join(donos) if donos else "Desconhecido"

    except Exception as e:
        info["Disponibilidade"] = "Erro"
        info["Origem"] = str(e)

    return info

# ================================
# 4️⃣ Função para consultar domínios internacionais
# ================================
def consultar_rdap(domain):
    """Consulta domínios internacionais via RDAP.org"""
    url = f"https://rdap.org/domain/{domain}"
    info = {
        "Dominio": domain,
        "Origem": "RDAP.org",
        "Expiração": "",
        "Servidor DNS": "",
        "Disponibilidade": "",
        "Dono/Entidade": ""
    }
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 404:
            info["Disponibilidade"] = "Domínio disponível"
            return info
        resp.raise_for_status()
        data = resp.json()
        info["Disponibilidade"] = "Registrado"

        # Expiração
        for ev in data.get("events", []):
            if ev.get("eventAction", "").lower() in ["expiration", "expires", "expiry"]:
                info["Expiração"] = ev.get("eventDate")
                break

        # Name servers
        ns_list = []
        for ns in data.get("nameservers", []):
            if ns.get("ldhName"):
                ns_list.append(ns.get("ldhName"))
        info["Servidor DNS"] = ", ".join(ns_list)

        # Dono/Entidade
        entities = data.get("entities", [])
        donos = []
        for ent in entities:
            if ent.get("roles"):
                donos.append(ent.get("handle", "Desconhecido"))
        info["Dono/Entidade"] = ", ".join(donos) if donos else "Desconhecido"

    except Exception as e:
        info["Disponibilidade"] = "Erro"
        info["Origem"] = str(e)

    return info

# ================================
# 5️⃣ Função principal
# ================================
def main():
    # Cria arquivo de domínios de exemplo se não existir
    if not os.path.exists(DOMAINS_FILE):
        print(f"{DOMAINS_FILE} não encontrado. Criando exemplo...")
        with open(DOMAINS_FILE, "w") as f:
            f.write("google.com\nregistro.br\nexample.com\ndominiofalso1234567.com\n")

    # Lê domínios do arquivo
    with open(DOMAINS_FILE, "r") as f:
        domains = [line.strip() for line in f if line.strip()]

    results = []
    for domain in domains:
        print(f"Consultando: {domain}")
        if domain.endswith(".br"):
            info = consultar_br(domain)
        else:
            info = consultar_rdap(domain)
        results.append(info)
        time.sleep(REQUEST_DELAY)

    # Salva resultados em CSV
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
        fieldnames = ["Dominio", "Disponibilidade", "Origem", "Expiração", "Servidor DNS", "Dono/Entidade"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"Consulta finalizada! Resultados salvos em {OUTPUT_FILE}")

# ================================
# 6️⃣ Executa o script
# ================================
if __name__ == "__main__":
    main()
