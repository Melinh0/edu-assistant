import os
import re
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from utils.file_utils import save_uploaded_file, get_files_list, delete_file, create_download_link
from utils.ocr import extract_text_from_file
from utils.llm import generate_plan, generate_exercises, get_available_models, call_ollama, call_ollama_stream
from utils.pdf_processor import process_pdf

BASE_DIR = Path(__file__).parent
MAX_CONTEXT_CHARS = int(os.getenv("MAX_CONTEXT_CHARS"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE"))
SUMMARIZE_TIMEOUT = int(os.getenv("SUMMARIZE_TIMEOUT"))

def extract_urls_from_text(text):
    raw = re.findall(r'https?://[^\s<>"]+', text)
    cleaned = []
    for url in raw:
        url = url.rstrip('.,;!?()')
        cleaned.append(url)
    return cleaned

def fetch_url_content(url, timeout=10, max_chars=8000):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text(separator='\n', strip=True)
        lines = (line.strip() for line in text.splitlines() if line.strip())
        content = '\n'.join(lines)
        if len(content) > max_chars:
            content = content[:max_chars] + "\n... [conteúdo truncado]"
        return content
    except Exception as e:
        return f"[Erro ao acessar URL: {str(e)}]"

def summarize_chunk(chunk, model):
    if not chunk or len(chunk) < 100:
        return chunk
    prompt = f"Resuma o seguinte texto de forma concisa, mantendo todas as informações importantes e os pontos principais:\n\n{chunk}"
    try:
        summary = call_ollama(prompt, model)
        if summary and len(summary) < len(chunk):
            return summary
        return chunk
    except Exception:
        return chunk

def split_into_chunks(text, chunk_size):
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start = end
    return chunks

def filter_context_by_keywords(context, keywords):
    if not context or not keywords:
        return context
    parts = context.split("\n\n--- ")
    filtered_parts = []
    for part in parts:
        if not part.strip():
            continue
        header = part.split(" ---", 1)[0] if " ---" in part else ""
        if any(k.lower() in header.lower() for k in keywords):
            filtered_parts.append(part)
    if filtered_parts:
        return "\n\n--- ".join(filtered_parts)
    return context

def reduce_context(context, model, target_length, keywords=None):
    if not context:
        return context
    if len(context) <= target_length:
        return context
    if keywords:
        filtered = filter_context_by_keywords(context, keywords)
        if filtered and len(filtered) < len(context):
            context = filtered
            if len(context) <= target_length:
                return context
    current_text = context
    max_iterations = 3
    iteration = 0
    while len(current_text) > target_length and iteration < max_iterations:
        iteration += 1
        chunks = split_into_chunks(current_text, CHUNK_SIZE)
        if not chunks:
            break
        summaries = []
        progress_text = st.empty()
        progress_bar = st.progress(0)
        for idx, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
            progress_text.text(f"Resumindo parte {idx+1} de {len(chunks)}...")
            summarized = summarize_chunk(chunk, model)
            if summarized:
                summaries.append(summarized)
            progress_bar.progress((idx + 1) / len(chunks))
        progress_bar.empty()
        progress_text.empty()
        if not summaries:
            break
        current_text = "\n\n".join(summaries)
        if len(current_text) <= target_length:
            break
    if len(current_text) > target_length:
        current_text = current_text[:target_length]
    return current_text

st.set_page_config(page_title="Edu Assistant", layout="wide")
st.title("📚 Edu Assistant – Gerador de Planos, Exercícios e Chat")

with st.sidebar:
    st.header("⚙️ Configurações")
    models = get_available_models()
    default_model = models[0] if models else "gemma3:4b"
    selected_model = st.selectbox("Modelo LLM", models if models else ["gemma3:4b"], key="llm_model")

    default_path = str(BASE_DIR / "docs")
    file_or_folder = st.text_input("Caminho do arquivo ou pasta", value=default_path)

    if st.button("🔄 Recarregar arquivos"):
        st.cache_data.clear()
        if "loaded_path" in st.session_state:
            del st.session_state["loaded_path"]
        st.rerun()

    st.divider()
    st.subheader("📊 Estatísticas do Contexto")
    current_path = str(Path(file_or_folder).resolve())
    if "loaded_path" not in st.session_state or st.session_state.loaded_path != current_path:
        with st.spinner("Carregando arquivos..."):
            all_files = []
            path_obj = Path(file_or_folder)
            if path_obj.exists():
                if path_obj.is_file():
                    all_files = [path_obj.name]
                elif path_obj.is_dir():
                    all_files = [f.name for f in path_obj.glob("*") if f.suffix.lower() in [".pdf", ".docx", ".pptx", ".txt", ".png", ".jpg", ".jpeg"]]
            st.session_state.all_files = all_files
            st.session_state.loaded_path = current_path
            st.session_state.messages = []

    if "context_text" in st.session_state and st.session_state.context_text:
        char_count = len(st.session_state.context_text)
        word_count = len(st.session_state.context_text.split())
        st.metric("Caracteres", f"{char_count:,}")
        st.metric("Palavras", f"{word_count:,}")
        st.metric("Arquivos carregados", len(st.session_state.get("selected_files", [])))
        if st.session_state.get("selected_files"):
            st.caption("Arquivos selecionados:")
            for f in st.session_state.selected_files:
                st.write(f"- {f}")
    else:
        st.info("Nenhum contexto carregado.")

    if st.button("🧹 Limpar contexto (reset)"):
        st.session_state.context_text = ""
        st.session_state.selected_files = []
        st.session_state.messages = []
        st.rerun()

if "context_text" not in st.session_state:
    st.session_state.context_text = ""
    st.session_state.selected_files = []
    st.session_state.messages = []
    st.session_state.modo = None
    st.session_state.last_prompt = ""

st.subheader("📂 Documentos disponíveis")

uploaded_file = st.file_uploader(
    "Envie um arquivo (PDF, PPTX, PNG, JPG, JPEG, TXT, DOCX)",
    type=["pdf", "pptx", "png", "jpg", "jpeg", "txt", "docx"]
)

if "upload_processed" not in st.session_state:
    st.session_state.upload_processed = False
if "last_uploaded" not in st.session_state:
    st.session_state.last_uploaded = None

if uploaded_file is not None:
    if not st.session_state.upload_processed or st.session_state.last_uploaded != uploaded_file.name:
        st.session_state.upload_processed = False
        st.session_state.last_uploaded = uploaded_file.name
        target_folder = Path(file_or_folder)
        if not target_folder.exists():
            target_folder = BASE_DIR / "docs"
            target_folder.mkdir(exist_ok=True)
        file_path = save_uploaded_file(uploaded_file, str(target_folder))
        if file_path:
            st.session_state.upload_processed = True
            st.success(f"Arquivo {uploaded_file.name} salvo com sucesso!")
            st.cache_data.clear()
            st.rerun()

if Path(file_or_folder).exists():
    files = get_files_list(file_or_folder)
    if files:
        st.write("Selecione os arquivos para extrair:")
        selected = []
        for f in files:
            col1, col2, col3 = st.columns([0.08, 0.62, 0.30], gap="small")
            with col1:
                checked = st.checkbox(
                    f"Selecionar {f}",
                    key=f"sel_{f}",
                    value=f in st.session_state.get("selected_files", []),
                    label_visibility="collapsed"
                )
                if checked:
                    selected.append(f)
            with col2:
                st.write(f)
            with col3:
                btn1, btn2 = st.columns(2, gap="small")
                with btn1:
                    file_path = os.path.join(file_or_folder, f)
                    with open(file_path, "rb") as file:
                        st.download_button(
                            "📥",
                            data=file,
                            file_name=f,
                            key=f"dl_{f}",
                            use_container_width=False
                        )
                with btn2:
                    if st.button("🗑️", key=f"del_{f}", use_container_width=False):
                        delete_file(f, file_or_folder)
                        st.cache_data.clear()
                        st.rerun()
        if selected != st.session_state.get("selected_files", []):
            st.session_state.selected_files = selected

        if st.button("📄 Extrair texto dos selecionados"):
            if selected:
                context = ""
                with st.spinner("Extraindo texto dos arquivos selecionados..."):
                    for f in selected:
                        file_path = os.path.join(file_or_folder, f)
                        if f.lower().endswith(".pdf"):
                            import tempfile
                            with tempfile.TemporaryDirectory() as tmpdir:
                                tmp_path = Path(tmpdir)
                                pdf_src = Path(file_path)
                                pdf_dest = tmp_path / pdf_src.name
                                with open(pdf_src, 'rb') as src:
                                    with open(pdf_dest, 'wb') as dst:
                                        dst.write(src.read())
                                process_pdf(pdf_dest, tmp_path / "output")
                                txt_files = list((tmp_path / "output").glob("*.txt"))
                                if txt_files:
                                    page_text = ""
                                    for txt_file in sorted(txt_files):
                                        with open(txt_file, 'r', encoding='utf-8') as tf:
                                            page_text += f"\n--- {f} - {txt_file.stem} ---\n"
                                            page_text += tf.read() + "\n"
                                    context += page_text
                                else:
                                    st.warning(f"Falha ao extrair texto do PDF {f}")
                        else:
                            with open(file_path, "rb") as fh:
                                file_bytes = fh.read()
                            text = extract_text_from_file(file_bytes, f, model=selected_model)
                            if text:
                                context += f"\n--- {f} ---\n{text}\n"
                            else:
                                st.warning(f"Falha ao extrair {f}")
                    if context.strip():
                        st.session_state.context_text = context
                        st.success("Texto extraído com sucesso!")
                    else:
                        st.warning("Nenhum texto foi extraído.")
            else:
                st.warning("Selecione pelo menos um arquivo.")

if st.session_state.context_text:
    st.text_area("📝 Contexto extraído (prévia)", st.session_state.context_text[:1000], height=150)

st.divider()
st.subheader("💬 Chat livre com o contexto")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Digite sua pergunta sobre os documentos...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    if not st.session_state.context_text.strip():
        st.error("Nenhum contexto carregado. Selecione arquivos e extraia o texto.")
    else:
        context = st.session_state.context_text

        history = st.session_state.messages[-5:] if len(st.session_state.messages) > 5 else st.session_state.messages
        history_text = ""
        for msg in history:
            if msg["role"] == "user":
                history_text += f"Usuário: {msg['content']}\n"
            else:
                history_text += f"Assistente: {msg['content']}\n"

        total_prompt_chars = len(history_text) + len(context) + len(user_input) + 500
        if total_prompt_chars > MAX_CONTEXT_CHARS:
            st.info("Contexto muito longo. Resumindo para caber no limite do modelo...")
            try:
                keywords = [w for w in user_input.lower().split() if len(w) > 4]
                target_len = MAX_CONTEXT_CHARS - len(history_text) - len(user_input) - 500
                target_len = max(target_len, 500)
                reduced = reduce_context(context, selected_model, target_len, keywords=keywords[:3])
                if reduced and len(reduced) < len(context):
                    context = reduced
                else:
                    context = context[:target_len]
            except Exception as e:
                st.error(f"Erro ao reduzir contexto: {e}")
                context = context[:MAX_CONTEXT_CHARS]

        full_prompt = f"""
Histórico da conversa:
{history_text}

Contexto dos documentos:
{context}

Pergunta atual:
{user_input}
"""

        with st.chat_message("assistant"):
            with st.spinner("Gerando resposta..."):
                response = call_ollama_stream(
                    prompt=full_prompt,
                    model=selected_model,
                    context=""
                )
                if response:
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                else:
                    st.error("Erro ao obter resposta da IA.")

st.divider()
st.subheader("📌 Ferramentas rápidas")
user_prompt = st.text_input(
    "Tema ou instrução específica (para plano/exercícios):",
    key="prompt_tool",
    value=st.session_state.get("last_prompt", "")
)
col1, col2 = st.columns(2)
with col1:
    if st.button("📋 Gerar Plano de Aula"):
        if user_prompt:
            if not st.session_state.context_text.strip():
                st.error("Nenhum contexto carregado.")
            else:
                st.session_state.last_prompt = user_prompt
                st.cache_data.clear()
                st.session_state.geracao_id = st.session_state.get("geracao_id", 0) + 1
                with st.spinner("Gerando plano..."):
                    plan = generate_plan(
                        st.session_state.context_text,
                        user_prompt,
                        selected_model,
                        cache_buster=st.session_state.geracao_id
                    )
                    st.session_state.plan = plan
                    st.session_state.modo = "plan"
                    if "exercises" in st.session_state:
                        del st.session_state.exercises
                    st.rerun()
        else:
            st.warning("Digite um tema.")
with col2:
    if st.button("📝 Gerar Exercícios"):
        if user_prompt:
            if not st.session_state.context_text.strip():
                st.error("Nenhum contexto carregado.")
            else:
                st.session_state.last_prompt = user_prompt
                st.cache_data.clear()
                st.session_state.geracao_id = st.session_state.get("geracao_id", 0) + 1
                with st.spinner("Gerando exercícios..."):
                    exercises = generate_exercises(
                        st.session_state.context_text,
                        user_prompt,
                        selected_model,
                        cache_buster=st.session_state.geracao_id
                    )
                    st.session_state.exercises = exercises
                    st.session_state.modo = "exercises"
                    if "plan" in st.session_state:
                        del st.session_state.plan
                    st.rerun()
        else:
            st.warning("Digite um tema.")

if st.session_state.get("modo") == "plan" and "plan" in st.session_state:
    st.subheader("📖 Plano de Aula")
    st.text_area(
        "Edite o texto do Plano (markdown):",
        key="plan",
        height=300
    )
    st.markdown("---")
    st.markdown(st.session_state.plan)
    col1, col2, col3 = st.columns(3)
    with col1:
        b, fn, mt = create_download_link(st.session_state.plan, "plano_aula", "txt")
        st.download_button("Baixar TXT", data=b, file_name=fn, mime=mt)
    with col2:
        b, fn, mt = create_download_link(st.session_state.plan, "plano_aula", "docx")
        st.download_button("Baixar DOCX", data=b, file_name=fn, mime=mt)
    with col3:
        b, fn, mt = create_download_link(st.session_state.plan, "plano_aula", "pdf")
        st.download_button("Baixar PDF", data=b, file_name=fn, mime=mt)

elif st.session_state.get("modo") == "exercises" and "exercises" in st.session_state:
    st.subheader("📝 Lista de Exercícios")
    st.text_area(
        "Edite os Exercícios (markdown):",
        key="exercises",
        height=300
    )
    st.markdown("---")
    st.markdown(st.session_state.exercises)
    col1, col2, col3 = st.columns(3)
    with col1:
        b, fn, mt = create_download_link(st.session_state.exercises, "exercicios", "txt")
        st.download_button("Baixar TXT", data=b, file_name=fn, mime=mt)
    with col2:
        b, fn, mt = create_download_link(st.session_state.exercises, "exercicios", "docx")
        st.download_button("Baixar DOCX", data=b, file_name=fn, mime=mt)
    with col3:
        b, fn, mt = create_download_link(st.session_state.exercises, "exercicios", "pdf")
        st.download_button("Baixar PDF", data=b, file_name=fn, mime=mt)

elif st.session_state.get("modo"):
    st.info("Gere um plano de aula ou lista de exercícios para começar.")

st.caption("Nota: O contexto é extraído dos arquivos da pasta/arquivo selecionado. Para respostas mais precisas, mantenha o prompt relevante.")