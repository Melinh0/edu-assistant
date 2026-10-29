import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from core.config import BASE_DIR, aluno_dir

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

CMM_CADERNO = (
    "https://cmm.eb.mil.br/images/2025/Processo%20Seletivo%202025-2026/COMUNICADOS/"
    "2_COMUNICADO_Nr_13_-_CADERNO_DE_QUESTOES_assinado%20-%20completo%202.pdf"
)
CMM_GABARITO = (
    "https://cmm.eb.mil.br/images/2025/Processo%20Seletivo%202025-2026/COMUNICADOS/"
    "2_COMUNICADO_Nr_12_-_Divulgacao_do_Gabarito_assinado%202.pdf"
)

FONTES = {
    "cmm": {
        "diretas": [CMM_CADERNO, CMM_GABARITO],
        "paginas": [
            "https://cmm.eb.mil.br/noticias/processo-seletivo/provas-anteriores",
            "https://www.cursosazambuja.com.br/provas-e-gabaritos-cursos-azambuja/538/colegio-militar-de-manaus-cmm",
        ],
        "filtro": None,
    },
    "colegios_militares": {
        "diretas": [],
        "paginas": [
            "https://militares.estrategia.com/portal/noticias/cm-2024-2025-confira-as-provas-e-gabaritos/",
        ],
        "filtro": None,
    },
    "uerj": {
        "diretas": [],
        "paginas": ["https://www.vestibular.uerj.br/?page_id=7747"],
        "filtro": "uerj",
    },
    "enem": {
        "diretas": [],
        "paginas": [
            "https://cursoenemgratuito.com.br/download-das-provas-do-enem/",
            "https://www.gov.br/inep/pt-br/areas-de-atuacao/avaliacao-e-exames-educacionais/enem/provas-e-gabaritos",
        ],
        "filtro": None,
    },
}


def scrape_urls_pdf(pagina, filtro=None):
    try:
        resp = requests.get(pagina, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"  ! falha ao acessar {pagina}: {exc}")
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    encontradas = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if ".pdf" not in href.lower():
            continue
        url = urljoin(pagina, href)
        if filtro and filtro not in url.lower():
            continue
        encontradas.add(url)
    return sorted(encontradas)


def nome_do_url(url):
    nome = Path(unquote(urlparse(url).path)).name
    nome = re.sub(r"[^\w.\- ]", "_", nome)
    return nome or "arquivo.pdf"


def baixar(url, pasta):
    destino = pasta / nome_do_url(url)
    if destino.exists() and destino.stat().st_size > 0:
        print(f"  = já existe: {destino.name}")
        return True
    try:
        with requests.get(url, headers=HEADERS, stream=True, timeout=60) as resp:
            resp.raise_for_status()
            tmp = destino.with_suffix(destino.suffix + ".part")
            tamanho = 0
            with open(tmp, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1 << 16):
                    f.write(chunk)
                    tamanho += len(chunk)
            if tamanho < 10240:
                tmp.unlink(missing_ok=True)
                print(f"  ! ignorado (muito pequeno): {url}")
                return False
            tmp.replace(destino)
        print(f"  + {destino.name} ({tamanho // 1024} KB)")
        return True
    except requests.RequestException as exc:
        print(f"  ! erro ao baixar {url}: {exc}")
        return False


def main():
    aluno = os.getenv("FETCH_STUDENT") or (sys.argv[1] if len(sys.argv) > 1 else "")
    if not aluno:
        print("Uso: FETCH_STUDENT=<nome> ou: uv run python scripts/fetch_student_sources.py <nome>")
        sys.exit(1)
    destino = aluno_dir(aluno) / "provas"
    sucesso = falhas = 0
    for nome, spec in FONTES.items():
        pasta = destino / nome
        pasta.mkdir(parents=True, exist_ok=True)
        print(f"\n== {nome} (aluno: {aluno}) ==")
        urls = list(spec["diretas"])
        for pagina in spec["paginas"]:
            encontradas = scrape_urls_pdf(pagina, spec["filtro"])
            print(f"  ~ {len(encontradas)} PDFs em {pagina}")
            urls.extend(encontradas)
        urls = list(dict.fromkeys(urls))
        for url in urls:
            if baixar(url, pasta):
                sucesso += 1
            else:
                falhas += 1
            time.sleep(0.3)
    print(f"\nConcluído: {sucesso} baixados, {falhas} falhas/ignorados.")
    return 0 if sucesso else 1


if __name__ == "__main__":
    sys.exit(main())