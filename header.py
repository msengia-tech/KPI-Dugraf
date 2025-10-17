import streamlit as st


def show_header():
    # --- Configuração da Página ---
    # Define o título da página, o ícone e o layout para ocupar a largura inteira.
    st.set_page_config(
        page_title="Dugraf - Dashboard",
        page_icon="📊",
        layout="wide",
    )
    col1, col2 = st.columns([5, 8])
    with col1:
        st.image("assets/logo_dugraf_branco.png", width=150)  # controla o tamanho aqui
    with col2:
        st.markdown(
            "<h1 style='margin:0; margin-top:50px; padding-top:8px;'>DASHBOARD DUGRAF</h1>",
            unsafe_allow_html=True,
        )
