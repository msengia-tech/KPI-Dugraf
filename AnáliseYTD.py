import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
from sqlalchemy import create_engine, text
import locale
import matplotlib.pyplot as plt

# --- Configuração do Locale para o padrão brasileiro (Windows) ---
try:
    locale.setlocale(locale.LC_ALL, "Portuguese_Brazil.1252")
except locale.Error:
    locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")

# --- Configuração da Página ---
# Define o título da página, o ícone e o layout para ocupar a largura inteira.
from header import show_header

show_header()  # Exibe o cabeçalho padrão


# Logo no canto superior esquerdo (na sidebar)
st.logo("assets/logo_dugraf_branco.png", size="large")


# --- Carregamento dos dados ---
# --- Conexão Segura com o Banco de Dados ---
@st.cache_resource
def get_engine():
    engine = create_engine(
        f"postgresql://{st.secrets['database']['user']}:{st.secrets['database']['password']}@{st.secrets['database']['host']}:{st.secrets['database']['port']}/{st.secrets['database']['database']}"
    )
    return engine


engine = get_engine()


# --- Carregamento dos dados ---
# Substitua o CSV pela sua query SQL
@st.cache_data
def carregar_dados(query):
    with engine.connect() as connection:
        df = pd.read_sql_query(text(query), connection)
    return df


# Query
query_vendas = """
SELECT 
codpro, codigo_cliente, nota_fiscal, empresa, filial, razao_social, cidade, uf, nome_representante, apelido_representante, emissao, ano, mes, produto, fabricante, familia, tipo, qtde, unimed, m2, total_r, ptax_data, ptax_negociado, ptax_valor, total_us, us_m2, novo_comum, novo_trelleborg, ramo_categoria, marcador_aplicado

FROM 
dugraf_dashboard_comercial

WHERE 
codigo_cliente NOT IN (12977,14371,15140,94,19194,18978) AND
nota_fiscal NOT IN (14548,14549,14550,14552,14556,14539,25420, 12237, 12254, 25961, 26049, 27266, 27403, 17052, 28578, 28416 , 17585 , 17877, 17950 ) AND
emissao > '2017-01-01'

order by emissao
"""
df = carregar_dados(query_vendas)

# --- Conversão de Tipos ---
# É uma boa prática garantir que a coluna de data esteja no formato datetime
df["emissao"] = pd.to_datetime(df["emissao"])

# --- Barra Lateral (Filtros) ---
# Logo no canto superior esquerdo (na sidebar)
st.logo("assets/logo_dugraf_branco.png", size="large")
st.sidebar.header("🔍 Filtros")

# --- Cálculo das Datas Padrão (YTD) ---
hoje = datetime.date.today()
ano_atual = hoje.year
ano_anterior = ano_atual - 1

# Período 2 (Ano Atual YTD)
data_inicio_p2_padrao = datetime.date(ano_atual, 1, 1)
data_fim_p2_padrao = hoje

# Período 1 (Ano Anterior YTD)
data_inicio_p1_padrao = datetime.date(ano_anterior, 1, 1)
# Tenta criar a data correspondente no ano anterior, tratando o caso de ano bissexto
try:
    data_fim_p1_padrao = hoje.replace(year=ano_anterior)
except ValueError:
    # Se hoje for 29/Fev e o ano anterior não for bissexto, usa 28/Fev
    data_fim_p1_padrao = hoje.replace(year=ano_anterior, day=28)


# --- Filtros de Período ---
st.sidebar.subheader("Período 1 (Anterior)")
col1_p1, col2_p1 = st.sidebar.columns(2)
with col1_p1:
    data_inicio_p1 = st.date_input(
        "Data Inicial",
        value=data_inicio_p1_padrao,
        key="p1_start",
        format="DD/MM/YYYY",
    )
with col2_p1:
    data_fim_p1 = st.date_input(
        "Data Final", value=data_fim_p1_padrao, key="p1_end", format="DD/MM/YYYY"
    )

st.sidebar.subheader("Período 2 (Atual)")
col1_p2, col2_p2 = st.sidebar.columns(2)
with col1_p2:
    data_inicio_p2 = st.date_input(
        "Data Inicial",
        value=data_inicio_p2_padrao,
        key="p2_start",
        format="DD/MM/YYYY",
    )
with col2_p2:
    data_fim_p2 = st.date_input(
        "Data Final", value=data_fim_p2_padrao, key="p2_end", format="DD/MM/YYYY"
    )

st.sidebar.markdown("---")


