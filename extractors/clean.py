import re


def clean_native(texto):
    if not texto:
        return ""
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    linhas = [l.rstrip() for l in texto.split("\n")]
    texto = "\n".join(linhas)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def clean_ocr(texto):
    if not texto:
        return ""
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    texto = re.sub(r"(\w)-\n(\w)", r"\1\2", texto)
    texto = re.sub(r"[ \t]{2,}", " ", texto)
    linhas = [l.strip() for l in texto.split("\n")]
    texto = "\n".join(linhas)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()
