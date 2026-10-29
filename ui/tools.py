import streamlit as st

from core import ollama_client
from core.exporters import create_download_link
from core.generators import generate_exercises, generate_plan
from ui import chave


def _bloco_resultado(aluno, modo, titulo, rotulo, padrao_nome):
    ctx_key = chave(aluno, modo)
    st.subheader(titulo)
    st.text_area(f"Edite o texto ({rotulo}, markdown):", key=ctx_key, height=300)
    st.markdown("---")
    st.markdown(st.session_state.get(ctx_key, ""))
    conteudo = st.session_state.get(ctx_key, "")
    col1, col2, col3 = st.columns(3)
    with col1:
        b, fn, mt = create_download_link(conteudo, padrao_nome, "txt")
        st.download_button("Baixar TXT", data=b, file_name=fn, mime=mt, key=f"{aluno}::{modo}::txt")
    with col2:
        b, fn, mt = create_download_link(conteudo, padrao_nome, "docx")
        st.download_button("Baixar DOCX", data=b, file_name=fn, mime=mt, key=f"{aluno}::{modo}::docx")
    with col3:
        b, fn, mt = create_download_link(conteudo, padrao_nome, "pdf")
        st.download_button("Baixar PDF", data=b, file_name=fn, mime=mt, key=f"{aluno}::{modo}::pdf")


def gerar_sugestoes_ia(contexto, model, provider, tipo="plano", user_input=""):
    """Gera sugestões inteligentes baseadas no contexto e entrada do usuário usando o LLM."""
    if tipo == "plano":
        base_prompt = (
            f"Você é um assistente pedagógico especializado em criar planos de aula para o Colégio Militar. "
            f"Analise o contexto do material do aluno e a intenção do usuário (se houver) "
            f"para sugerir 5 planos de aula detalhados, específicos e práticos. "
            f"Cada sugestão deve ser um prompt completo e rico, pronto para usar, "
            f"contendo: objetivo claro, conteúdo programático, metodologia sugerida e avaliação. "
            f"Responda APENAS com uma lista numerada (1. 2. 3. 4. 5.), cada item sendo um prompt completo. "
            f"Sem introduções, sem explicações extras.\n\n"
            f"Contexto do material:\n{contexto[:3000]}\n\n"
        )
        if user_input.strip():
            base_prompt += f"Intenção do usuário: {user_input.strip()}\n\n"
        base_prompt += "Sugestões de planos de aula:"
    else:
        base_prompt = (
            f"Você é um especialista em criar exercícios no estilo Colégio Militar (múltipla escolha A-E). "
            f"Analise o contexto do material do aluno e a intenção do usuário (se houver) "
            f"para sugerir 5 listas de exercícios detalhadas, específicas e práticas. "
            f"Cada sugestão deve ser um prompt completo e rico, pronto para usar, "
            f"contendo: quantidade sugerida, tópicos específicos, nível de dificuldade, "
            f"foco em interpretação/raciocínio lógico, e formato padrão Colégio Militar. "
            f"Responda APENAS com uma lista numerada (1. 2. 3. 4. 5.), cada item sendo um prompt completo. "
            f"Sem introduções, sem explicações extras.\n\n"
            f"Contexto do material:\n{contexto[:3000]}\n\n"
        )
        if user_input.strip():
            base_prompt += f"Intenção do usuário: {user_input.strip()}\n\n"
        base_prompt += "Sugestões de listas de exercícios:"

    try:
        resposta = ollama_client.generate(base_prompt, model, provider=provider, temperature=0.4, num_predict=800)
        sugestoes = []
        for linha in resposta.split("\n"):
            linha = linha.strip()
            if linha and (linha[0].isdigit() or linha.startswith("-")):
                clean = linha.lstrip("0123456789.- ").strip()
                if clean and len(clean) > 20:
                    sugestoes.append(clean)
        return sugestoes[:5]
    except Exception as e:
        return []