# Filtro de Filial
filiais_disponiveis = sorted(df["filial"].unique())
filiais_selecionadas = st.sidebar.multiselect(
    "Filial", filiais_disponiveis, default=filiais_disponiveis
)

# Filtro de Segmento
# Remove valores nulos/NaN e em branco para evitar erros na ordenação
lista_segmentos = [
    seg for seg in df["ramo_categoria"].unique() if pd.notna(seg) and str(seg).strip()
]
segmentos_disponiveis = sorted(lista_segmentos)
segmentos_selecionadas = st.sidebar.multiselect(
    "Segmento", segmentos_disponiveis, default=segmentos_disponiveis
)

# Filtro por Vendedor com opção "Selecionar Todos"
selecionar_todos_reps = st.sidebar.checkbox(
    "Selecionar Todos os Representantes", value=True
)
lista_representantes = [
    seg
    for seg in df["apelido_representante"].unique()
    if pd.notna(seg) and str(seg).strip()
]
representantes_disponiveis = sorted(lista_representantes)

if selecionar_todos_reps:
    representantes_selecionados = st.sidebar.multiselect(
        "Representante",
        representantes_disponiveis,
        default=representantes_disponiveis,
    )
else:
    representantes_selecionados = st.sidebar.multiselect(
        "Representante", representantes_disponiveis, default=None
    )


# Filtro por Produto com opção "Selecionar Todos"
selecionar_todos_produtos = st.sidebar.checkbox(
    "Selecionar Todos os Produtos", value=True
)
produtos_disponiveis = sorted(df["produto"].unique())

if selecionar_todos_produtos:
    produtos_selecionados = st.sidebar.multiselect(
        "Produtos", produtos_disponiveis, default=produtos_disponiveis
    )
else:
    produtos_selecionados = st.sidebar.multiselect(
        "Produtos", produtos_disponiveis, default=None
    )

# --- Filtragem do DataFrame ---

# Converte as datas do input para datetime para a comparação
data_inicio_p1_dt = pd.to_datetime(data_inicio_p1)
data_fim_p1_dt = pd.to_datetime(data_fim_p1)
data_inicio_p2_dt = pd.to_datetime(data_inicio_p2)
data_fim_p2_dt = pd.to_datetime(data_fim_p2)

# O dataframe principal é filtrado com base nas seleções feitas na barra lateral.
df_filtrado = df[
    (df["filial"].isin(filiais_selecionadas))
    & (df["ramo_categoria"].isin(segmentos_selecionadas))
    & (df["apelido_representante"].isin(representantes_selecionados))
    & (df["produto"].isin(produtos_selecionados))
]


# Cria dataframes separados para cada período usando os filtros de data
df_p1 = df_filtrado[
    (df_filtrado["emissao"] >= data_inicio_p1_dt)
    & (df_filtrado["emissao"] <= data_fim_p1_dt)
]

df_p2 = df_filtrado[
    (df_filtrado["emissao"] >= data_inicio_p2_dt)
    & (df_filtrado["emissao"] <= data_fim_p2_dt)
]


# --- Conteúdo Principal ---

st.subheader(" KPI's - Análise YTD")
st.markdown(
    "Escolha os filtros para comparar a evolução de um período atual com o mesmo período no ano anterior."
)

# --- Métricas Principais (KPIs) com Comparação ---
st.subheader("m²")

# --- Cálculos para o Período 2 (Atual) ---
faturamento_p2 = df_p2["m2"].sum()
faturado_us_p2 = df_p2["total_us"].sum()
faturado_r_p2 = df_p2["total_r"].sum()
ticket_medio_p2 = faturado_us_p2 / faturamento_p2 if faturamento_p2 > 0 else 0

# --- Cálculos para o Período 1 (Anterior) ---
faturamento_p1 = df_p1["m2"].sum()
faturado_us_p1 = df_p1["total_us"].sum()
faturado_r_p1 = df_p1["total_r"].sum()
ticket_medio_p1 = faturado_us_p1 / faturamento_p1 if faturamento_p1 > 0 else 0


# --- Cálculos de Variação (Delta) em Percentual ---
def calcular_variacao_perc(atual, anterior):
    """Calcula a variação percentual de forma segura, evitando divisão por zero."""
    if anterior > 0:
        return (atual - anterior) / anterior
    # Se o anterior for 0, não há base para comparação percentual.
    # Pode retornar 0 ou um valor grande se o atual for > 0.
    # Retornar 0 é mais seguro para a visualização.
    return 0


