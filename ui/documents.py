import os
import streamlit as st
from pathlib import Path

from core.config import aluno_dir, list_files
from core.exporters import save_uploaded_file
from extractors import EXTENSOES_SUPORTADAS, extract_files
from extractors.cache import get_cached
from ui import chave


def render_documents(aluno, model, refine, provider):
    st.subheader(f"Documentos - {aluno}")

    folder = aluno_dir(aluno)

    # --- Controles principais no topo ---
    col_main1, col_main2, col_main3 = st.columns([2, 1, 1])
    with col_main1:
        extrair_btn = st.button(
            "Atualizar contexto (extrair todos)",
            key=chave(aluno, "extrair_todos_btn"),
            type="primary",
            use_container_width=True,
        )
    with col_main2:
        modo_rapido = st.checkbox(
            "Modo rápido",
            value=True,
            key=chave(aluno, "modo_rapido"),
            help="Apenas texto nativo, sem OCR. Muito mais rápido.",
        )
    with col_main3:
        max_workers = st.number_input(
            "Workers",
            min_value=1,
            max_value=16,
            value=min(8, (os.cpu_count() or 4)),
            key=chave(aluno, "max_workers"),
            help="Processos paralelos.",
        )

    # Upload de arquivos
    uploaded = st.file_uploader(
        "Enviar arquivos (PDF, PPTX, DOCX, TXT, MD, JSON, CSV, HTML, PNG, JPG)",
        type=EXTENSOES_SUPORTADAS,
        key=chave(aluno, "uploader"),
        accept_multiple_files=True,
    )
    if uploaded:
        for up in uploaded:
            marcador = chave(aluno, "ultimo_upload", up.name)
            if st.session_state.get(marcador) != up.name:
                save_uploaded_file(up, str(folder))
                st.session_state[marcador] = up.name
        st.cache_data.clear()
        st.rerun()

    files = list_files(aluno)

    if not files:
        st.info("Nenhum arquivo nesta pasta ainda. Envie arquivos acima.")
        return

    arquivos_processados = st.session_state.get(chave(aluno, "arquivos_processados"), [])

    # Status resumido
    total = len(files)
    cached_count = sum(1 for rel in files if get_cached(folder.joinpath(*rel.parts)) is not None)
    processados_count = len(arquivos_processados)
    
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    col_stat1.metric("Total arquivos", total)
    col_stat2.metric("Em cache", cached_count)
    col_stat3.metric("Processados na última extração", processados_count)

    st.markdown("### Arquivos do aluno")
    cols = st.columns([0.05, 0.45, 0.25, 0.15, 0.1])
    headers = ["", "Arquivo", "Tipo", "Tamanho", "Status"]
    for col, header in zip(cols, headers):
        col.caption(header)

    for rel in files:
        abs_path = folder.joinpath(*rel.parts)
        size_kb = abs_path.stat().st_size / 1024 if abs_path.exists() else 0
        ext = abs_path.suffix.lower()
        cached = get_cached(abs_path) is not None
        foi_processado = rel.as_posix() in arquivos_processados

        c1, c2, c3, c4, c5 = st.columns([0.05, 0.45, 0.25, 0.15, 0.1])
        c1.write("")
        c2.write(f"**{rel.name}**")
        c3.caption(ext[1:] if ext else "-")
        c4.caption(f"{size_kb:.1f} KB")

        if cached:
            c5.success("Cache OK")
        elif foi_processado:
            c5.warning("Sem texto extraído")
        else:
            c5.warning("Pendente")

    # Ação de extração
    if extrair_btn:
        caminhos = [folder.joinpath(*rel.parts) for rel in files]
        barra = st.progress(0.0)
        status = st.empty()

        def ao_progresso(concluidos, total, nome):
            barra.progress(concluidos / total)
            status.text(f"Extraindo {concluidos}/{total}: {nome}")

        with st.spinner("Extraindo texto de todos os arquivos (paralelo, com cache)..."):
            contexto = extract_files(
                caminhos,
                model=model,
                refine=refine,
                progress_cb=ao_progresso,
                max_workers=max_workers,
                quick_mode=modo_rapido,
                provider=provider,
            )
        barra.empty()
        status.empty()
        if contexto.strip():
            st.session_state[chave(aluno, "ctx")] = contexto
            import time
            st.session_state[chave(aluno, "ultima_extracao")] = time.time()
            st.session_state[chave(aluno, "arquivos_processados")] = [r.as_posix() for r in files]
            st.success(f"Contexto atualizado! {len(files)} arquivo(s) processados.")
            st.rerun()
        else:
            st.warning("Nenhum texto foi extraído dos arquivos.")