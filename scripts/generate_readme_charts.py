#!/usr/bin/env python3
"""
Gera gráficos de exemplo para o README demonstrando as capacidades do Edu Assistant
sem usar dados reais de alunos.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os
from pathlib import Path

# Configuração de estilo
plt.style.use('seaborn-v0_8-whitegrid')
COLORS = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E']

output_dir = Path("docs/assets")
output_dir.mkdir(parents=True, exist_ok=True)

# 1. Gráfico: Tipos de arquivo suportados
def grafico_formatos_suportados():
    formatos = ['PDF', 'PPTX', 'DOCX', 'TXT/MD', 'CSV/JSON', 'HTML', 'Imagens']
    arquivos = [180, 45, 30, 120, 25, 15, 60]
    
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(formatos, arquivos, color=COLORS[:7], edgecolor='white', linewidth=1.5)
    ax.set_xlabel('Arquivos processados (exemplo)', fontsize=11)
    ax.set_title('Formatos Suportados e Volume Típico de Processamento', fontsize=13, fontweight='bold', pad=15)
    
    for bar, val in zip(bars, arquivos):
        ax.text(bar.get_width() + 3, bar.get_y() + bar.get_height()/2, 
                f'{val}', va='center', fontsize=10, fontweight='bold')
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig(output_dir / 'formatos_suportados.png', dpi=150, bbox_inches='tight')
    plt.close()

# 2. Gráfico: Pipeline de extração
def grafico_pipeline_extracao():
    etapas = ['Upload', 'Cache\nCheck', 'Texto\nNativo', 'OCR\nParalelo', 'OCR.space\nFallback', 'Visão\nLLM', 'Refino\nLLM', 'Cache\nSalvar']
    tempo = [0.1, 0.05, 0.3, 2.5, 3.0, 8.0, 15.0, 0.2]
    cores = ['#2E86AB'] * 2 + ['#6A994E'] + ['#F18F01'] * 2 + ['#A23B72'] * 2 + ['#C73E1D']
    
    fig, ax = plt.subplots(figsize=(12, 4))
    bars = ax.bar(etapas, tempo, color=cores, edgecolor='white', linewidth=1.5)
    ax.set_ylabel('Tempo médio (segundos)', fontsize=11)
    ax.set_title('Pipeline de Extração Inteligente — Cache + Fallbacks Progressivos', fontsize=13, fontweight='bold', pad=15)
    ax.set_yscale('log')
    
    for bar, val in zip(bars, tempo):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.3, 
                f'{val}s', ha='center', fontsize=9, fontweight='bold')
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig(output_dir / 'pipeline_extracao.png', dpi=150, bbox_inches='tight')
    plt.close()

# 3. Gráfico: Rotação de chaves e failover
def grafico_rotacao_chaves():
    chaves = [f'Chave {i+1}' for i in range(7)]
    requisicoes = [145, 132, 156, 98, 167, 123, 89]
    erros_429 = [3, 5, 2, 8, 1, 4, 6]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    
    # Requisições por chave
    bars1 = ax1.bar(chaves, requisicoes, color=COLORS[0], edgecolor='white', linewidth=1)
    ax1.set_ylabel('Requisições bem-sucedidas', fontsize=10)
    ax1.set_title('Distribuição de Requisições (Round-Robin)', fontsize=11, fontweight='bold')
    ax1.tick_params(axis='x', rotation=45)
    
    # Erros 429 e failover
    bars2 = ax2.bar(chaves, erros_429, color=COLORS[3], edgecolor='white', linewidth=1)
    ax2.set_ylabel('Erros 429 (quota)', fontsize=10)
    ax2.set_title('Failover Automático por Chave', fontsize=11, fontweight='bold')
    ax2.tick_params(axis='x', rotation=45)
    
    for bars, vals in [(bars1, requisicoes), (bars2, erros_429)]:
        for bar, val in zip(bars, vals):
            if val > 0:
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, 
                         str(val), ha='center', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'rotacao_chaves.png', dpi=150, bbox_inches='tight')
    plt.close()

# 4. Gráfico: BM25 - Relevância do contexto
def grafico_bm25_relevancia():
    np.random.seed(42)
    consultas = ['Frações 6º ano', 'Interpretação texto', 'Geometria área', 'Problemas lógica', 'Gramática classes']
    relevancia = np.random.uniform(0.72, 0.96, len(consultas))
    chars_usados = np.random.randint(8000, 25000, len(consultas))
    
    fig, ax = plt.subplots(figsize=(10, 5))
    scatter = ax.scatter(chars_usados, relevancia, s=200, c=COLORS, alpha=0.8, edgecolors='white', linewidth=2)
    
    for i, consulta in enumerate(consultas):
        ax.annotate(consulta, (chars_usados[i], relevancia[i]), 
                    xytext=(5, 5), textcoords='offset points', fontsize=9, fontweight='bold')
    
    ax.set_xlabel('Caracteres do contexto selecionado', fontsize=11)
    ax.set_ylabel('Score de relevância BM25', fontsize=11)
    ax.set_title('Busca BM25: Contexto Relevante vs. Tamanho do Prompt', fontsize=13, fontweight='bold', pad=15)
    ax.set_ylim(0.65, 1.0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig(output_dir / 'bm25_relevancia.png', dpi=150, bbox_inches='tight')
    plt.close()

# 5. Gráfico: Tipos de saída gerados
def grafico_tipos_saida():
    categorias = ['Planos de Aula', 'Exercícios Múltipla Escolha (A-E)', 'Simulados Completos', 'Listas de Revisão', 'Redações']
    quantidade = [42, 156, 18, 67, 23]
    formatos = ['TXT', 'DOCX', 'PDF']
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Pizza - tipos de conteúdo
    ax1 = axes[0]
    wedges, texts, autotexts = ax1.pie(quantidade, labels=categorias, autopct='%1.0f%%',
                                        colors=COLORS, startangle=90, textprops={'fontsize': 9})
    ax1.set_title('Tipos de Conteúdo Gerado', fontsize=11, fontweight='bold')
    
    # Barras empilhadas - formatos de exportação
    ax2 = axes[1]
    formatos_dados = {
        'TXT': [35, 120, 15, 55, 18],
        'DOCX': [28, 95, 12, 42, 14],
        'PDF': [22, 88, 10, 35, 11]
    }
    bottom = np.zeros(len(categorias))
    for fmt, vals in formatos_dados.items():
        ax2.bar(categorias, vals, bottom=bottom, label=fmt, color={'TXT': COLORS[0], 'DOCX': COLORS[1], 'PDF': COLORS[2]}[fmt])
        bottom += np.array(vals)
    
    ax2.set_ylabel('Downloads', fontsize=10)
    ax2.set_title('Exportações por Formato', fontsize=11, fontweight='bold')
    ax2.legend(title='Formato')
    ax2.tick_params(axis='x', rotation=30)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'tipos_saida.png', dpi=150, bbox_inches='tight')
    plt.close()

# 6. Gráfico: Comparativo de modelos gratuitos
def grafico_modelos_gratuitos():
    modelos = ['gemma4:31b', 'gpt-oss:120b', 'gpt-oss:20b', 'nemotron-3-ultra', 
               'llama3.1:70b', 'qwen2.5:72b', 'phi3.5:7b', 'mistral-nemo:12b']
    contexto = [32768, 131072, 131072, 131072, 131072, 131072, 16384, 131072]
    velocidade = [85, 45, 72, 38, 52, 48, 95, 68]  # tokens/s relativo
    
    fig, ax1 = plt.subplots(figsize=(11, 5))
    
    x = np.arange(len(modelos))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, [c/1000 for c in contexto], width, 
                    label='Contexto (k tokens)', color=COLORS[0], edgecolor='white')
    ax2 = ax1.twinx()
    bars2 = ax2.bar(x + width/2, velocidade, width,
                    label='Velocidade (tokens/s)', color=COLORS[1], edgecolor='white')
    
    ax1.set_xticks(x)
    ax1.set_xticklabels(modelos, rotation=45, ha='right', fontsize=9)
    ax1.set_ylabel('Janela de Contexto (k tokens)', fontsize=10, color=COLORS[0])
    ax2.set_ylabel('Velocidade Relativa (tokens/s)', fontsize=10, color=COLORS[1])
    ax1.set_title('Modelos Gratuitos Ollama Cloud — Contexto vs Velocidade', fontsize=13, fontweight='bold', pad=15)
    
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'modelos_gratuitos.png', dpi=150, bbox_inches='tight')
    plt.close()

# 7. Dashboard resumo
def grafico_dashboard_resumo():
    fig = plt.figure(figsize=(14, 8))
    gs = fig.add_gridspec(3, 3, hspace=0.35, wspace=0.25)
    
    # KPI cards - apenas 3 colunas no grid, então 3 KPIs
    kpis = [
        ('Alunos Ativos', '12', '+3 este mês', COLORS[0]),
        ('Arquivos Processados', '2.847', '+412 esta semana', COLORS[1]),
        ('Tokens Economizados', '4.2M', 'via cache + BM25', COLORS[2]),
    ]
    
    for i, (titulo, valor, subtitulo, cor) in enumerate(kpis):
        ax = fig.add_subplot(gs[0, i])
        ax.text(0.5, 0.65, valor, ha='center', va='center', fontsize=32, fontweight='bold', color=cor)
        ax.text(0.5, 0.35, titulo, ha='center', va='center', fontsize=11, color='#333')
        ax.text(0.5, 0.12, subtitulo, ha='center', va='center', fontsize=9, color='#666')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        # Borda colorida
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_color(cor)
            spine.set_linewidth(3)
    
    # Mini gráfico - evolução semanal
    ax5 = fig.add_subplot(gs[1:, 0])
    semanas = ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4']
    uploads = [45, 52, 38, 67]
    extracoes = [42, 48, 35, 61]
    ax5.plot(semanas, uploads, 'o-', label='Uploads', color=COLORS[0], linewidth=2)
    ax5.plot(semanas, extracoes, 's-', label='Extrações', color=COLORS[1], linewidth=2)
    ax5.fill_between(semanas, uploads, alpha=0.2, color=COLORS[0])
    ax5.fill_between(semanas, extracoes, alpha=0.2, color=COLORS[1])
    ax5.set_title('Atividade Semanal', fontsize=11, fontweight='bold')
    ax5.legend(fontsize=9)
    ax5.spines['top'].set_visible(False)
    ax5.spines['right'].set_visible(False)
    
    # Mini gráfico - cache hit rate
    ax6 = fig.add_subplot(gs[1:, 1])
    dias = list(range(1, 15))
    hit_rate = [0.12, 0.23, 0.31, 0.45, 0.52, 0.58, 0.63, 0.67, 0.71, 0.74, 0.76, 0.78, 0.79, 0.81]
    ax6.plot(dias, hit_rate, 'o-', color=COLORS[2], linewidth=2, markersize=4)
    ax6.fill_between(dias, hit_rate, alpha=0.2, color=COLORS[2])
    ax6.axhline(y=0.8, color='gray', linestyle='--', alpha=0.5, label='Meta 80%')
    ax6.set_ylim(0, 1)
    ax6.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax6.set_yticklabels(['0%', '20%', '40%', '60%', '80%', '100%'])
    ax6.set_title('Taxa de Cache Hit (acúmulo)', fontsize=11, fontweight='bold')
    ax6.legend(fontsize=9)
    ax6.spines['top'].set_visible(False)
    ax6.spines['right'].set_visible(False)
    
    # Mini gráfico - distribuição de tamanho de contexto
    ax7 = fig.add_subplot(gs[1:, 2])
    tamanhos = np.random.lognormal(9, 0.8, 500)
    tamanhos = tamanhos[tamanhos < 50000]
    ax7.hist(tamanhos, bins=30, color=COLORS[4], alpha=0.7, edgecolor='white')
    ax7.axvline(x=np.median(tamanhos), color='red', linestyle='--', linewidth=2, label=f'Mediana: {int(np.median(tamanhos)):,}')
    ax7.axvline(x=50000, color='orange', linestyle='--', linewidth=2, label='Limite: 50k')
    ax7.set_xlabel('Caracteres', fontsize=10)
    ax7.set_ylabel('Frequência', fontsize=10)
    ax7.set_title('Distribuição Tamanho do Contexto', fontsize=11, fontweight='bold')
    ax7.legend(fontsize=9)
    ax7.spines['top'].set_visible(False)
    ax7.spines['right'].set_visible(False)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'dashboard_resumo.png', dpi=150, bbox_inches='tight')
    plt.close()

if __name__ == '__main__':
    print("Gerando gráficos para README...")
    grafico_formatos_suportados()
    print("  ✓ formatos_suportados.png")
    grafico_pipeline_extracao()
    print("  ✓ pipeline_extracao.png")
    grafico_rotacao_chaves()
    print("  ✓ rotacao_chaves.png")
    grafico_bm25_relevancia()
    print("  ✓ bm25_relevancia.png")
    grafico_tipos_saida()
    print("  ✓ tipos_saida.png")
    grafico_modelos_gratuitos()
    print("  ✓ modelos_gratuitos.png")
    grafico_dashboard_resumo()
    print("  ✓ dashboard_resumo.png")
    print(f"\nTodos salvos em {output_dir}/")