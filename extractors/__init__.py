from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import os

from extractors import cache
from extractors.image import extract_image
from extractors.office import extract_docx, extract_pptx
from extractors.pdf import extract_pdf
from extractors.plain import extract_plain

EXTENSOES_SUPORTADAS = [
    "pdf", "pptx", "docx", "txt", "md", "json", "csv", "html",
    "png", "jpg", "jpeg",
]

_EXTS_IMAGEM = {"png", "jpg", "jpeg"}

DEFAULT_MAX_WORKERS = min(8, (os.cpu_count() or 4))


def extract_file(path, model=None, refine=False, quick_mode=False, provider="ollama"):
    arquivo = Path(path)
    if not arquivo.exists():
        return ""
    salvo = cache.get_cached(arquivo)
    if salvo is not None:
        return salvo
    try:
        data = arquivo.read_bytes()
    except OSError:
        return ""
    ext = arquivo.suffix.lower().lstrip(".")
    if ext == "pdf":
        texto = extract_pdf(data, model=model, refine=refine, quick_mode=quick_mode, provider=provider)
    elif ext == "pptx":
        texto = extract_pptx(data)
    elif ext == "docx":
        texto = extract_docx(data)
    elif ext in _EXTS_IMAGEM:
        texto = extract_image(data)
    else:
        texto = extract_plain(ext, data)
    if texto:
        cache.put_cached(arquivo, texto)
    return texto


def _extract_file_worker(args):
    path, model, refine, quick_mode, provider = args
    return extract_file(path, model=model, refine=refine, quick_mode=quick_mode, provider=provider)


def extract_files(paths, model=None, refine=False, progress_cb=None, max_workers=None, quick_mode=False, provider="ollama"):
    if max_workers is None:
        max_workers = DEFAULT_MAX_WORKERS

    arquivos = [Path(p) for p in paths]
    if not arquivos:
        return ""
    resultados = {}

    if len(arquivos) == 1:
        resultados[0] = extract_file(arquivos[0], model=model, refine=refine, quick_mode=quick_mode, provider=provider)
        if progress_cb:
            progress_cb(1, 1, arquivos[0].name)
    else:
        workers = min(max_workers, len(arquivos))
        tasks = [(str(a), model, refine, quick_mode, provider) for a in arquivos]
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futuros = {pool.submit(_extract_file_worker, t): i for i, t in enumerate(tasks)}
            concluidos = 0
            for fut in as_completed(futuros):
                i = futuros[fut]
                try:
                    resultados[i] = fut.result()
                except Exception:
                    resultados[i] = ""
                concluidos += 1
                if progress_cb:
                    progress_cb(concluidos, len(arquivos), arquivos[i].name)

    partes = []
    for i, a in enumerate(arquivos):
        texto = resultados.get(i, "")
        if texto.strip():
            partes.append(f"--- {a.name} ---\n{texto}")
    return "\n\n".join(partes)