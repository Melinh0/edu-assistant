import hashlib
from pathlib import Path

from core.config import EXTRACTION_CACHE, aluno_of


def _hash_arquivo_fast(path):
    """Hash rápido usando apenas mtime + size. Para cache válido na maioria dos casos."""
    stat = path.stat()
    h = hashlib.sha1()
    h.update(str(stat.st_mtime_ns).encode("utf-8"))
    h.update(str(stat.st_size).encode("utf-8"))
    return h.hexdigest()


def _hash_arquivo_full(path):
    """Hash completo do conteúdo. Mais lento mas detecta mudanças sem alterar mtime."""
    stat = path.stat()
    h = hashlib.sha1()
    h.update(str(stat.st_mtime_ns).encode("utf-8"))
    h.update(str(stat.st_size).encode("utf-8"))
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _cache_dir(path):
    return aluno_of(path) / ".cache"


def get_cached(path):
    if not EXTRACTION_CACHE:
        return None
    arquivo = Path(path)
    if not arquivo.exists():
        return None
    cache_file = _cache_dir(arquivo) / f"{_hash_arquivo_fast(arquivo)}.txt"
    if cache_file.exists():
        try:
            return cache_file.read_text(encoding="utf-8")
        except OSError:
            return None
    return None


def put_cached(path, text):
    if not EXTRACTION_CACHE or not text:
        return
    arquivo = Path(path)
    try:
        cache_dir = _cache_dir(arquivo)
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / f"{_hash_arquivo_fast(arquivo)}.txt").write_text(text, encoding="utf-8")
    except OSError:
        pass