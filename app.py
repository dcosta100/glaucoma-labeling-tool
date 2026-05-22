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
        "Labeler name is not configured. Open **labeler_config.yaml** and set "
        "`labeler_name` to your name, then restart the app."
    )

if not config.MANIFEST_PATH.exists():
    _stop_with(
        f"Manifest not found at `{config.MANIFEST_PATH}`. "
        "Run `python scripts/prepare_data.py` or check the paths in labeler_config.yaml."
    )

df = data.get_manifest()
if df.empty:
    _stop_with("The manifest is empty — no exams to label.")

# ----- app ----- #
labeling_page(df)
