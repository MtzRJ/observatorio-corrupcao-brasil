"""
╔══════════════════════════════════════════════════════════════╗
║     OBSERVATÓRIO DA CORRUPÇÃO BRASILEIRA — Streamlit App    ║
║     Arquivo principal: painel_corrupcao.py                  ║
║                                                              ║
║     Para rodar localmente:                                   ║
║       pip install streamlit pandas plotly sqlite3            ║
║       streamlit run painel_corrupcao.py                      ║
║                                                              ║
║     Para publicar (gratuito):                                ║
║       1. Suba para GitHub                                    ║
║       2. Acesse share.streamlit.io                           ║
║       3. Conecte o repositório → Deploy                      ║
╚══════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json
from datetime import datetime
import hashlib

ANO_MAX = datetime.now().year + 1
ANO_MIN = 1985

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Observatório da Corrupção BR",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/seu-usuario/corrupcao-brasil",
        "Report a bug": "https://github.com/seu-usuario/corrupcao-brasil/issues",
        "About": "Banco de dados educacional sobre corrupção no Brasil (1988–presente). Fontes: MPF, STF, TCU, Portal da Transparência, PF."
    }
)

# ── CSS customizado ───────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Inter:wght@300;400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    h1, h2, h3, .metric-label {
        font-family: 'Syne', sans-serif !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f1923 0%, #1a2940 100%);
    }
    section[data-testid="stSidebar"] * {
        color: #e0e8f0 !important;
    }

    /* Cards de métricas */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a2940 0%, #0f1923 100%);
        border: 1px solid #2e4a6e;
        border-radius: 12px;
        padding: 16px 20px;
        border-left: 4px solid #e8b84b;
    }
    [data-testid="stMetricValue"] {
        font-family: 'Syne', sans-serif !important;
        color: #e8b84b !important;
        font-size: 1.8rem !important;
    }
    [data-testid="stMetricLabel"] {
        color: #8ba3c0 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    /* Cabeçalho principal */
    .main-header {
        background: linear-gradient(135deg, #0f1923 0%, #1a2940 50%, #0f2535 100%);
        border-bottom: 3px solid #e8b84b;
        padding: 24px 32px;
        margin: -24px -24px 32px -24px;
        border-radius: 0 0 16px 16px;
    }
    .main-title {
        font-family: 'Syne', sans-serif;
        font-size: 2.2rem;
        font-weight: 800;
        color: #ffffff;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .main-subtitle {
        color: #8ba3c0;
        font-size: 0.9rem;
        margin-top: 6px;
        font-weight: 300;
    }
    .badge {
        display: inline-block;
        background: #e8b84b22;
        border: 1px solid #e8b84b55;
        color: #e8b84b;
        font-size: 0.7rem;
        padding: 2px 10px;
        border-radius: 20px;
        font-weight: 600;
        letter-spacing: 0.05em;
        margin-right: 6px;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 2px solid #1a2940;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px 8px 0 0;
        color: #8ba3c0;
        font-family: 'Syne', sans-serif;
        font-weight: 600;
        font-size: 0.85rem;
        padding: 8px 20px;
    }
    .stTabs [aria-selected="true"] {
        background: #1a2940 !important;
        color: #e8b84b !important;
        border-bottom: 3px solid #e8b84b;
    }

    /* Info boxes */
    .info-box {
        background: #0f2535;
        border-left: 4px solid #2e7ab8;
        border-radius: 8px;
        padding: 16px 20px;
        margin: 12px 0;
        font-size: 0.9rem;
        color: #c5d8ea;
    }
    .warn-box {
        background: #1f1a0f;
        border-left: 4px solid #e8b84b;
        border-radius: 8px;
        padding: 16px 20px;
        margin: 12px 0;
        font-size: 0.9rem;
        color: #e0d0a0;
    }
    .danger-box {
        background: #1f0f0f;
        border-left: 4px solid #c0392b;
        border-radius: 8px;
        padding: 16px 20px;
        margin: 12px 0;
        font-size: 0.9rem;
        color: #e0a0a0;
    }

    /* Tabela */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }

    /* Botões */
    .stButton > button {
        background: linear-gradient(135deg, #2e7ab8, #1a5a8a);
        color: white;
        border: none;
        border-radius: 8px;
        font-family: 'Syne', sans-serif;
        font-weight: 600;
        padding: 8px 20px;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #e8b84b, #c9920a);
        color: #0f1923;
        transform: translateY(-1px);
    }

    /* Divider estilizado */
    hr {
        border: none;
        border-top: 1px solid #1a2940;
        margin: 24px 0;
    }
</style>
""", unsafe_allow_html=True)


# ── Conexão com banco ─────────────────────────────────────────────────────────
# __file__ garante que o caminho funciona no Streamlit Cloud e localmente
_BASE_DIR = Path(__file__).parent.resolve()

@st.cache_resource
def get_connection():
    candidatos = [
        _BASE_DIR / "corrupcao_brasil.db",
        Path("corrupcao_brasil.db").resolve(),
        Path("/mount/src") / "corrupcao_brasil.db",
    ]
    # Busca recursiva na pasta do script (cobre subpastas)
    try:
        for extra in _BASE_DIR.rglob("corrupcao_brasil.db"):
            candidatos.append(extra)
    except Exception:
        pass

    db_path = next((c for c in candidatos if c.exists()), None)

    if db_path is None:
        arquivos = ", ".join(p.name for p in _BASE_DIR.iterdir()) if _BASE_DIR.exists() else "pasta não encontrada"
        st.error("❌ Banco de dados não encontrado. Verifique se `corrupcao_brasil.db` foi enviado para o GitHub na mesma pasta que `painel_corrupcao.py`.")
        st.info(f"📂 Pasta do script: `{_BASE_DIR}`  |  Arquivos: `{arquivos}`")
        st.stop()

    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

@st.cache_data(ttl=3600)
def query(_conn, sql, params=()):
    return pd.read_sql_query(sql, _conn, params=params)


conn = get_connection()

# ── Dados carregados ──────────────────────────────────────────────────────────
df_casos    = query(conn, "SELECT * FROM casos ORDER BY valor_reais DESC NULLS LAST")
df_pessoas  = query(conn, "SELECT * FROM pessoas ORDER BY nome")
df_empresas = query(conn, "SELECT * FROM empresas")
df_partidos = query(conn, "SELECT * FROM partidos")
df_ops      = query(conn, "SELECT * FROM operacoes")

# views
df_resumo   = query(conn, "SELECT * FROM v_casos_resumo")
df_rede     = query(conn, "SELECT * FROM v_rede_relacionamentos")
df_part_rank= query(conn, "SELECT * FROM v_partidos_escandalo ORDER BY total_politicos_investigados DESC")


