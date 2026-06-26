import os
import requests
import streamlit as st
import re

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_HOST = os.getenv("OLLAMA_HOST")
OLLAMA_MAX_TOKENS = int(os.getenv("OLLAMA_MAX_TOKENS"))

def get_available_models():
    models_str = os.getenv("OLLAMA_AVAILABLE_MODELS", "gemma3:4b, gemma4:31b, gemma3:12b")
    return [m.strip() for m in models_str.split(',')]

def call_ollama(prompt, model, context=""):
    full_prompt = f"Contexto:\n{context}\n\nInstrução:\n{prompt}"
    headers = {
        "Authorization": f"Bearer {OLLAMA_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "num_predict": OLLAMA_MAX_TOKENS
        }
    }
    url = f"{OLLAMA_HOST}/api/generate"
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=600)
        if response.status_code == 200:
            data = response.json()
            return data.get('response', '')
        else:
            st.error(f"Erro na API Ollama: {response.status_code} - {response.text}")
            return ""
    except Exception as e:
        st.error(f"Exceção na chamada Ollama: {str(e)}")
        return ""

def format_alternatives(text):
    lines = text.split('\n')
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if re.match(r'^[a-d]\)', stripped):
            new_lines.append('    - ' + stripped + '  ')
        elif re.match(r'^[a-d]\.', stripped):
            new_lines.append('    - ' + stripped + '  ')
        else:
            new_lines.append(line)
    return '\n'.join(new_lines)

def generate_plan(context, user_prompt, model):
    prompt = f"Com base no conteúdo fornecido, crie um plano de aula detalhado e roteiro para o tema: {user_prompt}. Inclua objetivos, materiais, atividades e avaliação. Use formatação LaTeX para expressões matemáticas quando necessário."
    raw = call_ollama(prompt, model, context)
    return raw

def generate_exercises(context, user_prompt, model):
    prompt = (
        f"Com base no conteúdo fornecido, crie uma lista com EXATAMENTE 10 questões de múltipla escolha sobre o tema: {user_prompt}. "
        "Cada questão deve ter 4 alternativas (a, b, c, d). "
        "Para cada questão, escreva o enunciado em uma linha. Em seguida, escreva cada alternativa em uma nova linha, "
        "iniciando com 'a) ', 'b) ', 'c) ', 'd) ' e indentada com 4 espaços. "
        "No final, inclua um gabarito com as respostas corretas (ex: 'Gabarito: 1-a, 2-b, ...'). "
        "Use formatação LaTeX para expressões matemáticas quando necessário. "
        "Não use marcadores de lista como '*' ou '-', apenas as letras e parênteses."
    )
    raw = call_ollama(prompt, model, context)
    if raw:
        raw = format_alternatives(raw)
    return raw