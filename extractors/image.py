import os
import platform
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
from io import BytesIO

from PIL import Image, ImageOps

_tesseract_path = None
_tesseract_configured = False


def _setup_tesseract():
    global _tesseract_path, _tesseract_configured
    if _tesseract_configured:
        return _tesseract_path
    _tesseract_configured = True
    if platform.system() == "Windows":
        caminhos = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"C:\ProgramData\chocolatey\bin\tesseract.exe",
        ]
        tessdata = [
            r"C:\Program Files\Tesseract-OCR\tessdata",
            r"C:\Program Files (x86)\Tesseract-OCR\tessdata",
        ]
    else:
        caminhos = ["/usr/bin/tesseract", "/usr/local/bin/tesseract"]
        tessdata = [
            "/usr/share/tesseract-ocr/5.00/tessdata",
            "/usr/share/tesseract-ocr/4.00/tessdata",
            "/usr/share/tesseract-ocr/tessdata",
            "/usr/local/share/tesseract-ocr/tessdata",
        ]

    import pytesseract

    for path in caminhos:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            _tesseract_path = path
            break

    if "TESSDATA_PREFIX" in os.environ and os.path.exists(os.environ["TESSDATA_PREFIX"]):
        return _tesseract_path
    for d in tessdata:
        if os.path.exists(d):
            os.environ["TESSDATA_PREFIX"] = d
            break
    return _tesseract_path


@lru_cache(maxsize=1)
def tesseract_disponivel():
    try:
        import pytesseract
    except ImportError:
        return False
    _setup_tesseract()
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def _baixar_idioma():
    import requests

    tessdata = os.environ.get("TESSDATA_PREFIX")
    if not tessdata:
        return
    alvo = os.path.join(tessdata, "por.traineddata")
    if os.path.exists(alvo):
        return
    try:
        resp = requests.get(
            "https://github.com/tesseract-ocr/tessdata/raw/main/por.traineddata",
            timeout=60,
        )
        if resp.status_code == 200:
            with open(alvo, "wb") as f:
                f.write(resp.content)
    except requests.RequestException:
        pass


def preprocess_image(pil_img):
    return ImageOps.autocontrast(pil_img.convert("L"))


def _ocr_worker(args):
    img_bytes, psm = args
    if not tesseract_disponivel():
        return ""
    import pytesseract

    _baixar_idioma()
    try:
        img = Image.open(BytesIO(img_bytes))
        processada = preprocess_image(img)
        config = f"--psm {psm} --oem 3 -l por+eng"
        return pytesseract.image_to_string(processada, config=config)
    except Exception:
        return ""


def imagem_para_texto(pil_img, psm=6):
    if not tesseract_disponivel():
        return ""
    import pytesseract

    _baixar_idioma()
    processada = preprocess_image(pil_img)
    config = f"--psm {psm} --oem 3 -l por+eng"
    return pytesseract.image_to_string(processada, config=config)


def extract_image(file_bytes):
    try:
        img = Image.open(BytesIO(file_bytes))
        return imagem_para_texto(img)
    except Exception:
        return ""