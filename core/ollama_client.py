import json
import threading

import requests

from core.config import OLLAMA_API_KEYS, OLLAMA_HOST, OLLAMA_MAX_TOKENS, NVIDIA_API_KEYS

_lock_ollama = threading.Lock()
_lock_nvidia = threading.Lock()
_indice_ollama = 0
_indice_nvidia = 0


class LLMError(Exception):
    pass


def _proxima_chave_ollama():
    global _indice_ollama
    with _lock_ollama:
        if not OLLAMA_API_KEYS:
            raise LLMError("Nenhuma chave Ollama configurada em OLLAMA_API_KEYS.")
        chave = OLLAMA_API_KEYS[_indice_ollama % len(OLLAMA_API_KEYS)]
        _indice_ollama += 1
        return chave


def _proxima_chave_nvidia():
    global _indice_nvidia
    with _lock_nvidia:
        if not NVIDIA_API_KEYS:
            raise LLMError("Nenhuma chave NVIDIA configurada em NVIDIA_API_KEYS.")
        chave = NVIDIA_API_KEYS[_indice_nvidia % len(NVIDIA_API_KEYS)]
        _indice_nvidia += 1
        return chave


def resetar_rotacao_ollama():
    global _indice_ollama
    with _lock_ollama:
        _indice_ollama = 0


def resetar_rotacao_nvidia():
    global _indice_nvidia
    with _lock_nvidia:
        _indice_nvidia = 0


def _erro_de_cota(status, corpo):
    if status in (401, 402, 403, 429):
        return True
    texto = (corpo or "").lower()
    return any(s in texto for s in ("rate limit", "quota", "too many requests", "usage limit", "insufficient_quota"))


def _postar_ollama(payload, stream, timeout):
    ultimo = None
    tentativas = max(len(OLLAMA_API_KEYS), 1)
    for _ in range(tentativas):
        chave = _proxima_chave_ollama()
        headers = {"Authorization": f"Bearer {chave}", "Content-Type": "application/json"}
        try:
            resp = requests.post(
                f"{OLLAMA_HOST}/api/generate",
                json=payload,
                headers=headers,
                stream=stream,
                timeout=timeout,
            )
        except requests.RequestException as exc:
            ultimo = exc
            continue
        if resp.status_code == 200:
            return resp
        corpo = resp.text or ""
        if _erro_de_cota(resp.status_code, corpo):
            ultimo = LLMError(f"chave Ollama esgotada ({resp.status_code})")
            continue
        raise LLMError(f"Erro na API Ollama: {resp.status_code} - {corpo[:300]}")
    raise LLMError(f"Todas as chaves Ollama falharam. Último erro: {ultimo}")


def _postar_nvidia(payload, stream, timeout):
    ultimo = None
    tentativas = max(len(NVIDIA_API_KEYS), 1)
    for _ in range(tentativas):
        chave = _proxima_chave_nvidia()
        headers = {"Authorization": f"Bearer {chave}", "Content-Type": "application/json"}
        try:
            resp = requests.post(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                json=payload,
                headers=headers,
                stream=stream,
                timeout=timeout,
            )
        except requests.RequestException as exc:
            ultimo = exc
            continue
        if resp.status_code == 200:
            return resp
        corpo = resp.text or ""
        if _erro_de_cota(resp.status_code, corpo):
            ultimo = LLMError(f"chave NVIDIA esgotada ({resp.status_code})")
            continue
        raise LLMError(f"Erro na API NVIDIA: {resp.status_code} - {corpo[:300]}")
    raise LLMError(f"Todas as chaves NVIDIA falharam. Último erro: {ultimo}")


def _build_ollama_payload(prompt, model, temperature, num_predict, seed, stream):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": stream,
        "options": {
            "num_predict": num_predict or OLLAMA_MAX_TOKENS,
            "temperature": temperature,
            "top_p": 0.95,
        },
    }
    if seed is not None:
        payload["options"]["seed"] = seed
    return payload


def _build_nvidia_payload(prompt, model, temperature, num_predict, seed, stream):
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": stream,
        "max_tokens": num_predict or 4096,
        "temperature": temperature,
        "top_p": 0.95,
    }
    if seed is not None:
        payload["seed"] = seed
    return payload


def generate(prompt, model, provider="ollama", temperature=1.0, num_predict=None, seed=None):
    if provider == "nvidia":
        payload = _build_nvidia_payload(prompt, model, temperature, num_predict, seed, stream=False)
        resp = _postar_nvidia(payload, stream=False, timeout=600)
        return resp.json()["choices"][0]["message"]["content"]
    else:
        payload = _build_ollama_payload(prompt, model, temperature, num_predict, seed, stream=False)
        resp = _postar_ollama(payload, stream=False, timeout=600)
        return resp.json().get("response", "")


