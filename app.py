import streamlit as st
import pandas as pd
import plotly.express as px
import re

# ================= CONFIG =================
st.set_page_config(
    page_title="Dashboard Imobiliário Premium",
    page_icon="🏢",
    layout="wide"
)

# ================= DADOS =================
@st.cache_data
def carregar_dados():
    bruto = pd.read_csv("apartamentos.csv", sep=";", engine="python", header=None)

    dados = []

    for _, row in bruto.iterrows():
        linha = [str(x).strip() for x in row if pd.notna(x) and str(x).strip() != ""]

        if not linha:
            continue

        texto = " ".join(linha).upper()

        if "UNIDADE" in texto:
            continue

        if len(linha) < 6:
            continue

        idx = None
        for i, val in enumerate(linha):
            if val.isdigit():
                idx = i
                break

        if idx is None or len(linha) < idx + 6:
            continue

        unidade = linha[idx]
        bloco = linha[idx + 1]
        andar = linha[idx + 2]
        quartos = linha[idx + 3]
        posicao = linha[idx + 4]
        area = linha[idx + 5]

        m = re.search(r'R\$\s*([\d\.]+,\d{2})', " ".join(linha))
        if not m:
            continue

        valor = m.group(1)

        dados.append([unidade, bloco, andar, quartos, posicao, area, valor])

    df = pd.DataFrame(dados, columns=[
        "unidade", "bloco", "andar", "quartos", "posicao", "area", "valor_venda"
    ])

    df["valor_venda"] = (
        df["valor_venda"]
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    df["valor_venda"] = pd.to_numeric(df["valor_venda"], errors="coerce")

    df["area"] = (
        df["area"]
        .str.replace("m²", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.replace(" ", "", regex=False)
    )
    df["area"] = pd.to_numeric(df["area"], errors="coerce")

    df["preco_m2"] = df["valor_venda"] / df["area"]

    return df.dropna()

df = carregar_dados()

# ================= SIDEBAR =================
st.sidebar.header("🔎 Filtros")

blocos = st.sidebar.multiselect("Bloco", df["bloco"].unique(), default=df["bloco"].unique())
andares = st.sidebar.multiselect("Andar", df["andar"].unique(), default=df["andar"].unique())
quartos = st.sidebar.multiselect("Quartos", df["quartos"].unique(), default=df["quartos"].unique())

df_filtrado = df[
    (df["bloco"].isin(blocos)) &
    (df["andar"].isin(andares)) &
    (df["quartos"].isin(quartos))
]

# ================= TÍTULO =================
st.title("🏢 Dashboard Imobiliário Premium")
st.markdown("Visão estratégica para tomada de decisão.")

# ================= KPIs =================
st.subheader("📊 Resumo Executivo")

c1, c2, c3, c4, c5, c6 = st.columns(6)

c1.metric("Total", len(df_filtrado))
c2.metric("Estoque", f"R$ {df_filtrado['valor_venda'].sum():,.0f}")
c3.metric("Ticket Médio", f"R$ {df_filtrado['valor_venda'].mean():,.0f}")
c4.metric("Maior", f"R$ {df_filtrado['valor_venda'].max():,.0f}")
c5.metric("Menor", f"R$ {df_filtrado['valor_venda'].min():,.0f}")
c6.metric("Preço m²", f"R$ {df_filtrado['preco_m2'].mean():,.0f}")

st.markdown("---")

# ================= LINHA 1 =================
col1, col2 = st.columns(2)

with col1:
    st.subheader("🏢 Comparação entre Blocos")

    fig = px.bar(
        df_filtrado.groupby("bloco")["valor_venda"].sum().reset_index(),
        x="bloco",
        y="valor_venda",
        color="bloco",
        text_auto=True
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("🏗️ Valorização por Andar")

    fig = px.line(
        df_filtrado.groupby("andar")["valor_venda"].mean().reset_index(),
        x="andar",
        y="valor_venda",
        markers=True
    )
    st.plotly_chart(fig, use_container_width=True)

# ================= LINHA 2 =================
col3, col4 = st.columns(2)

with col3:
    st.subheader("☀️ Posição Solar")

    fig = px.bar(
        df_filtrado.groupby("posicao")["valor_venda"].mean().reset_index(),
        x="posicao",
        y="valor_venda",
        text_auto=True
    )
    st.plotly_chart(fig, use_container_width=True)

with col4:
    st.subheader("💰 Preço por m²")

    fig = px.scatter(
        df_filtrado,
        x="area",
        y="valor_venda",
        color="bloco",
        size="preco_m2",
        hover_name="unidade"
    )
    st.plotly_chart(fig, use_container_width=True)

# ================= LINHA 3 =================
col5, col6 = st.columns(2)

with col5:
    st.subheader("📊 Tipos de Apartamento")

    top = df_filtrado["quartos"].value_counts().reset_index()
    top.columns = ["quartos", "quantidade"]

    fig = px.bar(top, x="quartos", y="quantidade")
    st.plotly_chart(fig, use_container_width=True)

with col6:
    st.subheader("💎 Unidades Premium")

    limite = df_filtrado["valor_venda"].quantile(0.9)
    premium = df_filtrado[df_filtrado["valor_venda"] >= limite]

    st.metric("Qtd Premium", len(premium))
    st.dataframe(premium.sort_values("valor_venda", ascending=False), height=250)

# ================= TABELA =================
st.markdown("---")
st.subheader("📋 Base Completa")
st.dataframe(df_filtrado, use_container_width=True)