import os
import requests
import streamlit as st

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

def generate_plan(context, user_prompt, model):
    prompt = f"Com base no conteúdo fornecido, crie um plano de aula detalhado e roteiro para o tema: {user_prompt}. Inclua objetivos, materiais, atividades e avaliação."
    return call_ollama(prompt, model, context)

def generate_exercises(context, user_prompt, model):
    prompt = f"Com base no conteúdo fornecido, crie uma lista de exercícios sobre o tema: {user_prompt}. Inclua questões de múltipla escolha e dissertativas, com gabarito."
    return call_ollama(prompt, model, context)