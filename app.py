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


def load_html() -> str:
    if not HTML_FILE.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {HTML_FILE}")
    return HTML_FILE.read_text(encoding="utf-8")


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

    components.html(html, height=2200, scrolling=True)


if __name__ == "__main__":
    main()
