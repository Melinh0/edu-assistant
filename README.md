# Edu Assistant

Ferramenta para professores particulares: gerencie PDFs de alunos, extraia texto com OCR e gere planos de aula e exercícios personalizados usando modelos LLM (Ollama).

## Funcionalidades
- Upload e gerenciamento de PDFs
- Extração de texto via OCR.space
- Seleção de múltiplos documentos como contexto
- Geração de planos de aula detalhados
- Geração de listas de exercícios com gabarito
- Download dos resultados em TXT, DOCX ou PDF

## Como usar com Docker

### Pré-requisitos
- Docker e Docker Compose instalados

### Passos
1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/edu-assistant.git
   cd edu-assistant
   ```

2. Copie o arquivo de exemplo de variáveis de ambiente:
   ```bash
   cp .env.example .env
   ```
   Edite o `.env` com suas chaves da API (OCR.space) e, se necessário, ajuste o `OLLAMA_HOST` (padrão `http://ollama:11434` para uso com Docker).

3. Inicie os serviços com Docker Compose:
   ```bash
   docker-compose up -d
   ```

4. Aguarde o download dos modelos Ollama (a primeira execução pode levar alguns minutos). Para baixar um modelo específico, execute:
   ```bash
   docker exec -it edu-assistant-ollama-1 ollama pull gemma3:4b
   ```
   (Substitua pelo modelo desejado, conforme listado no `.env`)

5. Acesse a aplicação em `http://localhost:8501` no navegador.

6. Para parar os containers:
   ```bash
   docker-compose down
   ```

## Como usar sem Docker (desenvolvimento local)

1. Instale o Python 3.12+ e o `uv`:
   ```bash
   pip install uv
   ```

2. Instale as dependências:
   ```bash
   uv sync
   ```

3. Configure o arquivo `.env` com as variáveis necessárias (veja `.env.example`).

4. Execute a aplicação:
   ```bash
   uv run streamlit run app.py
   ```

5. Acesse `http://localhost:8501` no navegador.

## Variáveis de ambiente

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `OLLAMA_API_KEY` | Chave da API Ollama (opcional para local) | `sk-...` |
| `OLLAMA_HOST` | URL do servidor Ollama | `http://ollama:11434` |
| `OLLAMA_AVAILABLE_MODELS` | Lista de modelos separados por vírgula | `gemma3:4b,gemma4:31b` |
| `OLLAMA_MAX_TOKENS` | Máximo de tokens gerados | `4096` |
| `OCR_SPACE_API_KEY` | Chave da API OCR.space (obrigatória) | `K...` |

## Tecnologias
- Streamlit (interface)
- OCR.space (OCR)
- Ollama (LLM)
- python-docx, reportlab (exportação)
- Docker (containerização)