def render_tools(aluno, model, provider, **_):
    st.divider()
    st.subheader("Ferramentas rápidas")

    contexto = st.session_state.get(chave(aluno, "ctx"), "")
    if not contexto.strip():
        st.warning("Nenhum contexto carregado. Atualize o contexto na aba Documentos primeiro.")
        return

    tab_plano, tab_exercicios = st.tabs(["Plano de Aula", "Exercícios"])

    with tab_plano:
        st.markdown("### Gerar Plano de Aula")
        
        sugestoes_key_plano = chave(aluno, "sugestoes_ia_plano")
        if sugestoes_key_plano not in st.session_state:
            with st.spinner("Gerando sugestões baseadas no contexto..."):
                st.session_state[sugestoes_key_plano] = gerar_sugestoes_ia(contexto, model, provider, "plano")
        
        sugestoes_plano = st.session_state[sugestoes_key_plano]
        opcoes_plano = ["-- Digite seu próprio tema --"] + sugestoes_plano
        
        sugestao_selecionada_plano = st.selectbox(
            "Sugestões baseadas no contexto (clique para usar):",
            opcoes_plano,
            key=chave(aluno, "sugestao_plano_select"),
            index=0,
        )
        
        col_refresh, col_usar = st.columns([1, 1])
        with col_refresh:
            if st.button("Atualizar sugestões", key=chave(aluno, "refresh_sugestoes_plano"), use_container_width=True):
                user_text = st.session_state.get(chave(aluno, "prompt_plano"), "")
                with st.spinner("Gerando novas sugestões adaptadas..."):
                    st.session_state[sugestoes_key_plano] = gerar_sugestoes_ia(contexto, model, provider, "plano", user_text)
                st.rerun()
        with col_usar:
            if sugestao_selecionada_plano != "-- Digite seu próprio tema --":
                if st.button("Usar esta sugestão", key=chave(aluno, "usar_sugestao_plano"), type="secondary", use_container_width=True):
                    st.session_state[chave(aluno, "prompt_plano")] = sugestao_selecionada_plano
                    st.rerun()
        
        user_prompt_plano = st.text_area(
            "Tema ou instrução específica (as sugestões acima se adaptam ao que você escrever aqui):",
            key=chave(aluno, "prompt_plano"),
            height=120,
            placeholder="Ex: Plano de aula sobre frações para o 6º ano, com foco em operações, problemas e preparação para vestibular Colégio Militar...",
        )

        if st.button("Gerar Plano de Aula", key=chave(aluno, "btn_plano"), type="primary", use_container_width=True):
            if not user_prompt_plano.strip():
                st.warning("Digite um tema ou instrução.")
            else:
                with st.spinner("Gerando plano de aula..."):
                    resultado = generate_plan(contexto, user_prompt_plano, model, provider=provider)
                if resultado:
                    st.session_state[chave(aluno, "plano")] = resultado
                    st.session_state.pop(chave(aluno, "exercicios"), None)
                    st.rerun()
                else:
                    st.error("A IA não retornou conteúdo.")

    with tab_exercicios:
        st.markdown("### Gerar Exercícios")
        
        sugestoes_key_exerc = chave(aluno, "sugestoes_ia_exerc")
        if sugestoes_key_exerc not in st.session_state:
            with st.spinner("Gerando sugestões baseadas no contexto..."):
                st.session_state[sugestoes_key_exerc] = gerar_sugestoes_ia(contexto, model, provider, "exercicios")
        
        sugestoes_exerc = st.session_state[sugestoes_key_exerc]
        opcoes_exerc = ["-- Digite seu próprio tema --"] + sugestoes_exerc
        
        sugestao_selecionada_exerc = st.selectbox(
            "Sugestões baseadas no contexto (clique para usar):",
            opcoes_exerc,
            key=chave(aluno, "sugestao_exerc_select"),
            index=0,
        )
        
        col_refresh2, col_usar2 = st.columns([1, 1])
        with col_refresh2:
            if st.button("Atualizar sugestões", key=chave(aluno, "refresh_sugestoes_exerc"), use_container_width=True):
                user_text = st.session_state.get(chave(aluno, "prompt_exerc"), "")
                with st.spinner("Gerando novas sugestões adaptadas..."):
                    st.session_state[sugestoes_key_exerc] = gerar_sugestoes_ia(contexto, model, provider, "exercicios", user_text)
                st.rerun()
        with col_usar2:
            if sugestao_selecionada_exerc != "-- Digite seu próprio tema --":
                if st.button("Usar esta sugestão", key=chave(aluno, "usar_sugestao_exerc"), type="secondary", use_container_width=True):
                    st.session_state[chave(aluno, "prompt_exerc")] = sugestao_selecionada_exerc
                    st.rerun()
        
        col_qtd, col_tipo = st.columns([1, 2])
        with col_qtd:
            num_exercicios = st.number_input(
                "Quantidade de exercícios:",
                min_value=1,
                max_value=50,
                value=10,
                step=1,
                key=chave(aluno, "num_exercicios"),
            )
        with col_tipo:
            tipo_exercicio = st.selectbox(
                "Tipo de exercício:",
                ["Múltipla escolha (A-E) padrão Colégio Militar", "Verdadeiro/Falso", "Dissertativos", "Misto"],
                key=chave(aluno, "tipo_exercicio"),
            )

        user_prompt_exerc = st.text_area(
            "Tema ou instrução específica (as sugestões acima se adaptam ao que você escrever aqui):",
            key=chave(aluno, "prompt_exerc"),
            height=120,
            placeholder="Ex: 20 exercícios de múltipla escolha sobre frações e interpretação de texto para o 6º ano, estilo Colégio Militar de Manaus...",
        )

        prompt_final = f"{user_prompt_exerc}. Gere exatamente {num_exercicios} exercícios do tipo: {tipo_exercicio}. Cada questão de múltipla escolha deve ter EXATAMENTE 5 alternativas (A) até (E). Indique o gabarito ao final de cada questão."

        if st.button("Gerar Exercícios", key=chave(aluno, "btn_exerc"), type="primary", use_container_width=True):
            if not user_prompt_exerc.strip():
                st.warning("Digite um tema ou instrução.")
            else:
                with st.spinner(f"Gerando {num_exercicios} exercícios..."):
                    resultado = generate_exercises(contexto, prompt_final, model, provider=provider)
                if resultado:
                    st.session_state[chave(aluno, "exercicios")] = resultado
                    st.session_state.pop(chave(aluno, "plano"), None)
                    st.rerun()
                else:
                    st.error("A IA não retornou conteúdo.")

    if chave(aluno, "plano") in st.session_state:
        _bloco_resultado(aluno, "plano", "Plano de Aula", "Plano", "plano_aula")
    elif chave(aluno, "exercicios") in st.session_state:
        _bloco_resultado(aluno, "exercicios", "Lista de Exercícios", "Exercícios", "exercicios")