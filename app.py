import streamlit as st
import os
from dotenv import load_dotenv
load_dotenv()

from utils.file_utils import save_uploaded_file, get_files_list, delete_file, create_download_link
from utils.ocr import extract_text_from_pdf
from utils.llm import generate_plan, generate_exercises, get_available_models

st.set_page_config(page_title="Edu Assistant", layout="wide")

DOCS_DIR = "docs"
os.makedirs(DOCS_DIR, exist_ok=True)

st.title("📚 Edu Assistant - Gerador de Planos e Exercícios")

uploaded_file = st.file_uploader("Envie um PDF", type=["pdf"])
if uploaded_file:
    save_uploaded_file(uploaded_file, DOCS_DIR)
    st.success(f"Arquivo {uploaded_file.name} salvo com sucesso!")

files = get_files_list(DOCS_DIR)
if files:
    st.subheader("Documentos disponíveis")
    selected_files = []
    for f in files:
        col1, col2, col3 = st.columns([0.7, 0.15, 0.15])
        with col1:
            if st.checkbox(f, key=f):
                selected_files.append(f)
        with col2:
            with open(os.path.join(DOCS_DIR, f), "rb") as file:
                st.download_button("📥", data=file, file_name=f, key=f"dl_{f}")
        with col3:
            if st.button("🗑️", key=f"del_{f}"):
                delete_file(f, DOCS_DIR)
                st.rerun()

    if selected_files:
        st.subheader("Contexto selecionado")
        models = get_available_models()
        default_model = models[0] if models else "gemma3:4b"
        model = st.selectbox("Modelo LLM (para extração com visão)", models if models else ["gemma3:4b"], key="vision_model")

        if st.button("Extrair texto dos selecionados"):
            context = ""
            for f in selected_files:
                file_path = os.path.join(DOCS_DIR, f)
                with open(file_path, "rb") as fh:
                    pdf_bytes = fh.read()
                text = extract_text_from_pdf(pdf_bytes, model=model)
                if text:
                    context += f"\n--- {f} ---\n{text}\n"
                else:
                    st.warning(f"Não foi possível extrair texto de {f}")
            if context.strip():
                st.session_state['context'] = context[:30000]
                st.success("Texto extraído com sucesso!")
            else:
                st.warning("Não foi possível extrair texto dos PDFs selecionados.")

        if 'context' in st.session_state:
            st.text_area("Contexto extraído (prévia)", st.session_state['context'][:1000], height=150)
            user_prompt = st.text_input("Digite o tema ou instrução para o plano/exercícios:")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Gerar Plano de Aula"):
                    if user_prompt:
                        with st.spinner("Gerando plano..."):
                            plan = generate_plan(st.session_state['context'], user_prompt, model)
                            st.session_state['plan'] = plan
                    else:
                        st.warning("Digite um tema.")
            with col2:
                if st.button("Gerar Exercícios"):
                    if user_prompt:
                        with st.spinner("Gerando exercícios..."):
                            exercises = generate_exercises(st.session_state['context'], user_prompt, model)
                            st.session_state['exercises'] = exercises
                    else:
                        st.warning("Digite um tema.")

            if 'plan' in st.session_state:
                st.subheader("Plano de Aula")
                st.write(st.session_state['plan'])
                col1, col2, col3 = st.columns(3)
                with col1:
                    b, fn, mt = create_download_link(st.session_state['plan'], "plano_aula", "txt")
                    st.download_button("Baixar TXT", data=b, file_name=fn, mime=mt)
                with col2:
                    b, fn, mt = create_download_link(st.session_state['plan'], "plano_aula", "docx")
                    st.download_button("Baixar DOCX", data=b, file_name=fn, mime=mt)
                with col3:
                    b, fn, mt = create_download_link(st.session_state['plan'], "plano_aula", "pdf")
                    st.download_button("Baixar PDF", data=b, file_name=fn, mime=mt)

            if 'exercises' in st.session_state:
                st.subheader("Lista de Exercícios")
                st.write(st.session_state['exercises'])
                col1, col2, col3 = st.columns(3)
                with col1:
                    b, fn, mt = create_download_link(st.session_state['exercises'], "exercicios", "txt")
                    st.download_button("Baixar TXT", data=b, file_name=fn, mime=mt)
                with col2:
                    b, fn, mt = create_download_link(st.session_state['exercises'], "exercicios", "docx")
                    st.download_button("Baixar DOCX", data=b, file_name=fn, mime=mt)
                with col3:
                    b, fn, mt = create_download_link(st.session_state['exercises'], "exercicios", "pdf")
                    st.download_button("Baixar PDF", data=b, file_name=fn, mime=mt)
else:
    st.info("Nenhum documento salvo. Faça upload de um PDF.")