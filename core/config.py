import os
from pathlib import Path
import streamlit as st

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "docs"

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "https://ollama.com").rstrip("/")
OLLAMA_API_KEYS = [k.strip() for k in os.getenv("OLLAMA_API_KEYS", "").split(",") if k.strip()]
if not OLLAMA_API_KEYS and os.getenv("OLLAMA_API_KEY"):
    OLLAMA_API_KEYS = [os.getenv("OLLAMA_API_KEY").strip()]

NVIDIA_API_KEYS = [k.strip() for k in os.getenv("NVIDIA_API_KEYS", "").split(",") if k.strip()]
if not NVIDIA_API_KEYS and os.getenv("NVIDIA_API_KEY"):
    NVIDIA_API_KEYS = [os.getenv("NVIDIA_API_KEY").strip()]

OLLAMA_MAX_TOKENS = int(os.getenv("OLLAMA_MAX_TOKENS", "8192"))
MAX_CONTEXT_CHARS = int(os.getenv("MAX_CONTEXT_CHARS", "50000"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "5000"))
OCR_SPACE_API_KEY = os.getenv("OCR_SPACE_API_KEY", "")
EXTRACTION_CACHE = os.getenv("EXTRACTION_CACHE", "1") == "1"
LLM_REFINE_DEFAULT = os.getenv("LLM_REFINE", "0") == "1"
OCR_WORKERS = int(os.getenv("OCR_WORKERS", "4"))
ALUNOS_PADRAO = tuple(
    a.strip() for a in os.getenv("ALUNOS_PADRAO", "").split(",") if a.strip()
)


def get_available_models():
    raw = os.getenv("OLLAMA_AVAILABLE_MODELS", "gemma4:31b-cloud")
    return [m.strip() for m in raw.split(",") if m.strip()]


def get_vision_models():
    raw = os.getenv("OLLAMA_VISION_MODELS", "gemma4:31b-cloud")
    return [m.strip() for m in raw.split(",") if m.strip()]


def is_vision_model(model):
    return bool(model) and model in get_vision_models()


def list_alunos():
    DOCS_DIR.mkdir(exist_ok=True)
    names = {p.name for p in DOCS_DIR.iterdir() if p.is_dir() and not p.name.startswith(".")}
    names.update(ALUNOS_PADRAO)
    return sorted(names)


def aluno_dir(aluno):
    path = DOCS_DIR / aluno
    path.mkdir(parents=True, exist_ok=True)
    return path


def create_aluno(nome):
    limpo = "".join(c for c in nome.strip().lower() if c.isalnum() or c in "-_ ").strip()
    limpo = limpo.replace(" ", "_")
    if not limpo:
        raise ValueError("Nome de aluno inválido.")
    return aluno_dir(limpo)


def aluno_of(file_path):
    path = Path(file_path).resolve()
    try:
        rel = path.relative_to(DOCS_DIR.resolve())
        return DOCS_DIR / rel.parts[0]
    except ValueError:
        return path.parent


def list_files(aluno):
    folder = aluno_dir(aluno)
    return sorted(
        p.relative_to(folder)
        for p in folder.rglob("*")
        if p.is_file() and not any(part.startswith(".") for part in p.relative_to(folder).parts)
    )


def has_ollama_keys():
    return bool(OLLAMA_API_KEYS)


def has_nvidia_keys():
    return bool(NVIDIA_API_KEYS)


def get_llm_providers():
    providers = []
    if has_ollama_keys():
        providers.append("ollama")
    if has_nvidia_keys():
        providers.append("nvidia")
    return providers


@st.cache_data(ttl=3600)
def get_free_models_ollama():
    """Retorna modelos gratuitos do Ollama (cache 1 hora)."""
    from core.ollama_client import listar_modelos_gratuitos_ollama
    return listar_modelos_gratuitos_ollama()


@st.cache_data(ttl=3600)
def get_all_models_ollama():
    """Retorna todos os modelos do Ollama (cache 1 hora)."""
    from core.ollama_client import listar_todos_modelos_ollama
    return listar_todos_modelos_ollama()


def get_models_for_provider(provider, only_free=False):
    """Retorna modelos disponíveis para o provedor."""
    if provider == "ollama":
        if only_free:
            free_models = get_free_models_ollama()
            if free_models:
                return free_models
        all_models = get_all_models_ollama()
        if all_models:
            return all_models
        return get_available_models()
    elif provider == "nvidia":
        return ["meta/llama-3.1-70b-instruct", "meta/llama-3.1-8b-instruct", "nvidia/nemotron-3-ultra"]
    return []