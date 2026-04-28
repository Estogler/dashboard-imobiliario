# app.py
# STREAMLIT RUN APP.PY

import streamlit as st
import pandas as pd
import plotly.express as px

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(
    page_title="Dashboard Imobiliário Premium",
    page_icon="🏢",
    layout="wide"
)

# =====================================================
# FUNÇÕES
# =====================================================
def limpar_valor(valor):
    valor = str(valor)
    valor = valor.replace("R$", "").replace(".", "").replace(",", ".").strip()
    return float(valor)

def moeda(v):
    return f"R$ {v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

def classificar_tipologia(txt):
    txt = str(txt).upper()

    varanda = "VAR" in txt
    moto = "MOT" in txt
    carro = "CAR" in txt

    if varanda and carro:
        return "F2/HMP (c/ Vaga Carro) (c/ Varanda)"
    elif varanda and moto:
        return "F2/HMP (c/ Vaga Moto) (c/ Varanda)"
    elif varanda:
        return "F2/HMP (c/ Varanda)"
    elif carro:
        return "F2/HMP (c/ Vaga Carro)"
    elif moto:
        return "F2/HMP (c/ Vaga Moto)"
    else:
        return "Faixa 2"

# =====================================================
# TÍTULO
# =====================================================
st.title("🏢 Dashboard Imobiliário Premium")
st.caption("Sistema Inteligente de Precificação Imobiliária")

# =====================================================
# UPLOAD CSV
# =====================================================
arquivo = st.file_uploader(
    "Envie o arquivo CSV do empreendimento",
    type=["csv"]
)

if not arquivo:
    st.info("Faça upload do CSV para iniciar.")
    st.stop()

# =====================================================
# LEITURA
# =====================================================
df = pd.read_csv(arquivo, sep=";", encoding="utf-8")

# =====================================================
# LIMPEZA
# =====================================================
df["Valor"] = df["Valor Unidade/Lote"].apply(limpar_valor)
df["Andar"] = pd.to_numeric(df["Andar"], errors="coerce")
df["Tipologia Final"] = df["Tipologia"].apply(classificar_tipologia)

# disponíveis
df_disp = df[
    df["Status da Unidade"].str.upper().str.contains("DISPON")
].copy()

# =====================================================
# SIDEBAR FILTROS
# =====================================================
st.sidebar.header("🔎 Filtros")

torre = st.sidebar.multiselect(
    "Torre / Bloco",
    sorted(df_disp["Torre"].unique()),
    default=sorted(df_disp["Torre"].unique())
)

tipologia = st.sidebar.multiselect(
    "Tipologia",
    sorted(df_disp["Tipologia Final"].unique()),
    default=sorted(df_disp["Tipologia Final"].unique())
)

andar_min = int(df_disp["Andar"].min())
andar_max = int(df_disp["Andar"].max())

faixa_andar = st.sidebar.slider(
    "Andar",
    andar_min,
    andar_max,
    (andar_min, andar_max)
)

# aplicar filtros
base = df_disp[
    (df_disp["Torre"].isin(torre)) &
    (df_disp["Tipologia Final"].isin(tipologia)) &
    (df_disp["Andar"] >= faixa_andar[0]) &
    (df_disp["Andar"] <= faixa_andar[1])
]

# =====================================================
# KPIS
# =====================================================
st.subheader("📈 Indicadores")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Unidades", len(base))
c2.metric("Valor Médio", moeda(base["Valor"].mean()))
c3.metric("Menor Valor", moeda(base["Valor"].min()))
c4.metric("Maior Valor", moeda(base["Valor"].max()))

st.divider()

# =====================================================
# TABELA COMERCIAL
# =====================================================
st.subheader("📋 Tabela Comercial")

resumo = base.groupby("Tipologia Final").agg(
    Unidades=("Unidade", "count"),
    A_Partir=("Valor", "min"),
    Ate=("Valor", "max"),
    Avaliacao=("Valor", "mean")
).reset_index()

resumo.columns = [
    "Tipologia",
    "Unidades",
    "A Partir:",
    "Até:",
    "Avaliação"
]

for col in ["A Partir:", "Até:", "Avaliação"]:
    resumo[col] = resumo[col].apply(moeda)

st.dataframe(
    resumo,
    use_container_width=True,
    hide_index=True
)

st.divider()

# =====================================================
# TABELA DE UNIDADES
# =====================================================
st.subheader("🏠 Unidades Disponíveis")

mostrar = base[
    ["Torre", "Unidade", "Andar", "Tipologia Final", "Valor"]
].copy()

mostrar["Valor"] = mostrar["Valor"].apply(moeda)

mostrar.columns = [
    "Bloco",
    "Unidade",
    "Andar",
    "Tipologia",
    "Preço"
]

st.dataframe(
    mostrar.sort_values(["Andar", "Unidade"]),
    use_container_width=True,
    hide_index=True
)

st.divider()

# =====================================================
# GRÁFICO 1
# =====================================================
st.subheader("📊 Preço por Andar")

fig = px.scatter(
    base,
    x="Andar",
    y="Valor",
    color="Tipologia Final",
    hover_data=["Unidade"],
    height=500
)

fig.update_layout(
    yaxis_title="Preço",
    xaxis_title="Andar",
    legend_title="Tipologia"
)

st.plotly_chart(fig, use_container_width=True)

# =====================================================
# GRÁFICO 2
# =====================================================
st.subheader("📉 Estoque por Tipologia")

estoque = base["Tipologia Final"].value_counts().reset_index()
estoque.columns = ["Tipologia", "Quantidade"]

fig2 = px.bar(
    estoque,
    x="Tipologia",
    y="Quantidade",
    text="Quantidade",
    height=450
)

fig2.update_layout(
    xaxis_title="Tipologia",
    yaxis_title="Quantidade"
)

st.plotly_chart(fig2, use_container_width=True)

# =====================================================
# FOOTER
# =====================================================
st.divider()
st.caption("Powered by Estogler Analytics • Dashboard Imobiliário Premium V2")