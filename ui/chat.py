import streamlit as st

from core import ollama_client
from core.config import MAX_CONTEXT_CHARS
from core.retrieval import construir_contexto
from ui import chave


def render_chat(aluno, model, provider, **_):
    st.subheader("Chat com o aluno")

    contexto_total = st.session_state.get(chave(aluno, "ctx"), "")
    if not contexto_total.strip():
        st.warning("Nenhum contexto carregado para este aluno.")
        st.info("Vá na aba Documentos e clique em 'Atualizar contexto' para extrair o texto dos arquivos.")
        return

    msg_key = chave(aluno, "msgs")
    mensagens = st.session_state.setdefault(msg_key, [])

    for msg in mensagens:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Digite sua pergunta sobre os documentos...", key=chave(aluno, "chat"))
    if not user_input:
        return

    mensagens.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    historico = mensagens[-5:]
    history_text = "".join(
        f"{'Usuário' if m['role'] == 'user' else 'Assistente'}: {m['content']}\n"
        for m in historico
    )

    orcamento = MAX_CONTEXT_CHARS - len(history_text) - len(user_input) - 500
    contexto = construir_contexto(contexto_total, user_input, max(orcamento, 1000))

    full_prompt = (
        f"Histórico da conversa:\n{history_text}\n"
        f"Contexto dos documentos:\n{contexto}\n"
        f"Pergunta atual:\n{user_input}"
    )

    with st.chat_message("assistant"):
        placeholder = st.empty()
        try:
            with st.spinner("Gerando resposta..."):
                partes = []
                acumulado = ""
                for pedaco in ollama_client.generate_stream(full_prompt, model, provider=provider):
                    partes.append(pedaco)
                    acumulado += pedaco
                    placeholder.markdown(acumulado + "|")
                placeholder.markdown(acumulado)
            if acumulado:
                mensagens.append({"role": "assistant", "content": acumulado})
            else:
                st.error("A IA não retornou conteúdo.")
        except ollama_client.LLMError as exc:
            placeholder.empty()
            st.error(f"Erro ao chamar a IA: {exc}")