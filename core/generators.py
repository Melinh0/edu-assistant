import random
import re
import time

from core import ollama_client
from core.config import get_llm_providers, MAX_CONTEXT_CHARS


def _nonce(cache_buster=None):
    return f"{cache_buster}_{int(time.time())}_{random.randint(0, 1000000)}"


def _default_provider():
    providers = get_llm_providers()
    if "ollama" in providers:
        return "ollama"
    if "nvidia" in providers:
        return "nvidia"
    return "ollama"


def _truncate_context(contexto, max_chars=MAX_CONTEXT_CHARS):
    """Trunca o contexto para caber no limite do modelo."""
    if len(contexto) <= max_chars:
        return contexto
    # Mantém o início e o fim, corta o meio
    half = max_chars // 2
    return contexto[:half] + "\n\n[... CONTEXTO TRUNCADO ...]\n\n" + contexto[-half:]


def format_alternativas(texto):
    linhas = []
    for linha in texto.split("\n"):
        strip = linha.strip()
        if re.match(r"^[a-eA-E][).]", strip):
            linhas.append("    - " + strip + "  ")
        else:
            linhas.append(linha)
    return "\n".join(linhas)


def generate_plan(contexto, user_prompt, model, cache_buster=None, provider=None):
    if provider is None:
        provider = _default_provider()
    contexto_truncado = _truncate_context(contexto)
    prompt = (
        f"Com base no conteúdo fornecido, crie um plano de aula detalhado para o tema: "
        f"{user_prompt}. Inclua objetivos, materiais, atividades e avaliação. "
        f"Use LaTeX para fórmulas quando necessário."
    )
    full = f"Contexto:\n{contexto_truncado}\n\nInstrução (ID: {_nonce(cache_buster)}):\n{prompt}"
    return ollama_client.generate(full, model, provider=provider)


def generate_exercises(contexto, user_prompt, model, cache_buster=None, provider=None):
    if provider is None:
        provider = _default_provider()
    contexto_truncado = _truncate_context(contexto)
    prompt = (
        f"Com base no conteúdo, {user_prompt}. "
        "Cada questão de múltipla escolha deve ter EXATAMENTE 5 alternativas "
        "(A) até (E), no padrão das provas do Colégio Militar. "
        "Indique a resposta correta (gabarito) ao final de cada questão. "
        "Coloque cada alternativa em uma nova linha, indentada com 4 espaços, "
        "iniciando com 'A) ', 'B) ', 'C) ', 'D) ', 'E) '. "
        "Use LaTeX quando necessário. Sempre respeite o pedido do prompt."
    )
    full = f"Contexto:\n{contexto_truncado}\n\nInstrução (ID: {_nonce(cache_buster)}):\n{prompt}"
    raw = ollama_client.generate(full, model, provider=provider)
    return format_alternativas(raw) if raw else raw


def refinar_texto(raw_text, model, provider=None):
    if not raw_text or not model:
        return raw_text
    if provider is None:
        provider = _default_provider()
    prompt = (
        "O texto abaixo foi extraído por OCR e está bagunçado, com palavras quebradas, "
        "caracteres trocados e estrutura confusa.\n"
        "Reorganize, corrija e estruture o texto para ficar legível, mantendo o conteúdo original.\n"
        "- Corrija erros comuns de OCR (ex: 'crianqa' -> 'criança').\n"
        "- Organize em parágrafos ou tópicos coerentes.\n"
        "- Se houver questões, mantenha numeração e alternativas.\n"
        "- Preserve números, fórmulas e o significado original. Não invente informações.\n"
        "- Responda APENAS com o texto corrigido e organizado.\n\n"
        f"Texto bruto do OCR:\n{raw_text}"
    )
    try:
        refined = ollama_client.generate(prompt, model, provider=provider, temperature=0.2)
        return refined if refined else raw_text
    except ollama_client.LLMError:
        return raw_text