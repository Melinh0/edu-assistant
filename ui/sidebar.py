import streamlit as st
from datetime import datetime

from core.config import (
    LLM_REFINE_DEFAULT,
    aluno_dir,
    create_aluno,
    get_llm_providers,
    get_models_for_provider,
    list_alunos,
)
from ui import chave


def render_sidebar():
    pendente = st.session_state.pop("_selecionar_aluno", None)
    if pendente:
        st.session_state["aluno_selecionado"] = pendente

    st.header("Configurações")

    alunos = list_alunos()
    aluno = st.selectbox("Aluno", alunos, key="aluno_selecionado")

    with st.expander("Novo aluno"):
        novo = st.text_input("Nome do novo aluno", key="novo_aluno_nome")
        if st.button("Criar aluno", key="criar_aluno_btn"):
            if novo.strip():
                try:
                    create_aluno(novo)
                    st.session_state["_selecionar_aluno"] = novo.strip().lower().replace(" ", "_")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
            else:
                st.warning("Digite um nome.")

    providers = get_llm_providers()
    if not providers:
        st.error("Nenhum provedor LLM configurado. Defina OLLAMA_API_KEYS ou NVIDIA_API_KEYS no .env")
        st.stop()

    provider = st.selectbox("Provedor LLM", providers, key="llm_provider")

    # Sempre apenas modelos gratuitos para Ollama
    apenas_gratuitos = (provider == "ollama")
    modelos = get_models_for_provider(provider, only_free=apenas_gratuitos)
    model = st.selectbox("Modelo", modelos, key="llm_model")

    refinar = st.checkbox(
        "Refinar texto extraído com LLM (lento)",
        value=LLM_REFINE_DEFAULT,
        key="refinar_llm",
    )

    st.divider()
    st.subheader("Contexto do Aluno")

    contexto = st.session_state.get(chave(aluno, "ctx"), "")
    arquivos_processados = st.session_state.get(chave(aluno, "arquivos_processados"), [])
    ultima_extracao = st.session_state.get(chave(aluno, "ultima_extracao"), 0)

    if contexto:
        col1, col2 = st.columns(2)
        col1.metric("Caracteres", f"{len(contexto):,}")
        col2.metric("Arquivos", len(arquivos_processados))

        if ultima_extracao:
            try:
                dt = datetime.fromtimestamp(ultima_extracao)
                st.caption(f"Atualizado em: {dt.strftime('%d/%m/%Y %H:%M')}")
            except Exception:
                pass

        if arquivos_processados:
            with st.expander("Ver arquivos incluídos"):
                for nome in arquivos_processados:
                    st.caption(f"- {nome}")
    else:
        st.info("Nenhum contexto carregado. Vá na aba Documentos e clique em 'Atualizar contexto'.")

    if st.button("Limpar tudo (contexto + chat)", key="limpar_tudo"):
        st.session_state[chave(aluno, "ctx")] = ""
        st.session_state[chave(aluno, "arquivos_processados")] = []
        st.session_state[chave(aluno, "ultima_extracao")] = 0
        st.session_state[chave(aluno, "msgs")] = []
        st.cache_data.clear()
        st.rerun()

    st.divider()
    folder = aluno_dir(aluno)
    st.caption(f"Pasta: `{folder.name}/`")

    return {"aluno": aluno, "model": model, "refine": refinar, "provider": provider}