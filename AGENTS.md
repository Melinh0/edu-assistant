# AGENTS.md — Convenções do projeto

## Comandos

- Instalar dependências: `uv sync`
- Rodar o app: `uv run streamlit run app.py`
- Verificar sintaxe: `uv run python -m compileall -q app.py core extractors ui scripts`
- Baixar materiais do aluno: `uv run python scripts/fetch_student_sources.py`

## Estrutura

- `app.py` — entrada fina: só monta `render_sidebar()` + `render_documents()` + `render_chat()` + `render_tools()`.
- `core/` — `config` (env e pastas), `ollama_client` (HTTP + rotação de chaves), `generators` (prompts), `exporters` (txt/docx/pdf), `retrieval` (BM25).
- `extractors/` — dispatch por extensão em `__init__`, `pdf` (PyMuPDF + Tesseract paralelo + OCR.space + visão), `office`, `plain`, `image`, `cache`, `clean`.
- `ui/` — componentes Streamlit; estado em `session_state` com prefixo `"<aluno>::<chave>"`.
- `docs/<aluno>/` — um diretório por aluno; `.cache/` guarda extrações (ignorado pelo git).

## Convenções

- Nada de comentários ou docstrings nos `.py`.
- Sem `streamlit` fora de `ui/` e `app.py`: `core/` e `extractors/` devem rodar sem UI (testáveis via script).
- Nunca alterar dígitos, acentos ou fórmulas na limpeza de texto: `extractors/clean.py` só normaliza espaços/quebras de linha (`clean_ocr` só desfaz hifenização de fim de linha).
- Refino de texto com LLM é opcional (checkbox, padrão desligado) — extração nunca deve depender de LLM.
- Chaves de API só via `.env` (`OLLAMA_API_KEYS` em rotação); nunca hardcodar chaves em código.
- Toda chamada ao Ollama passa por `core/ollama_client.py` (failover automático em 429/cota).
- Exercícios de múltipla escolha: sempre 5 alternativas (A–E), padrão Colégio Militar.
- Formatos suportados listados em `extractors.EXTENSOES_SUPORTADAS` (fonte única para o uploader).

## Verificação após mudanças

1. `uv run python -m compileall -q app.py core extractors ui scripts`
2. Teste de extração real em `docs/maurinho/` (primeira extração lê o arquivo; repetição deve vir do cache).
3. Teste de rotação: resposta deve alternar chaves; 429 deve fazer failover sem derrubar a chamada.
