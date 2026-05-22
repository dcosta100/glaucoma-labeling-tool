# ─────────────────────────────────────────────────────────────────────────────
# Visual Field Labeling Tool — versão local/offline
# ─────────────────────────────────────────────────────────────────────────────
import streamlit as st

from utils import config, data
from utils.labeling_ui import labeling_page

st.set_page_config(page_title=config.PAGE_TITLE, layout="wide")


def _stop_with(msg: str) -> None:
    st.error(msg)
    st.stop()


# ----- validações de configuração ----- #
if not config.LABELER_NAME:
    st.title("👀 Visual Field Labeling Tool")
    _stop_with(
        "Nome do labeler não configurado. Abra **labeler_config.yaml** e preencha "
        "`labeler_name` com o seu nome, depois reinicie o app."
    )

if not config.MANIFEST_PATH.exists():
    _stop_with(
        f"Manifest não encontrado em `{config.MANIFEST_PATH}`. "
        "Rode `python scripts/prepare_data.py` ou confirme os caminhos no labeler_config.yaml."
    )

df = data.get_manifest()
if df.empty:
    _stop_with("O manifest está vazio — nenhum exame para rotular.")

# ----- app ----- #
labeling_page(df)
