import requests
import os
import streamlit as st
from PyPDF2 import PdfReader
from io import BytesIO
import base64
import fitz

OCR_SPACE_API_KEY = os.getenv("OCR_SPACE_API_KEY")
OCR_URL = "https://api.ocr.space/parse/image"
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_HOST = os.getenv("OLLAMA_HOST")

def extract_text_from_pdf(pdf_bytes, model=None):
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        if text.strip():
            return text.strip()
        else:
            st.info("PyPDF2 não extraiu texto (PDF provavelmente escaneado).")
    except Exception as e:
        st.info(f"PyPDF2 falhou: {str(e)}")

    ocr_text = extract_text_with_ocr(pdf_bytes)
    if ocr_text.strip():
        return ocr_text

    if model and is_vision_model(model):
        st.info("Tentando extrair texto com visão do Ollama...")
        return extract_text_with_vision(pdf_bytes, model)
    else:
        st.warning("Não foi possível extrair texto. Considere usar um modelo com suporte a visão (ex: gemma4:31b).")
        return ""

def extract_text_with_ocr(pdf_bytes):
    if not OCR_SPACE_API_KEY:
        st.error("Chave OCR Space não configurada.")
        return ""
    files = {'file': ('document.pdf', pdf_bytes, 'application/pdf')}
    data = {
        'apikey': OCR_SPACE_API_KEY,
        'language': 'por',
        'isOverlayRequired': False,
        'filetype': 'PDF'
    }
    try:
        response = requests.post(OCR_URL, files=files, data=data, timeout=60)
        if response.status_code == 200:
            result = response.json()
            if result.get('OCRExitCode') == 1:
                return result['ParsedResults'][0]['ParsedText']
            else:
                st.error(f"Erro no OCR: {result.get('ErrorMessage', 'Desconhecido')}")
                return ""
        else:
            st.error(f"Falha na requisição OCR: {response.status_code}")
            st.error(f"Detalhes: {response.text}")
            return ""
    except Exception as e:
        st.error(f"Exceção no OCR: {str(e)}")
        return ""

def is_vision_model(model):
    vision_models = os.getenv("OLLAMA_VISION_MODELS", "gemma4:31b").split(',')
    vision_models = [m.strip() for m in vision_models if m.strip()]
    return model in vision_models

def extract_text_with_vision(pdf_bytes, model):
    if not OLLAMA_API_KEY:
        st.error("Chave Ollama não configurada.")
        return ""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        all_text = ""
        max_pages = 3
        for i, page in enumerate(doc):
            if i >= max_pages:
                st.info(f"Limite de {max_pages} páginas para visão. As demais páginas não foram processadas.")
                break
            pix = page.get_pixmap()
            img_bytes = pix.tobytes("png")
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            prompt = "Extraia todo o texto desta imagem. Responda apenas com o texto extraído, sem comentários adicionais."
            payload = {
                "model": model,
                "prompt": prompt,
                "images": [img_base64],
                "stream": False,
                "options": {"num_predict": 4000}
            }
            headers = {
                "Authorization": f"Bearer {OLLAMA_API_KEY}",
                "Content-Type": "application/json"
            }
            url = f"{OLLAMA_HOST}/api/generate"
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            if response.status_code == 200:
                data = response.json()
                page_text = data.get('response', '')
                all_text += f"\n--- Página {i+1} ---\n{page_text}\n"
            else:
                st.error(f"Erro na chamada Ollama (página {i+1}): {response.status_code} - {response.text}")
        doc.close()
        return all_text.strip()
    except Exception as e:
        st.error(f"Erro ao extrair com visão: {str(e)}")
        return ""