# ══════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("### 🔍 Observatório da Corrupção Brasileira")
    st.markdown("---")

    st.markdown("**Navegação**")
    pagina = st.radio("", [
        "🏠 Visão Geral",
        "📋 Casos",
        "👤 Pessoas",
        "🏢 Empresas",
        "🎯 Partidos",
        "🔗 Rede de Relacionamentos",
        "✏️ Contribuir com dados",
        "📚 Sobre & Como Usar",
    ], label_visibility="collapsed")

    st.markdown("---")

    st.markdown("**Filtros**")
    anos = st.slider("Período", 1988, ANO_MAX, (1988, ANO_MAX))
    tipos_pessoa = st.multiselect(
        "Tipo de envolvido",
        ["politico", "empresario", "operador", "laranja", "doleiro", "servidor", "outro"],
        default=["politico", "empresario", "operador", "laranja", "doleiro", "servidor", "outro"]
    )

    st.markdown("---")
    st.markdown("""
    <div style="font-size:0.72rem; color:#5a7a9a; line-height:1.6">
    📊 Fontes: MPF, STF, TCU, CGU, PF<br>
    🗓️ Atualização: contínua<br>
    ⚖️ Uso educacional e de pesquisa<br><br>
    <strong style="color:#e8b84b">⚠️ Dados públicos — sem fins comerciais</strong>
    </div>
    """, unsafe_allow_html=True)


# ── Filtrar por anos ──────────────────────────────────────────────────────────
df_casos_f = df_casos[
    (df_casos["ano_inicio"] >= anos[0]) &
    (df_casos["ano_inicio"] <= anos[1])
]
df_pessoas_f = df_pessoas[df_pessoas["tipo"].isin(tipos_pessoa)]


# ══════════════════════════════════════════════════════════════
#  CABEÇALHO
# ══════════════════════════════════════════════════════════════

