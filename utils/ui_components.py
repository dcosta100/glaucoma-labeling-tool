import streamlit as st
import base64
import os
from typing import Dict
from utils import config


class UIComponents:
    """Handles UI components and interactions for the visual field labeling interface"""

    def __init__(self):
        pass

    def display_pdf(self, pdf_path: str, height: int = 500):
        """Embed a PDF file into the Streamlit interface."""
        if not os.path.exists(pdf_path):
            st.error(f"PDF file not found: {pdf_path}")
            return

        with open(pdf_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode("utf-8")
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="{height}px" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)

    def render_labels_for_field(self, vf_key: str, defaults: Dict = None) -> Dict:
        """
        Display label selectors for a single visual field.
        
        Args:
            vf_key: Unique key for the field (e.g., '1_R_2')
            defaults: Preloaded labels (if any)
        
        Returns:
            Dictionary of selected labels
        """
        st.markdown("##### Labels")

        selected_labels = {}

        # --- Primeira linha (4 colunas) ---
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            for label_key in ["normality", "reliability"]:
                options = config.VISUAL_FIELD_LABELS[label_key]
                default = defaults.get(label_key) if defaults else options[0]
                selected = st.selectbox(
                    label_key.capitalize(),
                    options,
                    index=options.index(default) if default in options else 0,
                    key=f"{vf_key}_{label_key}",
                )
                selected_labels[label_key] = selected

        with col2:
            for label_key in ["gdefect1", "gposition1", "gdefect2", "gposition2", "gdefect3", "gposition3"]:
                options = config.VISUAL_FIELD_LABELS[label_key]
                default = defaults.get(label_key) if defaults else options[0]
                selected = st.selectbox(
                    label_key.capitalize(),
                    options,
                    index=options.index(default) if default in options else 0,
                    key=f"{vf_key}_{label_key}",
                )
                selected_labels[label_key] = selected
        
        with col3:
            for label_key in ["ngdefect1", "ngposition1", "ngdefect2", "ngposition2", "ngdefect3", "ngposition3"]:
                options = config.VISUAL_FIELD_LABELS[label_key]
                default = defaults.get(label_key) if defaults else options[0]
                selected = st.selectbox(
                    label_key.capitalize(),
                    options,
                    index=options.index(default) if default in options else 0,
                    key=f"{vf_key}_{label_key}",
                )
                selected_labels[label_key] = selected

        with col4:
            for label_key in ["artifact1", "artifact2"]:
                options = config.VISUAL_FIELD_LABELS[label_key]
                default = defaults.get(label_key) if defaults else options[0]
                selected = st.selectbox(
                    label_key.capitalize(),
                    options,
                    index=options.index(default) if default in options else 0,
                    key=f"{vf_key}_{label_key}",
                )
                selected_labels[label_key] = selected
        
        # --- Segunda linha (1 coluna) ---
        default_comment = defaults.get("comment") if defaults else ""
        comment = st.text_area("Comment", value=default_comment, key=f"{vf_key}_comment")
        selected_labels["comment"] = comment

        return selected_labels

    def show_top_header(self, maskedid: str, age: str):
        """Display the header with patient ID and age"""
        st.markdown(
            f"""
            <h2 style='text-align:center;'>Patient ID: {maskedid} &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; Age: {age}</h2>
            <hr style='margin-top:-10px;' />
            """,
            unsafe_allow_html=True,
        )

    def create_dual_column_layout(self):
        """Create side-by-side scrollable sections for OD and OS"""
        col_r, col_l = st.columns(2)
        return col_r, col_l

    def label_section_title(self, eye: str, index: int):
        """Label for each visual field within a column"""
        st.markdown(f"### Eye: **{eye}**, Field #{index}")

    def no_fields_warning(self, eye: str):
        """Display a warning when no visual fields are available"""
        st.warning(f"No visual field tests available for eye {eye}")

    def show_save_buttons(self):
        """Display action buttons at the bottom"""
        col1, col2, col3 = st.columns([1, 1, 2])
        save = col1.button("💾 Save")
        flag = col2.button("🚩 Flag")
        next_btn = col3.button("➡️ Save and Next Patient")
        return save, flag, next_btn

    def show_success_message(self, msg: str):
        st.success(msg)

    def show_error_message(self, msg: str):
        st.error(msg)

    def show_warning_message(self, msg: str):
        st.warning(msg)
