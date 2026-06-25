# Edu Assistant

Ferramenta para professores particulares: gerencie PDFs de alunos, extraia texto com OCR e gere planos de aula e exercícios personalizados usando modelos LLM (Ollama).

## Funcionalidades
- Upload e gerenciamento de PDFs
- Extração de texto via OCR.space
- Seleção de múltiplos documentos como contexto
- Geração de planos de aula detalhados
- Geração de listas de exercícios com gabarito
- Download dos resultados em TXT, DOCX ou PDF

## Como usar
1. Clone o repositório.
2. Instale as dependências: `pip install -r requirements.txt`
3. Configure as variáveis de ambiente no arquivo `.env` (veja `.env.example`).
4. Execute: `streamlit run app.py`
5. Acesse `http://localhost:8501` no navegador.

## Variáveis de ambiente
- `OLLAMA_API_KEY`: chave da API Ollama
- `OLLAMA_HOST`: URL da API (padrão: https://ollama.com)
- `OCR_SPACE_API_KEY`: chave da API OCR.space
- `OLLAMA_AVAILABLE_MODELS`: lista de modelos separados por vírgula
- `OLLAMA_MAX_TOKENS`: limite máximo de tokens gerados

## Tecnologias
- Streamlit (interface)
- OCR.space (OCR)
- Ollama (LLM)
- python-docx, fpdf (exportação)