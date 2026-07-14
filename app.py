from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(
    page_title="Portal Administrativo | Controle de Internet",
    page_icon=":globe_with_meridians:",
    layout="wide",
    initial_sidebar_state="collapsed",
)


HTML_FILE = Path(__file__).with_name("controle-internet.html")

DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "mse123"


def load_html() -> str:
    if not HTML_FILE.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {HTML_FILE}")
    return HTML_FILE.read_text(encoding="utf-8")


def get_credentials() -> tuple[str, str]:
    username = st.secrets.get("portal_username", DEFAULT_USERNAME)
    password = st.secrets.get("portal_password", DEFAULT_PASSWORD)
    return username, password


def login_gate() -> bool:
    expected_user, expected_password = get_credentials()
    if st.session_state.get("portal_authenticated"):
        return True

    st.markdown(
        """
        <style>
          .login-wrap {
            max-width: 420px;
            margin: 64px auto;
            padding: 28px;
            background: #ffffff;
            border: 1px solid #e4e7ec;
            border-radius: 18px;
            box-shadow: 0 10px 30px rgba(16,24,40,.08);
          }
          .login-wrap h1 {
            margin: 0 0 8px;
            color: #17356c;
            font-size: 28px;
          }
          .login-wrap p {
            margin: 0 0 18px;
            color: #667085;
          }
        </style>
        <div class="login-wrap">
          <h1>Portal Administrativo</h1>
          <p>Acesso protegido para dados de internet, linhas ativas e credenciais.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("portal_login", clear_on_submit=False):
        username = st.text_input("Usuario")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar", use_container_width=True)

    if submitted:
        if username == expected_user and password == expected_password:
            st.session_state["portal_authenticated"] = True
            st.rerun()
        else:
            st.error("Usuario ou senha invalidos.")

    st.caption(
        "Para producao, configure `portal_username` e `portal_password` em `Secrets` no Streamlit Cloud."
    )
    return False


def main() -> None:
    st.markdown(
        """
        <style>
          .stApp {
            background: #e8eaee;
          }
          .block-container {
            max-width: 100%;
            padding: 0;
          }
          header[data-testid="stHeader"] {
            background: transparent;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )

    try:
        html = load_html()
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.stop()

    if not login_gate():
        return

    top_a, top_b = st.columns([1, 5])
    with top_a:
        if st.button("Sair", use_container_width=True):
            st.session_state["portal_authenticated"] = False
            st.rerun()

    components.html(html, height=2300, scrolling=True)


if __name__ == "__main__":
    main()
