import subprocess
import sys
import os
import time
from datetime import datetime
import requests
import csv
from bs4 import BeautifulSoup

# ================================
# 1️⃣ Verifica e instala pacotes
# ================================
def checar_e_instalar_pacote(pacote):
    try:
        __import__(pacote if pacote != "beautifulsoup4" else "bs4")
        print(f"[OK] Pacote '{pacote}' já está instalado.")
    except ImportError:
        print(f"[INFO] Pacote '{pacote}' não encontrado. Instalando...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pacote])
        print(f"[OK] Pacote '{pacote}' instalado com sucesso!")

pacotes_necessarios = ["requests", "beautifulsoup4"]
for pacote in pacotes_necessarios:
    checar_e_instalar_pacote(pacote)

# ================================
# 2️⃣ Função para formatar data
# ================================
def formatar_data_br(data_iso):
    if not data_iso:
        return ""
    try:
        dt = datetime.fromisoformat(data_iso.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return data_iso

# ================================
# 3️⃣ Configurações e constantes
# ================================
DOMAINS_FILE = "dominios.txt"
OUTPUT_FILE = "resultado.csv"
REQUEST_DELAY = 2

# ================================
# 4️⃣ Consulta domínios .br via RDAP
# ================================
def consultar_br(domain):
    info = {
        "Dominio": domain,
        "Origem": "Registro.br",
        "Expiração": "",
        "Servidor DNS": "",
        "Disponibilidade": "",
        "Dono/Entidade": ""
    }
    try:
        url = f"https://rdap.registro.br/domain/{domain}"
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
                info["Expiração"] = formatar_data_br(ev.get("eventDate"))
                break

        # Name servers
        ns_list = []
        for ns in data.get("nameservers", []):
            if ns.get("ldhName"):
                ns_list.append(ns.get("ldhName"))
        info["Servidor DNS"] = ", ".join(ns_list)

        # Dono/Entidade via RDAP (fallback)
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
# 5️⃣ Consulta domínios internacionais via RDAP.org
# ================================
def consultar_rdap(domain):
    info = {
        "Dominio": domain,
        "Origem": "RDAP.org",
        "Expiração": "",
        "Servidor DNS": "",
        "Disponibilidade": "",
        "Dono/Entidade": ""
    }
    try:
        url = f"https://rdap.org/domain/{domain}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 404:
            info["Disponibilidade"] = "Domínio disponível"
            return info
        resp.raise_for_status()
        data = resp.json()
        info["Disponibilidade"] = "Registrado"

        for ev in data.get("events", []):
            if ev.get("eventAction", "").lower() in ["expiration", "expires", "expiry"]:
                info["Expiração"] = formatar_data_br(ev.get("eventDate"))
                break

        ns_list = []
        for ns in data.get("nameservers", []):
            if ns.get("ldhName"):
                ns_list.append(ns.get("ldhName"))
        info["Servidor DNS"] = ", ".join(ns_list)

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
# 6️⃣ Consulta WHOIS via site Registro.br (pegando title do OwnerHandle)
# ================================
def consultar_whois_site(domain):
    info = ""
    try:
        url = f"https://registro.br/tecnologia/ferramentas/whois/?search={domain}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")  # Corrigido aqui

        # Procura a célula da tabela com a classe 'cell-ownerhandle'
        td_owner = soup.find("td", {"class": "cell-ownerhandle"})
        if td_owner:
            span = td_owner.find("span", {"class": "link"})
            if span and span.has_attr("title"):
                info = span["title"].strip()
    except Exception as e:
        info = f"Erro: {e}"
    return info

# ================================
# 7️⃣ Função principal
# ================================
def main():
    if not os.path.exists(DOMAINS_FILE):
        print(f"{DOMAINS_FILE} não encontrado. Criando exemplo...")
        with open(DOMAINS_FILE, "w") as f:
            f.write("google.com\nregistro.br\nexample.com\ndominiofalso1234567.com\n")

    with open(DOMAINS_FILE, "r") as f:
        domains = [line.strip() for line in f if line.strip()]

    results = []
    for domain in domains:
        print(f"Consultando: {domain}")
        if domain.endswith(".br"):
            info = consultar_br(domain)
            whois_site = consultar_whois_site(domain)
            info["Dono/Entidade"] = whois_site or info["Dono/Entidade"]
        else:
            info = consultar_rdap(domain)
        results.append(info)
        time.sleep(REQUEST_DELAY)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
        fieldnames = ["Dominio", "Disponibilidade", "Origem", "Expiração", "Servidor DNS", "Dono/Entidade"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"Consulta finalizada! Resultados salvos em {OUTPUT_FILE}")

# ================================
# 8️⃣ Executa o script
# ================================
if __name__ == "__main__":
    main()
