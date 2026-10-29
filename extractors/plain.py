import json

from bs4 import BeautifulSoup

from extractors.clean import clean_native


def extract_txt(file_bytes):
    return clean_native(file_bytes.decode("utf-8", errors="ignore"))


def extract_json(file_bytes):
    try:
        dados = json.loads(file_bytes.decode("utf-8", errors="ignore"))
        return clean_native(json.dumps(dados, ensure_ascii=False, indent=2))
    except (ValueError, TypeError):
        return extract_txt(file_bytes)


def extract_html(file_bytes):
    try:
        soup = BeautifulSoup(file_bytes.decode("utf-8", errors="ignore"), "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        return clean_native(soup.get_text(separator="\n"))
    except Exception:
        return extract_txt(file_bytes)


def extract_plain(ext, file_bytes):
    if ext in ("txt", "md", "csv", "log"):
        return extract_txt(file_bytes)
    if ext == "json":
        return extract_json(file_bytes)
    if ext in ("html", "htm"):
        return extract_html(file_bytes)
    return ""