delta_faturamento_perc = calcular_variacao_perc(faturamento_p2, faturamento_p1)
delta_faturado_us_perc = calcular_variacao_perc(faturado_us_p2, faturado_us_p1)
delta_faturado_r_perc = calcular_variacao_perc(faturado_r_p2, faturado_r_p1)
delta_ticket_medio_perc = calcular_variacao_perc(ticket_medio_p2, ticket_medio_p1)


# --- Inclusão dos CARDs com as métricas no Dashboard ---
col1, col2, col3, col4 = st.columns(4)
col1.metric(
    "m² Total (Período Atual)",
    f"{locale.format_string('%.2f', faturamento_p2, grouping=True)} m²",
    f"{delta_faturamento_perc:.2%}",
)
col2.metric(
    "US$ Faturado (Período Atual)",
    f"US$ {locale.format_string('%.2f', faturado_us_p2, grouping=True)}",
    f"{delta_faturado_us_perc:.2%}",
)
col3.metric(
    "R$ Faturado (Período Atual)",
    f"R$ {locale.format_string('%.2f', faturado_r_p2, grouping=True)}",
    f"{delta_faturado_r_perc:.2%}",
)
col4.metric(
    "US$ Ticket Médio (Período Atual)",
    f"US$ {locale.format_string('%.2f', ticket_medio_p2, grouping=True)}",
    f"{delta_ticket_medio_perc:.2%}",
)


st.markdown("---")

# --- Análises Visuais com Plotly (usando dados do Período Atual) ---
st.subheader("Análises de Pareto (Período Atual)")

