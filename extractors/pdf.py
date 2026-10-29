import base64
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

import fitz
import requests
from PIL import Image

from core import ollama_client
from core.config import OCR_SPACE_API_KEY, OCR_WORKERS, is_vision_model
from extractors.clean import clean_native, clean_ocr
from extractors.image import imagem_para_texto, tesseract_disponivel

OCR_SPACE_URL = "https://api.ocr.space/parse/image"
MIN_TEXTO_NATIVO = 100
NATIVE_TEXT_RATIO_THRESHOLD = 0.3
LIMITE_OCR_SPACE = int(1.5 * 1024 * 1024)
MAX_PAGINAS_VISAO = 5
OCR_DPI = 150


def _ocr_pagina(args):
    data, page_number = args
    try:
        doc = fitz.open(stream=data, filetype="pdf")
        page = doc[page_number]
        pix = page.get_pixmap(dpi=OCR_DPI)
        img = Image.open(BytesIO(pix.tobytes("png")))
        doc.close()
        return page_number, imagem_para_texto(img, psm=6)
    except Exception:
        return page_number, ""


def _ocr_space(data):
    if not OCR_SPACE_API_KEY or len(data) > LIMITE_OCR_SPACE:
        return ""
    try:
        resp = requests.post(
            OCR_SPACE_URL,
            files={"file": ("document.pdf", data, "application/pdf")},
            data={
                "apikey": OCR_SPACE_API_KEY,
                "language": "por",
                "isOverlayRequired": False,
                "filetype": "PDF",
            },
            timeout=30,
        )
        if resp.status_code != 200:
            return ""
        result = resp.json()
        if result.get("OCRExitCode") == 1:
            partes = [
                r.get("ParsedText", "")
                for r in result.get("ParsedResults", [])
                if r.get("ParsedText")
            ]
            return "\n".join(partes)
    except (requests.RequestException, ValueError):
        pass
    return ""


def _ocr_visao(data, model, provider="ollama"):
    try:
        doc = fitz.open(stream=data, filetype="pdf")
        partes = []
        for i, page in enumerate(doc):
            if i >= MAX_PAGINAS_VISAO:
                break
            pix = page.get_pixmap(dpi=OCR_DPI)
            img_b64 = base64.b64encode(pix.tobytes("png")).decode("utf-8")
            texto = ollama_client.extrair_imagem(
                model,
                img_b64,
                "Extraia todo o texto desta imagem. Responda apenas com o texto extraído, sem comentários adicionais.",
                provider=provider,
            )
            if texto:
                partes.append(f"--- Página {i + 1} ---\n{texto}")
        doc.close()
        return "\n\n".join(partes)
    except Exception:
        return ""


def extract_pdf(data, model=None, refine=False, quick_mode=False, provider="ollama"):
    doc = fitz.open(stream=data, filetype="pdf")
    total = doc.page_count
    nativos = [doc[i].get_text() for i in range(total)]
    doc.close()

    total_native_chars = sum(len(t) for t in nativos)
    avg_chars_per_page = total_native_chars / total if total else 0
    native_ratio = sum(1 for t in nativos if len(t.strip()) >= MIN_TEXTO_NATIVO) / total if total else 0

    if native_ratio >= NATIVE_TEXT_RATIO_THRESHOLD and avg_chars_per_page > 200:
        secoes = []
        for i, texto in enumerate(nativos):
            if texto.strip():
                secoes.append(f"--- Página {i + 1} ---\n{clean_native(texto)}")
        resultado = "\n\n".join(secoes).strip()
        if refine and model and resultado:
            from core.generators import refinar_texto
            resultado = refinar_texto(resultado, model, provider=provider)
        return resultado

    if quick_mode:
        secoes = []
        for i, texto in enumerate(nativos):
            if texto.strip():
                secoes.append(f"--- Página {i + 1} ---\n{clean_native(texto)}")
        resultado = "\n\n".join(secoes).strip()
        if refine and model and resultado:
            from core.generators import refinar_texto
            resultado = refinar_texto(resultado, model, provider=provider)
        return resultado

    faltando = [i for i, t in enumerate(nativos) if len(t.strip()) < MIN_TEXTO_NATIVO]

    if faltando and tesseract_disponivel():
        tasks = [(data, i) for i in faltando]
        with ThreadPoolExecutor(max_workers=min(OCR_WORKERS, len(faltando))) as pool:
            resultados = list(pool.map(_ocr_pagina, tasks))
        for page_num, ocr in resultados:
            if len(ocr.strip()) > len(nativos[page_num].strip()):
                nativos[page_num] = ocr

    secoes = []
    for i, texto in enumerate(nativos):
        texto = clean_ocr(texto) if i in faltando else clean_native(texto)
        if texto.strip():
            secoes.append(f"--- Página {i + 1} ---\n{texto}")

    resultado = "\n\n".join(secoes).strip()

    if not resultado:
        api_text = _ocr_space(data)
        if api_text.strip():
            resultado = clean_ocr(api_text)

    if not resultado and model and is_vision_model(model):
        visao = _ocr_visao(data, model, provider=provider)
        if visao.strip():
            resultado = visao

    if refine and model and resultado:
        from core.generators import refinar_texto
        resultado = refinar_texto(resultado, model, provider=provider)

    return resultado