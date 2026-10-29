import streamlit as st

from ui.chat import render_chat
from ui.documents import render_documents
from ui.sidebar import render_sidebar
from ui.tools import render_tools

st.set_page_config(page_title="Edu Assistant", layout="wide", initial_sidebar_state="expanded")

st.title("Edu Assistant - Gerador de Planos, Exercícios e Chat")

cfg = render_sidebar()

tab_docs, tab_chat, tab_tools = st.tabs(["Documentos", "Chat", "Ferramentas"])

with tab_docs:
    render_documents(**cfg)

with tab_chat:
    render_chat(**cfg)

with tab_tools:
    render_tools(**cfg)

st.caption("O contexto é extraído automaticamente de todos os arquivos da pasta do aluno selecionado e buscado por BM25 a cada pergunta.")