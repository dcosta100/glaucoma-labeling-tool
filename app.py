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
if not config.get_labeler_name():
    st.title("👀 Visual Field Labeling Tool")
    st.markdown("#### Welcome! Please enter your name to begin.")
    with st.form("labeler_name_form"):
        name_input = st.text_input("Your name", placeholder="e.g. Jane Smith")
        submitted = st.form_submit_button("Start labeling", type="primary")
    if submitted and name_input.strip():
        config.set_labeler_name(name_input.strip())
        st.rerun()
    st.caption("Your name is saved on this machine and stored with your labels.")
    st.stop()

config.LABELER_NAME = config.get_labeler_name()

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