def generate_stream(prompt, model, provider="ollama", num_predict=None):
    if provider == "nvidia":
        payload = _build_nvidia_payload(prompt, model, 1.0, num_predict, None, stream=True)
        resp = _postar_nvidia(payload, stream=True, timeout=180)
        for linha in resp.iter_lines():
            if not linha:
                continue
            try:
                dados = json.loads(linha.decode("utf-8"))
            except ValueError:
                continue
            if "choices" in dados and dados["choices"]:
                delta = dados["choices"][0].get("delta", {})
                pedaco = delta.get("content", "")
                if pedaco:
                    yield pedaco
    else:
        payload = _build_ollama_payload(prompt, model, 1.0, num_predict, None, stream=True)
        resp = _postar_ollama(payload, stream=True, timeout=180)
        for linha in resp.iter_lines():
            if not linha:
                continue
            try:
                dados = json.loads(linha.decode("utf-8"))
            except ValueError:
                continue
            pedaco = dados.get("response", "")
            if pedaco:
                yield pedaco
            if dados.get("done"):
                break


def extrair_imagem(model, imagem_base64, prompt, num_predict=4000, provider="ollama"):
    if provider == "nvidia":
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{imagem_base64}"}},
                    ],
                }
            ],
            "max_tokens": num_predict,
            "stream": False,
        }
        resp = _postar_nvidia(payload, stream=False, timeout=180)
        return resp.json()["choices"][0]["message"]["content"]
    else:
        payload = {
            "model": model,
            "prompt": prompt,
            "images": [imagem_base64],
            "stream": False,
            "options": {"num_predict": num_predict},
        }
        resp = _postar_ollama(payload, stream=False, timeout=180)
        return resp.json().get("response", "")


MODELOS_GRATUITOS_CONHECIDOS = [
    "gemma4:31b",
    "gemma4:31b-cloud",
    "gemma3:27b-cloud",
    "gemma3:12b-cloud",
    "gemma3:4b-cloud",
    "gemma2:27b-cloud",
    "gemma2:9b-cloud",
    "llama3.1:8b-cloud",
    "llama3.1:70b-cloud",
    "llama3.2:3b-cloud",
    "llama3.2:1b-cloud",
    "qwen2.5:72b-cloud",
    "qwen2.5:32b-cloud",
    "qwen2.5:14b-cloud",
    "qwen2.5:7b-cloud",
    "qwen2.5:3b-cloud",
    "qwen2.5:1.5b-cloud",
    "qwen2.5:0.5b-cloud",
    "phi3.5:3.8b-cloud",
    "phi3.5:7b-cloud",
    "phi3:14b-cloud",
    "phi3:7b-cloud",
    "mistral:7b-cloud",
    "mistral-nemo:12b-cloud",
    "codellama:7b-cloud",
    "codellama:13b-cloud",
    "codellama:34b-cloud",
    "deepseek-coder:6.7b-cloud",
    "deepseek-coder:33b-cloud",
    "starcoder2:15b-cloud",
    "starcoder2:7b-cloud",
    "starcoder2:3b-cloud",
    "command-r:35b-cloud",
    "command-r-plus:104b-cloud",
]


def _fetch_ollama_models():
    """Busca modelos da API do Ollama Cloud. Retorna lista de nomes ou lista vazia se falhar."""
    if not OLLAMA_API_KEYS:
        return []
    try:
        chave = OLLAMA_API_KEYS[0]
        headers = {"Authorization": f"Bearer {chave}", "Content-Type": "application/json"}
        
        # Tenta endpoint principal do Ollama Cloud
        resp = requests.get(f"{OLLAMA_HOST}/api/models", headers=headers, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            modelos = []
            for m in data.get("models", []):
                # Ollama Cloud retorna: name, tags, plan, etc.
                nome = m.get("name", "")
                if not nome:
                    continue
                tags = m.get("tags", [])
                plan = m.get("plan", "")
                is_free = "free" in tags or "Free" in plan or m.get("free", False)
                if is_free or nome.endswith("-cloud"):
                    modelos.append(nome)
            if modelos:
                return sorted(set(modelos))
        
        # Fallback: /api/tags (estilo local)
        resp = requests.get(f"{OLLAMA_HOST}/api/tags", headers=headers, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            modelos = []
            for m in data.get("models", []):
                nome = m.get("name", "")
                if nome and ("-cloud" in nome or "free" in nome.lower()):
                    modelos.append(nome)
            if modelos:
                return sorted(set(modelos))
                
    except Exception:
        pass
    return []


def listar_modelos_gratuitos_ollama():
    """Retorna modelos gratuitos disponíveis para as chaves configuradas.
    Prioriza: API do Ollama Cloud > lista conhecida."""
    modelos_api = _fetch_ollama_models()
    if modelos_api:
        return modelos_api
    # Fallback para lista conhecida
    return MODELOS_GRATUITOS_CONHECIDOS


def listar_todos_modelos_ollama():
    """Retorna todos os modelos disponíveis na API (livres + pagos)."""
    if not OLLAMA_API_KEYS:
        return []
    try:
        chave = OLLAMA_API_KEYS[0]
        headers = {"Authorization": f"Bearer {chave}", "Content-Type": "application/json"}
        resp = requests.get(f"{OLLAMA_HOST}/api/models", headers=headers, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            return sorted([m.get("name", "") for m in data.get("models", []) if m.get("name")])
        resp = requests.get(f"{OLLAMA_HOST}/api/tags", headers=headers, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            return sorted([m.get("name", "") for m in data.get("models", []) if m.get("name")])
    except Exception:
        pass
    # Fallback
    from core.config import get_available_models
    conhecidos = set(MODELOS_GRATUITOS_CONHECIDOS)
    configurados = set(get_available_models())
    return sorted(conhecidos | configurados)