st.markdown("""
<div class="main-header">
  <p class="main-title">🔍 Observatório da Corrupção Brasileira</p>
  <p class="main-subtitle">
    Banco de dados educacional e de código aberto · 1988–presente · Fontes: MPF, STF, TCU, CGU, PF
  </p>
  <div style="margin-top:10px">
    <span class="badge">ESTUDO</span>
    <span class="badge">DADOS ABERTOS</span>
    <span class="badge">OPEN SOURCE</span>
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  PÁGINA 1 — VISÃO GERAL
# ══════════════════════════════════════════════════════════════

if pagina == "🏠 Visão Geral":

    # KPIs
    col1, col2, col3, col4, col5 = st.columns(5)
    total_valor = df_casos_f["valor_reais"].sum()
    with col1:
        st.metric("💰 Total estimado", f"R$ {total_valor/1e9:.0f} bi")
    with col2:
        st.metric("📁 Escândalos registrados", f"{len(df_casos_f)}")
    with col3:
        st.metric("👤 Pessoas investigadas", f"{len(df_pessoas_f)}")
    with col4:
        cond = df_pessoas_f["situacao_legal"].str.contains("Condenado", na=False).sum()
        st.metric("⚖️ Condenados(as)", f"{cond}")
    with col5:
        st.metric("🏢 Empresas", f"{len(df_empresas)}")

    st.markdown("<br>", unsafe_allow_html=True)

    col_a, col_b = st.columns([3, 2])

    with col_a:
        st.markdown("#### 📊 Maiores escândalos por valor estimado (R$)")
        df_plot = df_casos_f.dropna(subset=["valor_reais"]).nlargest(10, "valor_reais")
        fig = px.bar(
            df_plot,
            x="valor_reais",
            y="nome",
            orientation="h",
            color="valor_reais",
            color_continuous_scale=["#1a5a8a", "#2e7ab8", "#e8b84b", "#c0392b"],
            labels={"valor_reais": "Valor Estimado (R$)", "nome": ""},
            text=df_plot["valor_reais"].apply(lambda v: f"R$ {v/1e9:.1f}bi" if v >= 1e9 else f"R$ {v/1e6:.0f}mi")
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#c5d8ea", family="Inter"),
            showlegend=False,
            coloraxis_showscale=False,
            yaxis=dict(categoryorder="total ascending"),
            height=420,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        fig.update_traces(textposition="outside", textfont=dict(color="#e8b84b", size=11))
        fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)
        fig.update_yaxes(showgrid=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown("#### 🕐 Linha do tempo")
        df_timeline = df_casos_f.dropna(subset=["valor_reais", "ano_inicio"]).copy()
        df_timeline["valor_bi"] = df_timeline["valor_reais"] / 1e9
        fig2 = px.scatter(
            df_timeline,
            x="ano_inicio",
            y="valor_bi",
            size="valor_bi",
            color="valor_bi",
            hover_name="nome",
            color_continuous_scale=["#1a5a8a", "#e8b84b", "#c0392b"],
            labels={"ano_inicio": "Ano", "valor_bi": "Valor (R$ bi)"},
            size_max=50
        )
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15,25,35,0.5)",
            font=dict(color="#c5d8ea", family="Inter"),
            coloraxis_showscale=False,
            height=420,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        fig2.update_xaxes(showgrid=True, gridcolor="#1a2940", zeroline=False)
        fig2.update_yaxes(showgrid=True, gridcolor="#1a2940")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    col_c, col_d = st.columns(2)
    with col_c:
        st.markdown("#### 🎯 Partidos com mais investigados")
        df_pp = df_part_rank[df_part_rank["total_politicos_investigados"] > 0].head(8)
        fig3 = px.bar(
            df_pp,
            x="sigla",
            y="total_politicos_investigados",
            color="espectro",
            color_discrete_map={
                "esquerda": "#c0392b",
                "centro-esquerda": "#e67e22",
                "centro": "#8ba3c0",
                "centro-direita": "#2e7ab8",
                "direita": "#1a2940",
                "catch-all": "#e8b84b"
            },
            labels={"sigla": "Partido político", "total_politicos_investigados": "Investigados"},
        )
        fig3.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#c5d8ea"),
            showlegend=True,
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
            height=300,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        fig3.update_xaxes(showgrid=False)
        fig3.update_yaxes(showgrid=True, gridcolor="#1a2940")
        st.plotly_chart(fig3, use_container_width=True)

    with col_d:
        st.markdown("#### ⚖️ Situação legal dos investigados")
        df_sit = df_pessoas_f["situacao_legal"].value_counts().reset_index()
        df_sit.columns = ["situacao", "total"]
        df_sit["situacao_curta"] = df_sit["situacao"].str[:30]
        fig4 = px.pie(
            df_sit.head(8),
            names="situacao_curta",
            values="total",
            color_discrete_sequence=["#c0392b", "#e8b84b", "#2e7ab8", "#27ae60", "#8ba3c0", "#e67e22", "#9b59b6", "#1abc9c"]
        )
        fig4.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#c5d8ea"),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
            height=300,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        fig4.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("""
    <div class="warn-box">
    ⚠️ <strong>Nota metodológica:</strong> Os valores são estimativas baseadas em relatórios do MPF, TCU, COAF e acordos de colaboração premiada. Processos em andamento podem ter novos desdobramentos. Este banco tem caráter educacional e não substitui a consulta às fontes primárias.
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  PÁGINA 2 — CASOS
# ══════════════════════════════════════════════════════════════

elif pagina == "📋 Casos":
    st.markdown("## 📋 Casos de corrupção")

    busca = st.text_input("🔎 Buscar por nome do escândalo ou órgão público", placeholder="Ex: Lava Jato, Petrobras, Mensalão...")
    col_ord1, col_ord2 = st.columns([2, 1])
    with col_ord1:
        ordenar = st.selectbox("Ordenar por:", ["Valor (maior primeiro)", "Valor (menor primeiro)", "Ano (mais recente primeiro)", "Ano (mais antigo primeiro)"])

    df_show = df_casos_f.copy()
    if busca:
        mask = (
            df_show["nome"].str.contains(busca, case=False, na=False) |
            df_show["orgao_alvo"].str.contains(busca, case=False, na=False) |
            df_show["descricao"].str.contains(busca, case=False, na=False)
        )
        df_show = df_show[mask]

    order_map = {
        "Valor (maior)": ("valor_reais", False),
        "Valor (menor)": ("valor_reais", True),
        "Ano (mais recente)": ("ano_inicio", False),
        "Ano (mais antigo)": ("ano_inicio", True),
    }
    col_sort, asc_sort = order_map[ordenar]
    df_show = df_show.sort_values(col_sort, ascending=asc_sort, na_position="last")

    st.markdown(f"**{len(df_show)} caso(s) encontrado(s)**")
    st.markdown("<br>", unsafe_allow_html=True)

    for _, row in df_show.iterrows():
        valor_fmt = f"R$ {row['valor_reais']/1e9:.1f} bilhões" if pd.notna(row['valor_reais']) and row['valor_reais'] >= 1e9 else (f"R$ {row['valor_reais']/1e6:.0f} milhões" if pd.notna(row['valor_reais']) else "Não estimado")
        periodo = f"{int(row['ano_inicio'])}–{int(row['ano_fim']) if pd.notna(row['ano_fim']) else 'atual'}"

        with st.expander(f"**{row['nome']}** · {periodo} · {valor_fmt}"):
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"**Período:** {periodo}")
            c2.markdown(f"**Valor estimado:** {valor_fmt}")
            c3.markdown(f"**Operação:** {row['operacao_pf'] or '—'}")
            st.markdown(f"**Órgão alvo:** {row['orgao_alvo'] or '—'}")
            st.markdown(f"**Descrição:** {row['descricao'] or '—'}")
            st.markdown(f"**Status judicial:** {row['status_judicial'] or '—'}")
            st.markdown(f"**Condenações:** {row['condenacoes'] or '—'}")
            if row['fontes']:
                st.markdown(f"*Fontes: {row['fontes']}*")

            # Envolvidos neste caso
            df_env = query(conn, """
                SELECT p.nome, p.tipo, p.cargo, cp.papel, p.situacao_legal
                FROM caso_pessoa cp
                JOIN pessoas p ON p.id = cp.pessoa_id
                WHERE cp.caso_id = ?
            """, (int(row['id']),))
            if not df_env.empty:
                st.markdown("**Pessoas envolvidas no caso:**")
                st.dataframe(df_env, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════
#  PÁGINA 3 — PESSOAS
# ══════════════════════════════════════════════════════════════

elif pagina == "👤 Pessoas":
    st.markdown("## 👤 Pessoas investigadas")

    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        busca_p = st.text_input("🔎 Buscar por nome", placeholder="Ex: Lula, Temer, Cunha...")
    with col_p2:
        tipo_filtro = st.multiselect("Tipo de envolvido", df_pessoas["tipo"].unique().tolist(), default=df_pessoas["tipo"].unique().tolist())
    with col_p3:
        partido_filtro = st.text_input("Partido político (se aplicável)", placeholder="Ex: PT, PMDB...")

    df_p = df_pessoas.copy()
    if busca_p:
        df_p = df_p[df_p["nome"].str.contains(busca_p, case=False, na=False)]
    if tipo_filtro:
        df_p = df_p[df_p["tipo"].isin(tipo_filtro)]
    if partido_filtro:
        df_p = df_p[df_p["partido"].str.contains(partido_filtro, case=False, na=False)]

    st.markdown(f"**{len(df_p)} pessoa(s) encontrada(s)**")

    for _, row in df_p.iterrows():
        icon_map = {"politico": "🏛️", "empresario": "💼", "operador": "🔧", "laranja": "🧩", "doleiro": "💱", "servidor": "📋", "outro": "👤"}
        icon = icon_map.get(row["tipo"], "👤")

        with st.expander(f"{icon} **{row['nome']}** · {row['tipo']} · {row['partido'] or '—'}"):
            c1, c2 = st.columns(2)
            c1.markdown(f"**Cargo:** {row['cargo'] or '—'}")
            c1.markdown(f"**Partido:** {row['partido'] or '—'}")
            c1.markdown(f"**Estado:** {row['estado'] or '—'}")
            c2.markdown(f"**Situação legal:** {row['situacao_legal'] or '—'}")
            c2.markdown(f"**Pena:** {row['pena'] or '—'}")
            if row["observacoes"]:
                st.markdown(f"*{row['observacoes']}*")

            # Casos desta pessoa
            df_casos_p = query(conn, """
                SELECT c.nome AS caso, cp.papel, c.status_judicial
                FROM caso_pessoa cp
                JOIN casos c ON c.id = cp.caso_id
                WHERE cp.pessoa_id = ?
            """, (int(row["id"]),))
            if not df_casos_p.empty:
                st.markdown("**Casos em que está envolvido:**")
                st.dataframe(df_casos_p, use_container_width=True, hide_index=True)

            # Relacionamentos
            df_rel_p = query(conn, """
                SELECT pa.nome AS de, r.tipo AS relacao, pb.nome AS para, c.nome AS caso
                FROM relacionamentos r
                JOIN pessoas pa ON pa.id = r.pessoa_a
                JOIN pessoas pb ON pb.id = r.pessoa_b
                LEFT JOIN casos c ON c.id = r.caso_id
                WHERE r.pessoa_a = ? OR r.pessoa_b = ?
            """, (int(row["id"]), int(row["id"])))
            if not df_rel_p.empty:
                st.markdown("**Relacionamentos documentados:**")
                st.dataframe(df_rel_p, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════
#  PÁGINA 4 — EMPRESAS
# ══════════════════════════════════════════════════════════════

elif pagina == "🏢 Empresas":
    st.markdown("## 🏢 Empresas investigadas")

    busca_e = st.text_input("🔎 Buscar empresa", placeholder="Ex: Odebrecht, JBS, Petrobras...")
    tipo_e  = st.multiselect("Tipo de empresa", df_empresas["tipo"].unique().tolist(), default=df_empresas["tipo"].unique().tolist())

    df_e = df_empresas.copy()
    if busca_e:
        df_e = df_e[df_e["razao_social"].str.contains(busca_e, case=False, na=False)]
    if tipo_e:
        df_e = df_e[df_e["tipo"].isin(tipo_e)]

    tipo_icons = {"empreiteira": "🏗️", "fachada": "🎭", "offshore": "🌐", "banco": "🏦", "outra": "🏢"}

    for _, row in df_e.iterrows():
        icon = tipo_icons.get(row["tipo"], "🏢")
        with st.expander(f"{icon} **{row['razao_social']}** · {row['tipo']} · {row['pais']}"):
            c1, c2 = st.columns(2)
            c1.markdown(f"**Tipo:** {row['tipo']}")
            c1.markdown(f"**Sede:** {row['sede'] or '—'} / {row['pais']}")
            c2.markdown(f"**Status:** {row['status'] or '—'}")
            if row["observacoes"]:
                st.markdown(f"*{row['observacoes']}*")

            # Casos
            df_casos_e = query(conn, """
                SELECT c.nome AS caso, ce.papel, c.status_judicial
                FROM caso_empresa ce
                JOIN casos c ON c.id = ce.caso_id
                WHERE ce.empresa_id = ?
            """, (int(row["id"]),))
            if not df_casos_e.empty:
                st.markdown("**Envolvida nos seguintes casos:**")
                st.dataframe(df_casos_e, use_container_width=True, hide_index=True)

            # Sócios
            df_socios = query(conn, """
                SELECT p.nome, pe.vinculo, p.situacao_legal
                FROM pessoa_empresa pe
                JOIN pessoas p ON p.id = pe.pessoa_id
                WHERE pe.empresa_id = ?
            """, (int(row["id"]),))
            if not df_socios.empty:
                st.markdown("**Sócios e vínculos identificados:**")
                st.dataframe(df_socios, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════
#  PÁGINA 5 — PARTIDOS
# ══════════════════════════════════════════════════════════════

elif pagina == "🎯 Partidos":
    st.markdown("## 🎯 Partidos políticos")

    st.markdown("""
    <div class="warn-box">
    ⚠️ <strong>Importante:</strong> A presença de um partido neste banco reflete citações em investigações públicas, não a condenação do partido em si. Nenhum grande partido brasileiro está isento — a corrupção sistêmica está estruturalmente ligada ao modelo do presidencialismo de coalizão.
    </div>
    """, unsafe_allow_html=True)

    col_pa, col_pb = st.columns([2, 1])

    with col_pa:
        st.markdown("#### Distribuição por espectro ideológico × número de investigados")
        df_part_plot = df_part_rank[df_part_rank["total_politicos_investigados"] > 0].copy()
        cor_map = {
            "esquerda": "#c0392b",
            "centro-esquerda": "#e67e22",
            "centro": "#8ba3c0",
            "centro-direita": "#2e7ab8",
            "direita": "#1a2940",
            "catch-all": "#e8b84b"
        }
        fig_p = px.scatter(
            df_part_plot,
            x="espectro",
            y="total_politicos_investigados",
            size="total_politicos_investigados",
            color="espectro",
            text="sigla",
            color_discrete_map=cor_map,
            labels={"espectro": "Espectro", "total_politicos_investigados": "Investigados"},
            size_max=60,
        )
        fig_p.update_traces(textposition="top center")
        fig_p.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15,25,35,0.5)",
            font=dict(color="#c5d8ea"),
            showlegend=False,
            height=380,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="#1a2940"),
            margin=dict(l=10, r=10, t=20, b=10)
        )
        st.plotly_chart(fig_p, use_container_width=True)

    with col_pb:
        st.markdown("#### Ranking completo")
        st.dataframe(
            df_part_rank[["sigla", "espectro", "total_politicos_investigados"]].rename(columns={
                "sigla": "Partido",
                "espectro": "Espectro",
                "total_politicos_investigados": "Investigados"
            }),
            use_container_width=True,
            hide_index=True
        )

    st.markdown("---")
    st.markdown("#### 💡 Por que o PMDB/MDB aparece em tantos escândalos?")
    st.markdown("""
    <div class="info-box">
    O PMDB foi o <strong>partido-pivot</strong> de praticamente todos os governos desde 1985. 
    Governou com Collor, FHC, Lula, Dilma e ainda deu origem ao governo Temer. 
    Por não ter ideologia fixa, estava sempre no poder — e onde há poder, há incentivos à corrupção. 
    Não é coincidência: é estrutural.
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  PÁGINA 6 — REDE
# ══════════════════════════════════════════════════════════════

elif pagina == "🔗 Rede de Relacionamentos":
    st.markdown("## 🔗 Rede de relacionamentos")

    st.markdown("""
    <div class="info-box">
    💡 Esta seção mostra como as pessoas investigadas se conectam entre si: quem ordenou pagamentos, quem delatou, quem atuava como laranja. É a parte mais poderosa do banco para compreender a estrutura das redes de corrupção.
    </div>
    """, unsafe_allow_html=True)

    # Tabela de relacionamentos
    st.markdown("#### Todos os relacionamentos documentados")
    st.dataframe(df_rede, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Busca de rede individual
    st.markdown("#### 🔍 Explorar a rede de uma pessoa")
    nomes_lista = df_pessoas["nome"].sort_values().tolist()
    nome_sel = st.selectbox("Selecione uma pessoa para visualizar sua rede", nomes_lista)

    if nome_sel:
        pessoa_id = df_pessoas[df_pessoas["nome"] == nome_sel]["id"].values[0]
        df_rede_p = query(conn, """
            SELECT pa.nome AS de, r.tipo AS relacao, pb.nome AS para,
                   c.nome AS caso, r.descricao
            FROM relacionamentos r
            JOIN pessoas pa ON pa.id = r.pessoa_a
            JOIN pessoas pb ON pb.id = r.pessoa_b
            LEFT JOIN casos c ON c.id = r.caso_id
            WHERE r.pessoa_a = ? OR r.pessoa_b = ?
        """, (int(pessoa_id), int(pessoa_id)))

        if df_rede_p.empty:
            st.info(f"Nenhum relacionamento documentado para {nome_sel}. Contribua com novos dados pela aba 'Contribuir'.")
        else:
            st.dataframe(df_rede_p, use_container_width=True, hide_index=True)

            # Visualização simples de grafo
            st.markdown("#### Mapa visual de relacionamentos")
            nomes_rede = list(set(df_rede_p["de"].tolist() + df_rede_p["para"].tolist()))
            edges_x, edges_y = [], []
            import random
            pos = {n: (random.uniform(-1, 1), random.uniform(-1, 1)) for n in nomes_rede}

            fig_g = go.Figure()
            for _, row in df_rede_p.iterrows():
                x0, y0 = pos[row["de"]]
                x1, y1 = pos[row["para"]]
                fig_g.add_trace(go.Scatter(
                    x=[x0, x1, None], y=[y0, y1, None],
                    mode="lines",
                    line=dict(width=2, color="#2e7ab8"),
                    showlegend=False,
                    hoverinfo="skip"
                ))
            node_x = [pos[n][0] for n in nomes_rede]
            node_y = [pos[n][1] for n in nomes_rede]
            colors = ["#e8b84b" if n == nome_sel else "#2e7ab8" for n in nomes_rede]
            fig_g.add_trace(go.Scatter(
                x=node_x, y=node_y,
                mode="markers+text",
                marker=dict(size=20, color=colors),
                text=nomes_rede,
                textposition="top center",
                textfont=dict(size=10, color="#c5d8ea"),
                showlegend=False
            ))
            fig_g.update_layout(
                paper_bgcolor="rgba(15,25,35,1)",
                plot_bgcolor="rgba(15,25,35,1)",
                xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                height=400,
                margin=dict(l=20, r=20, t=20, b=20)
            )
            st.plotly_chart(fig_g, use_container_width=True)

    # Export JSON
    st.markdown("---")
    if st.button("📥 Exportar rede completa para análise externa (Gephi / D3.js)"):
        nodes = [{"id": int(r["id"]), "label": r["nome"], "group": r["tipo"]} for _, r in df_pessoas.iterrows()]
        rels_raw = query(conn, "SELECT * FROM relacionamentos")
        edges = [{"from": int(r["pessoa_a"]), "to": int(r["pessoa_b"]), "type": r["tipo"]} for _, r in rels_raw.iterrows()]
        grafo = {"nodes": nodes, "edges": edges}
        st.download_button("⬇️ Baixar rede (grafo.json)", json.dumps(grafo, ensure_ascii=False, indent=2), "grafo_corrupcao.json", "application/json")


# ══════════════════════════════════════════════════════════════
#  PÁGINA 7 — CONTRIBUIR COM DADOS
# ══════════════════════════════════════════════════════════════

elif pagina == "✏️ Contribuir com dados":
    # ─── Formulário público de contribuição ─────────────────────────────────
    if True:
        st.markdown("## 📝 Contribuir com o banco de dados")
        st.markdown("""
        <div class="info-box">
        💡 Qualquer pessoa pode sugerir novos dados — <strong>mas toda contribuição é revisada pelo administrador antes de entrar no banco.</strong> Inclua sempre a fonte: link de reportagem, número de processo judicial, relatório do TCU ou CGU etc. Contribuições sem fonte verificável serão rejeitadas.
        </div>
        """, unsafe_allow_html=True)

        tipo_contribuicao = st.selectbox("O que deseja contribuir?", [
            "🗂️ Novo caso ou escândalo",
            "👤 Nova pessoa investigada",
            "🔗 Novo relacionamento entre pessoas",
            "🏢 Nova empresa investigada",
        ])

        # ── IDENTIFICAÇÃO DO CONTRIBUIDOR ────────────────────────────────────
        with st.expander("👤 Sua identificação (opcional — facilita o contato durante a revisão)", expanded=False):
            col_id1, col_id2 = st.columns(2)
            contrib_nome  = col_id1.text_input("Nome (opcional)", placeholder="Ex: João Silva")
            contrib_email = col_id2.text_input("Seu e-mail", placeholder="E-mail para receber retorno")
            st.caption("Seus dados de identificação não são publicados — servem apenas para contato durante o processo de revisão.")

        st.markdown("---")

        # ── FORMULÁRIOS POR TIPO ─────────────────────────────────────────────
        dados_para_salvar = {}
        form_ok = False

        if "Novo caso" in tipo_contribuicao:
            with st.form("contrib_caso"):
                col1, col2 = st.columns(2)
                nome_c   = col1.text_input("Nome do escândalo ou operação *")
                apelido  = col2.text_input("Apelido ou nome popular")
                col3, col4, col5 = st.columns(3)
                ano_i  = col3.number_input("Ano de início *", ANO_MIN, ANO_MAX, datetime.now().year)
                ano_f  = col4.number_input("Ano de encerramento (deixe 0 se ainda em curso)", 0, ANO_MAX, 0)
                valor  = col5.number_input("Valor estimado desviado (R$)", 0.0, step=1_000_000.0)
                orgao  = st.text_input("Órgão público alvo do esquema")
                operac = st.text_input("Nome da operação policial (se houver)")
                desc   = st.text_area("Descrição do esquema *", height=120,
                                      placeholder="Descreva como o esquema funcionava, quem estava envolvido e quais recursos foram desviados.")
                status = st.selectbox("Situação judicial atual", [
                    "Em investigação","Denúncia oferecida","Ação penal em andamento",
                    "Parcialmente condenado","Condenados – 1ª instância",
                    "Condenados – trânsito em julgado","Arquivado","Prescrição"])

                st.markdown("#### 📎 Fonte da informação (obrigatório)")
                fonte_url  = st.text_input("URL da fonte (link da reportagem ou processo) *",
                    placeholder="Ex: https://www.mpf.mp.br/... ou https://g1.globo.com/...")
                fonte_desc = st.text_area("Descreva brevemente a fonte",
                    placeholder="Ex: Reportagem da Agência Pública publicada em 15/03/2025 — detalha o esquema de desvios.",
                    height=80)
                st.markdown("""
                <div class="warn-box" style="font-size:0.85rem">
                ⚠️ A contribuição <strong>não entra imediatamente no banco</strong> — ela passa por revisão manual. Contribuições sem URL verificável serão rejeitadas.
                </div>""", unsafe_allow_html=True)
                confirmado = st.checkbox("Confirmo que esta informação é de fonte pública e verificável *")
                enviado = st.form_submit_button("📨 Enviar contribuição para revisão", use_container_width=True)

                if enviado:
                    if not nome_c or not desc or not fonte_url or not confirmado:
                        st.error("Preencha todos os campos obrigatórios (*) e confirme a declaração.")
                    else:
                        dados_para_salvar = {
                            "nome": nome_c, "apelido": apelido, "ano_inicio": int(ano_i),
                            "ano_fim": int(ano_f) if ano_f > 0 else None,
                            "descricao": desc, "orgao_alvo": orgao, "operacao_pf": operac,
                            "valor_reais": float(valor) if valor > 0 else None,
                            "status_judicial": status,
                        }
                        form_ok = True

        elif "Nova pessoa" in tipo_contribuicao:
            with st.form("contrib_pessoa"):
                col1, col2 = st.columns(2)
                nome_p  = col1.text_input("Nome completo da pessoa *")
                tipo_p  = col2.selectbox("Tipo *", [
                    "politico","empresario","operador","doleiro","laranja","servidor","outro"],
                    format_func=lambda x: {
                        "politico":"🏛️ Político","empresario":"💼 Empresário",
                        "operador":"🔧 Operador","doleiro":"💱 Doleiro",
                        "laranja":"🧩 Laranja","servidor":"📋 Servidor","outro":"👤 Outro"}[x])
                col3, col4 = st.columns(2)
                cargo_p   = col3.text_input("Cargo ou função exercida")
                partido_p = col4.text_input("Partido")
                col5, col6 = st.columns(2)
                estado_p  = col5.text_input("Estado (UF) de atuação")
                sit_p     = col6.selectbox("Situação legal atual", [
                    "Investigado","Réu – ação penal em andamento",
                    "Condenado – 1ª instância","Condenado – STJ","Condenado – STF",
                    "Condenado – trânsito em julgado","Absolvido",
                    "Delator / acordo de colaboração","Prescrição","Falecido"])
                pena_p = st.text_input("Pena aplicada (se já condenado)", placeholder="Ex: 12 anos e 6 meses, regime fechado")
                obs_p  = st.text_area("Observações e contexto", height=100,
                                      placeholder="Descreva o papel desta pessoa no esquema, o período dos fatos e eventuais delações relacionadas.")
                st.markdown("#### 📎 Fonte")
                fonte_url  = st.text_input("Link da fonte *",
                    placeholder="https://www.trf4.jus.br/... ou link de reportagem")
                fonte_desc = st.text_area("Descreva a fonte", height=60,
                    placeholder="Ex: Sentença TRF4 processo nº 5000123 de 15/02/2023.")
                confirmado = st.checkbox("Confirmo que esta informação é de fonte pública e verificável *")
                enviado_p = st.form_submit_button("📨 Enviar para revisão", use_container_width=True)

                if enviado_p:
                    if not nome_p or not fonte_url or not confirmado:
                        st.error("Nome e fonte são obrigatórios.")
                    else:
                        dados_para_salvar = {
                            "nome": nome_p, "tipo": tipo_p, "cargo": cargo_p,
                            "partido": partido_p, "estado": estado_p,
                            "situacao_legal": sit_p, "pena": pena_p, "observacoes": obs_p,
                        }
                        form_ok = True

        elif "Novo relacionamento" in tipo_contribuicao:
            df_p_contrib = query(conn, "SELECT nome FROM pessoas ORDER BY nome")
            lista_pessoas = df_p_contrib["nome"].tolist()
            with st.form("contrib_rel"):
                col1, col2 = st.columns(2)
                pessoa_a = col1.selectbox("Pessoa A — quem pratica a ação *", lista_pessoas)
                pessoa_b = col2.selectbox("Pessoa B — quem sofre ou recebe a ação *", lista_pessoas)
                tipo_rel = st.selectbox("Tipo de relacionamento documentado *", [
                    "delatou","ordenou","recebeu_de","laranja_de",
                    "operador_de","aliou_se","financiou","intermediou","encobriu","investigou"],
                    format_func=lambda x: {
                        "delatou":"🗣️ delatou","ordenou":"📣 ordenou pagamento/crime",
                        "recebeu_de":"💰 recebeu propina de","laranja_de":"🧩 foi laranja de",
                        "operador_de":"🔧 foi operador de","aliou_se":"🤝 aliou-se com",
                        "financiou":"💵 financiou","intermediou":"↔️ intermediou",
                        "encobriu":"🙈 encobriu","investigou":"🔍 investigou"}[x])
                casos_lista = query(conn, "SELECT nome FROM casos ORDER BY nome")["nome"].tolist()
                caso_rel = st.selectbox("Caso ao qual o relacionamento pertence (opcional)", ["— não especificado —"] + casos_lista)
                desc_rel = st.text_area("Descrição do relacionamento *", height=100,
                    placeholder="Ex: Segundo delação premiada homologada pelo STF em 2016, X ordenou o pagamento de R$ 2 milhões a Y.")
                st.markdown("#### 📎 Fonte")
                fonte_url  = st.text_input("Link da fonte *")
                fonte_desc = st.text_area("Descreva a fonte", height=60)
                confirmado = st.checkbox("Confirmo que esta informação é pública e documentada *")
                enviado_r = st.form_submit_button("📨 Enviar para revisão", use_container_width=True)

                if enviado_r:
                    if pessoa_a == pessoa_b:
                        st.error("A e B precisam ser pessoas diferentes.")
                    elif not desc_rel or not fonte_url or not confirmado:
                        st.error("Descrição e fonte são obrigatórios.")
                    else:
                        dados_para_salvar = {
                            "pessoa_a_nome": pessoa_a, "pessoa_b_nome": pessoa_b,
                            "tipo": tipo_rel, "caso_nome": caso_rel if caso_rel != "— nenhum —" else None,
                            "descricao": desc_rel,
                        }
                        form_ok = True

        elif "Nova empresa" in tipo_contribuicao:
            with st.form("contrib_empresa"):
                col1, col2 = st.columns(2)
                nome_e  = col1.text_input("Razão social da empresa *")
                tipo_e  = col2.selectbox("Tipo *", [
                    "empreiteira","fachada","offshore","banco","outra"],
                    format_func=lambda x: {
                        "empreiteira":"🏗️ Empreiteira","fachada":"🎭 Fachada/laranja",
                        "offshore":"🌐 Offshore","banco":"🏦 Banco","outra":"🏢 Outra"}[x])
                col3, col4 = st.columns(2)
                cnpj_e  = col3.text_input("CNPJ (pode ser parcial)")
                pais_e  = col4.text_input("País de constituição", value="Brasil")
                sede_e  = st.text_input("Cidade-sede")
                status_e = st.selectbox("Status atual da empresa", [
                    "Ativa","Baixada","Ativa (investigada)","Ativa (sancionada – CEIS)",
                    "Em recuperação judicial","Falida","Desconhecido"])
                obs_e = st.text_area("Papel desempenhado no esquema", height=100)
                st.markdown("#### 📎 Fonte")
                fonte_url  = st.text_input("Link da fonte *")
                fonte_desc = st.text_area("Descreva a fonte", height=60)
                confirmado = st.checkbox("Confirmo que esta informação é de fonte pública e verificável *")
                enviado_e = st.form_submit_button("📨 Enviar para revisão", use_container_width=True)

                if enviado_e:
                    if not nome_e or not fonte_url or not confirmado:
                        st.error("Razão social e fonte são obrigatórios.")
                    else:
                        dados_para_salvar = {
                            "razao_social": nome_e, "tipo": tipo_e, "cnpj_parcial": cnpj_e,
                            "sede": sede_e, "pais": pais_e, "status": status_e, "observacoes": obs_e,
                        }
                        form_ok = True

        # ── SALVAR NA FILA ────────────────────────────────────────────────────
        if form_ok and dados_para_salvar:
            tipo_str = tipo_contribuicao.split()[1].lower()
            try:
                conn.execute("""
                    INSERT INTO contribuicoes_pendentes
                    (tipo, nome_contribuidor, email_contribuidor,
                     dados_json, fonte_url, fonte_descricao)
                    VALUES (?,?,?,?,?,?)
                """, (
                    tipo_str,
                    contrib_nome if "contrib_nome" in dir() else "",
                    contrib_email if "contrib_email" in dir() else "",
                    json.dumps(dados_para_salvar, ensure_ascii=False),
                    fonte_url,
                    fonte_desc if "fonte_desc" in dir() else "",
                ))
                conn.commit()
                st.success("✅ Contribuição recebida com sucesso! Ela será analisada pelo administrador em breve.")
                st.info("📬 Obrigado pela contribuição. Após a verificação das fontes informadas, os dados serão incorporados ao banco oficial.")
                st.cache_data.clear()
            except Exception as e:
                st.error(f"Erro ao salvar contribuição: {e}")

        # ── CONTADOR PÚBLICO ──────────────────────────────────────────────────
        try:
            n_pend = conn.execute("SELECT COUNT(*) FROM contribuicoes_pendentes WHERE status='pendente'").fetchone()[0]
            n_aprov = conn.execute("SELECT COUNT(*) FROM contribuicoes_pendentes WHERE status='aprovado'").fetchone()[0]
            st.markdown("---")
            col_c1, col_c2 = st.columns(2)
            col_c1.metric("📥 Contribuições aguardando revisão", n_pend)
            col_c2.metric("✅ Contribuições aprovadas e publicadas", n_aprov)
        except: pass



        # ── Nota sobre revisão ────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("""
        <div class="info-box">
        📬 <strong>Processo de revisão:</strong> cada contribuição é analisada manualmente pelo administrador. As aprovadas são incorporadas ao banco oficial em até 7 dias úteis. Caso tenha informado seu e-mail, você receberá uma resposta sobre a decisão.
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  PÁGINA 8 — SOBRE & COMO USAR
# ══════════════════════════════════════════════════════════════

elif pagina == "📚 Sobre & Como Usar":
    st.markdown("## 📚 Sobre o Observatório")

    tab1, tab2, tab3, tab4 = st.tabs(["🎯 O que é", "🎓 Para pesquisadores", "💻 Para desenvolvedores", "📊 Como expandir o banco"])

    with tab1:
        st.markdown("""
        ### O que é este projeto?
        
        O **Observatório da Corrupção Brasileira** é um banco de dados educacional e de código aberto que reúne, estrutura e conecta informações públicas sobre casos de corrupção no Brasil desde 1988.
        
        **Não existe nenhum banco unificado assim disponível publicamente.** Os dados estão espalhados em centenas de documentos do MPF, STF, TCU, PF e veículos de jornalismo investigativo. Este projeto conecta essas peças.
        
        ### Para quem é útil?
        """)

        col1, col2, col3 = st.columns(3)
        col1.markdown("""
        **🎓 Estudantes e pesquisadores**
        - TCCs e dissertações sobre corrupção
        - Análise de redes políticas
        - Estudos de ciência política e direito
        - Pesquisa sobre impunidade
        """)
        col2.markdown("""
        **📰 Jornalistas investigativos**
        - Cruzamento rápido de nomes e casos
        - Identificação de conexões entre investigados
        - Base para investigações próprias
        - Contexto histórico de escândalos
        """)
        col3.markdown("""
        **🏛️ Cidadãos e ativistas**
        - Educação cívica e transparência
        - Monitoramento de casos em andamento
        - Referência para denúncias ao MPF/CGU
        - Compreensão do sistema político
        """)

        st.markdown("""
        ---
        ### O que este projeto **não** é
        """)
        st.markdown("""
        <div class="danger-box">
        ❌ <strong>Não é prova jurídica</strong> — dados de pesquisa não substituem documentos oficiais.<br>
        ❌ <strong>Não define culpa definitiva</strong> — investigado não é condenado; toda condenação é passível de recurso.<br>
        ❌ <strong>Não é exaustivo</strong> — o banco é um ponto de partida para pesquisa, não um arquivo completo.<br>
        ❌ <strong>Não tem fins políticos ou partidários</strong> — dados de todos os partidos são incluídos com o mesmo critério.
        </div>
        """, unsafe_allow_html=True)

    with tab2:
        st.markdown("""
        ### Como usar em pesquisa acadêmica
        
        **1. Como citar corretamente**
        
        Ao utilizar este banco em trabalhos acadêmicos, cite sempre as fontes primárias:
        - MPF (mpf.mp.br) — denúncias e acordos de delação
        - STF/STJ/TRFs — acórdãos e decisões
        - TCU (tcu.gov.br) — auditorias e relatórios
        - Portal da Transparência (portaldatransparencia.gov.br)
        
        **2. Exemplos de perguntas de pesquisa que este banco pode ajudar a responder:**
        - Quais partidos aparecem em mais escândalos por período histórico?
        - Existe correlação entre valor desviado e tipo de pena aplicada?
        - Quais operadores financeiros conectam mais casos distintos?
        - Como a rede de relacionamentos evolui entre diferentes escândalos?
        - Há padrão no tipo de empresa usada para lavagem em cada era?
        
        **3. Metodologia recomendada**
        
        Use este banco como **ponto de partida**, nunca como fonte única. Para cada dado relevante em sua pesquisa, verifique a fonte primária antes de publicar qualquer conclusão.
        
        **4. Adaptando o banco à sua pesquisa**
        
        O banco pode ser adaptado para temas específicos:
        - Só casos do Estado X (filtre por orgao_alvo)
        - Só laranjas (filtre tipo = 'laranja' em pessoas)
        - Só offshores (filtre tipo = 'offshore' em empresas)
        """)

    with tab3:
        st.markdown("""
        ### Como instalar e publicar este aplicativo
        
        **Instalação local:**
        ```bash
        pip install streamlit pandas plotly
        streamlit run painel_corrupcao.py
        ```
        
        **Publicar gratuitamente no Streamlit Community Cloud:**
        1. Suba os arquivos para um repositório público no GitHub:
           - `painel_corrupcao.py`
           - `corrupcao_brasil.db`
           - `requirements.txt`
           - `atualizador.py` (opcional)
        2. Acesse **share.streamlit.io**
        3. Conecte sua conta GitHub
        4. Selecione o repositório e o arquivo principal
        5. Clique **Deploy** — em 2 minutos seu app tem uma URL pública
        
        **requirements.txt mínimo:**
        ```
        streamlit>=1.30.0
        pandas>=2.0.0
        plotly>=5.18.0
        requests>=2.31.0
        ```
        
        **Atualização automática após o primeiro deploy:**
        """)
        st.markdown("""
        <div class="info-box">
        💡 Graças à integração nativa com o GitHub, basta enviar o código ou o banco atualizado para o repositório — o Streamlit Cloud detecta a mudança e reinicia o aplicativo automaticamente em cerca de 1 minuto.
        </div>
        """, unsafe_allow_html=True)

    with tab4:
        st.markdown("### Como adicionar novos dados ao banco")

        opcao_add = st.selectbox("O que deseja adicionar?", ["Novo caso", "Nova pessoa", "Nova empresa"])

        if opcao_add == "Novo caso":
            with st.form("form_caso"):
                st.markdown("#### Adicionar novo caso de corrupção")
                nome_c = st.text_input("Nome do escândalo *")
                col_ca, col_cb = st.columns(2)
                ano_i = col_ca.number_input("Ano início *", ANO_MIN, ANO_MAX, datetime.now().year)
                ano_f = col_cb.number_input("Ano fim (0 = atual)", 0, ANO_MAX, 0)
                desc_c = st.text_area("Descrição")
                orgao_c = st.text_input("Órgão alvo")
                valor_c = st.number_input("Valor estimado (R$)", 0.0, step=1000000.0)
                status_c = st.text_input("Status judicial")
                submitted = st.form_submit_button("➕ Adicionar caso")
                if submitted and nome_c:
                    try:
                        cur = conn.cursor()
                        cur.execute("""INSERT INTO casos (nome, ano_inicio, ano_fim, descricao, orgao_alvo, valor_reais, status_judicial)
                                       VALUES (?,?,?,?,?,?,?)""",
                                    (nome_c, int(ano_i), int(ano_f) if ano_f > 0 else None, desc_c, orgao_c, float(valor_c) if valor_c > 0 else None, status_c))
                        conn.commit()
                        st.success(f"✅ Caso '{nome_c}' adicionado! Recarregue a página para ver.")
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"Erro: {e}")

        elif opcao_add == "Nova pessoa":
            with st.form("form_pessoa"):
                st.markdown("#### Adicionar nova pessoa")
                nome_p = st.text_input("Nome completo *")
                col_pa, col_pb = st.columns(2)
                tipo_p = col_pa.selectbox("Tipo *", ["politico", "empresario", "operador", "laranja", "doleiro", "servidor", "outro"])
                partido_p = col_pb.text_input("Partido")
                cargo_p = st.text_input("Cargo/Função")
                situacao_p = st.text_input("Situação legal")
                pena_p = st.text_input("Pena/Status")
                obs_p = st.text_area("Observações")
                submitted_p = st.form_submit_button("➕ Adicionar pessoa")
                if submitted_p and nome_p:
                    try:
                        cur = conn.cursor()
                        cur.execute("""INSERT INTO pessoas (nome, tipo, cargo, partido, situacao_legal, pena, observacoes)
                                       VALUES (?,?,?,?,?,?,?)""",
                                    (nome_p, tipo_p, cargo_p, partido_p or None, situacao_p, pena_p, obs_p))
                        conn.commit()
                        st.success(f"✅ '{nome_p}' adicionado!")
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"Erro: {e}")

        elif opcao_add == "Nova empresa":
            with st.form("form_empresa"):
                st.markdown("#### Adicionar nova empresa")
                nome_e = st.text_input("Razão Social *")
                col_ea, col_eb = st.columns(2)
                tipo_e = col_ea.selectbox("Tipo *", ["empreiteira", "fachada", "offshore", "banco", "outra"])
                pais_e = col_eb.text_input("País", value="Brasil")
                sede_e = st.text_input("Sede (cidade)")
                status_e = st.text_input("Status atual")
                obs_e = st.text_area("Observações")
                submitted_e = st.form_submit_button("➕ Adicionar empresa")
                if submitted_e and nome_e:
                    try:
                        cur = conn.cursor()
                        cur.execute("""INSERT INTO empresas (razao_social, tipo, sede, pais, status, observacoes)
                                       VALUES (?,?,?,?,?,?)""",
                                    (nome_e, tipo_e, sede_e, pais_e, status_e, obs_e))
                        conn.commit()
                        st.success(f"✅ '{nome_e}' adicionada!")
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"Erro: {e}")

    # Download dos dados
    st.markdown("---")
    st.markdown("### 📥 Exportar os dados")
    col_dl1, col_dl2, col_dl3 = st.columns(3)
    with col_dl1:
        csv_casos = df_casos.to_csv(index=False, sep=";").encode("utf-8-sig")
        st.download_button("⬇️ Baixar casos (.csv)", csv_casos, "casos.csv", "text/csv")
    with col_dl2:
        csv_pessoas = df_pessoas.to_csv(index=False, sep=";").encode("utf-8-sig")
        st.download_button("⬇️ Baixar pessoas (.csv)", csv_pessoas, "pessoas.csv", "text/csv")
    with col_dl3:
        csv_empresas = df_empresas.to_csv(index=False, sep=";").encode("utf-8-sig")
        st.download_button("⬇️ Baixar empresas (.csv)", csv_empresas, "empresas.csv", "text/csv")
