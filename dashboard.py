import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import calendar
import warnings

from datetime import datetime
from sqlalchemy import create_engine

# Elimina Warnings
warnings.filterwarnings('ignore')


#st.set_page
# _config(layout="wide")
st.set_page_config(layout='wide', initial_sidebar_state='expanded')

with open('static/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


st.sidebar.header('Dashboard `Encomendas`')

# Função para conectar ao PostgreSQL
def conectar_postgres():
   # conn = psycopg2.connect(dbname='company', user='postgres', host='localhost', port=5433, password='admin')
    engine = create_engine('postgresql://postgres:admin@localhost:5433/company')
    conn = engine.connect()
    return conn

meses = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro"
}

# Obtendo o ano e mês atual
ano_atual = datetime.now().year
mes_atual = datetime.now().month

# Função para carregar os dados da tabela de vendas do PostgreSQL
@st.cache_data
def carregar_dados():
    conn = conectar_postgres()
    query = """
        SELECT  clientes.cliente_id  as "Cliente ID", 
                clientes.nome_cliente as "Cliente", 
                clientes.pais as "País",
                ordens.qtde as "Quantidade",
                ordens.produto_id as " Produto ID", 
                produtos.nome_produto as "Produto",
                ordens.data as "Data",
                produtos.preco as "Preço"
        FROM ordens
        INNER JOIN clientes on clientes.cliente_id = ordens.cliente_id
        INNER JOIN produtos on produtos.produto_id = ordens.produto_id
        ;"""
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Carregar os dados
dados = carregar_dados()


# sidebar
# Obtendo o ano e mês atual
ano_atual = datetime.now().year
mes_atual = datetime.now().month

# Filtro Ano
select_year = st.sidebar.selectbox('Ano', ['Todos'] + list(range(ano_atual, ano_atual - 10, -1)))
# Filtro Mês
select_month = st.sidebar.selectbox('Mês', ['Todos'] + list(meses.values()))

# print(select_month)

dados["Data"] = pd.to_datetime(dados["Data"])
dados["Ano"] = dados["Data"].apply(lambda x: str(x.year))
dados["Mes"] = dados["Data"].apply(lambda x: x.month)
dados['Mes'] = dados['Mes'].map(meses)

# Sort DataFrame by month names
dados['Mes'] = pd.Categorical(dados['Mes'], categories=meses.values(), ordered=True)

# Filtro cliente
select_client = st.sidebar.selectbox('Cliente', ['Todos'] + sorted(dados["Cliente"].unique()))

# Filtro País
select_country = st.sidebar.multiselect('País', ['Todos'] + sorted(dados["País"].unique()), ['Portugal', 'Grécia', 'Angola', 'Bélgica'])

# Filtro Produto
select_product = st.sidebar.multiselect('Produto', ['Todos'] + sorted(dados["Produto"].unique()), ["Notebook", "Memória RAM", "Disco SSD"])

# Create navigation sidebar
page = st.sidebar.radio("Página", ["Principal", "Detalhes"])

dados_filtered = dados[
    ((select_year == 'Todos') | (dados['Ano'] == str(select_year))) &
    ((select_client == 'Todos') | (dados['Cliente'] == select_client)) &
    ((select_month == 'Todos') | (dados['Mes'] == select_month)) &
    ((('Todos' in select_country) or dados['País'].isin(select_country)))
]

st.sidebar.markdown('''
---
Created by [JC](https://github.com/bluedragon86)
''')

# Define function for page 1
def page1():

    # Display the sum of the "preco" column formatted as euros
    formatted_value = "{:,.2f} €".format(dados_filtered["Preço"].sum()).replace(",", " ")
    st.metric("Valor [€]", formatted_value) 

    col2, col3 = st.columns(2)
    col4, col5, col6 = st.columns(3)

    if select_year == 'Todos':
        line_months = dados_filtered.groupby("Ano")[["Preço"]].sum().reset_index()
        fig1_line = px.scatter(line_months, x="Ano", y="Preço", size="Preço", color="Ano", size_max=60,  title="Vendas por Ano")
        # Increment the years on the x-axis
        fig1_line.update_layout(xaxis=dict(tickmode='linear', tick0=line_months["Ano"].min(), dtick=1))
        col2.plotly_chart(fig1_line, use_container_width=True)
    else:
        line_months = dados_filtered.groupby("Mes")[["Preço"]].sum().reset_index()
        fig1_line =  px.line(line_months, x="Mes", y="Preço", title="Vendas por Mês")

        # fig1_line = px.scatter(line_months, x="Mes", y="Preço", size="Preço", color="Mes", size_max=60,  title="Vendas por Mês")
        col2.plotly_chart(fig1_line, use_container_width=True)

    if select_year == 'Todos':
        bar_months = dados_filtered.groupby("Ano")[["Preço"]].sum().reset_index()
        fig2_months = px.bar(bar_months, x="Ano", y="Preço", title="Vendas por Ano")
        # Increment the years on the x-axis
        fig2_months.update_layout(xaxis=dict(tickmode='linear', tick0=line_months["Ano"].min(), dtick=1))
        col3.plotly_chart(fig2_months, use_container_width=True)
    else:
        bar_months = dados_filtered.groupby("Mes")[["Preço"]].sum().reset_index()
        fig2_months = px.bar(bar_months, x="Mes", y="Preço", title="Vendas por Mês")
        col3.plotly_chart(fig2_months, use_container_width=True)   

    donut_paises = px.pie(dados_filtered, values="Preço", names="País", title="Vendas por País", hole=0.5)
    col4.plotly_chart(donut_paises, use_container_width=True)

    donut_clientes = px.pie(dados_filtered, values="Preço", names="Cliente", title="Vendas por Cliente", hole=0.5)
    col5.plotly_chart(donut_clientes, use_container_width=True)

    donut_produtos = px.pie(dados_filtered, values="Preço", names="Produto", title="Vendas por Produto", hole=0.5)
    col6.plotly_chart(donut_produtos, use_container_width=True)

def page2():
    # Exibir o DataFrame
    st.write(dados_filtered)

# Display the selected page
if page == "Principal":
    page1()
elif page == "Detalhes":
    page2()