# Garante que os gráficos só serão renderizados se houver dados no período atual
if not df_p2.empty:

    col_graf1, col_graf2 = st.columns(2)

    # --- Gráfico 1: Pareto Clientes - Matplotlib ---
    with col_graf1:
        # Prepara o DataFrame para exibição, garantindo que não modificamos o original (df_p2)
        df_para_exibir = df_p2.copy()
        pareto_cli_tab = (
            df_para_exibir.groupby("razao_social")["m2"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )

        pareto_cli_tab["% Acumulado"] = (
            pareto_cli_tab["m2"].cumsum() / pareto_cli_tab["m2"].sum() * 100
        )

        limite_pareto_cli = pareto_cli_tab[pareto_cli_tab["% Acumulado"] <= 80]

        # formata as colunas para exibição

        limite_pareto_cli["m2"] = limite_pareto_cli["m2"].apply(
            lambda x: locale.format_string("%.2f", x, grouping=True)
        )

        limite_pareto_cli["% Acumulado"] = limite_pareto_cli["% Acumulado"].apply(
            lambda x: locale.format_string("%.2f", x, grouping=True)
        )

        # 3. Seleciona e renomeia as colunas
        limite_pareto_cli = limite_pareto_cli[
            [
                "razao_social",
                "m2",
                "% Acumulado",
            ]
        ].rename(
            columns={
                "razao_social": "Cliente",
                "m2": "m²",
                "% Acumulado": "% Acumulado",
            }
        )

        # 4. Exibe o DataFrame já ordenado e formatado
        st.dataframe(
            limite_pareto_cli,
            use_container_width=True,
        )

    # --- Gráfico 2: Pareto de produtos - Matplotlib ---
    with col_graf2:
        plt.style.use("dark_background")

        # Cria a figura e o eixo
        fig, ax = plt.subplots(figsize=(8, 4))
        fig.patch.set_facecolor("#0E1117")  # Fundo da figura
        ax.set_facecolor("#0E1117")  # Fundo da área do gráfico

        # Agrupa e calcula os dados
        pareto_tipo = (
            df_p2.groupby("tipo")["m2"].sum().sort_values(ascending=False).reset_index()
        )

        pareto_tipo["% Acumulado"] = (
            pareto_tipo["m2"].cumsum() / pareto_tipo["m2"].sum()
        )

        limite_pareto = pareto_tipo[pareto_tipo["% Acumulado"] <= 0.8]
        total_m2 = pareto_tipo["m2"].sum()

        if total_m2 > 0:
            # Gráfico de barras
            ax.bar(limite_pareto["tipo"], limite_pareto["m2"], color="skyblue")

            # Adiciona rótulos
            for index, value in enumerate(limite_pareto["m2"]):
                ax.text(
                    index,
                    value,
                    f"{value:,.0f}",
                    ha="center",
                    va="bottom",
                    color="white",
                )

            # Ajustes visuais
            ax.set_ylabel("Volume (m²)", color="white")
            ax.set_xlabel("Tipo de Produto", color="white")
            ax.tick_params(axis="x", colors="white", rotation=45)
            ax.tick_params(axis="y", colors="white")
            ax.set_title("Pareto de Produtos", color="white")
            ax.grid(axis="y", linestyle="--", alpha=0.5)
            ax.set_axisbelow(True)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["bottom"].set_color("white")
            ax.spines["left"].set_color("white")

            # Exibe no Streamlit ajustando ao container
            st.pyplot(fig, use_container_width=True)
        else:
            st.warning("Nenhum dado de m² para gerar o gráfico.")

    st.markdown("---")

    # --- Gráfico de Ranking de vendedores e evolução mensal ---
    st.subheader("Evolução do Faturamento de m² (Período Atual)")

    col_graf3, col_graf4 = st.columns(2)

    # --- Gráfico 3 evolução mensal ---

    with col_graf3:

        df_p2_copy = df_p2.copy()
        df_p2_copy["mes_ano"] = df_p2_copy["emissao"].dt.to_period("M").astype(str)

        faturamento_mensal = (
            df_p2_copy.groupby("mes_ano")["m2"]
            .sum()
            .reset_index()
            .sort_values("mes_ano")
        )

        grafico_mensal = px.line(
            faturamento_mensal,
            x="mes_ano",
            y="m2",
            title="Faturamento Mensal - m²",
            labels={"mes_ano": "Mês", "m2": "Faturamento (m²)"},
            markers=True,
        )
        grafico_mensal.update_layout(title_x=0.1)
        st.plotly_chart(grafico_mensal, use_container_width=True)

    # --- Gráfico 4 Ranking Vendedores ---

    with col_graf4:

        top_reps = (
            df_p2.groupby("apelido_representante")["m2"]
            .sum()
            .nlargest(10)
            .sort_values(ascending=True)
            .reset_index()
        )

        grafico_reps = px.bar(
            top_reps,
            x="m2",
            y="apelido_representante",
            orientation="h",
            title="Top 10 Representantes por m² Faturado",
            labels={"m2": "Faturamento (m²)", "apelido_representante": ""},
            text="m2",
        )
        grafico_reps.update_traces(
            texttemplate="%{text:,.2s} m²", textposition="inside"
        )
        grafico_reps.update_layout(
            title_x=0.1,
            plot_bgcolor="#0E1117",  # Fundo da área do gráfico
            paper_bgcolor="#0E1117",  # Fundo do container do gráfico
            font=dict(color="white"),  # Cor do texto
            xaxis=dict(color="white", gridcolor="gray"),  # Eixos
            yaxis=dict(color="white", gridcolor="gray"),
        )

        st.plotly_chart(grafico_reps, use_container_width=True)

else:
    st.warning(
        "Nenhum dado encontrado para o Período 2 (Atual) com os filtros selecionados."
    )


# --- Tabela de Dados Detalhados ---
st.subheader("Dados Detalhados (Período Atual)")

# Prepara o DataFrame para exibição, garantindo que não modificamos o original (df_p2)
df_para_exibir = df_p2.copy()

# 1. PRIMEIRO, ordena o DataFrame pela data original (datetime)
df_para_exibir = df_para_exibir.sort_values(by="emissao", ascending=False)

# 2. AGORA, formata as colunas para exibição
df_para_exibir["total_us"] = df_para_exibir["total_us"].apply(
    lambda x: locale.format_string("%.2f", x, grouping=True)
)
df_para_exibir["m2"] = df_para_exibir["m2"].apply(
    lambda x: locale.format_string("%.2f", x, grouping=True)
)
df_para_exibir["emissao"] = df_para_exibir["emissao"].dt.strftime("%d/%m/%Y")

# 3. Seleciona e renomeia as colunas
df_para_exibir = df_para_exibir[
    [
        "filial",
        "ramo_categoria",
        "razao_social",
        "apelido_representante",
        "emissao",
        "tipo",
        "codpro",
        "m2",
        "total_us",
    ]
].rename(
    columns={
        "filial": "Filial",
        "ramo_categoria": "Mercado",
        "razao_social": "Cliente",
        "apelido_representante": "Representante",
        "emissao": "Data Emissão",
        "tipo": "Produto",
        "codpro": "Cód Produto",
        "m2": "m²",
        "total_us": "Valor (US$)",
    }
)

# 4. Exibe o DataFrame já ordenado e formatado
st.dataframe(
    df_para_exibir,
    use_container_width=True,
)
