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
        Display label selectors for a single visual field, using 2 rows, 4 columns for 1st row and 1 column for 2nd row.

        Args:
            vf_key: Unique key for the field (e.g., '1_R_2')
            defaults: Preloaded labels (if any)
        
        Returns:
            Dictionary of selected labels
        """
        st.markdown("##### Labels")

        selected = {}
        defaults = defaults or {}

        def with_null(options: list) -> list:
            return ["Null"] + [opt for opt in options if opt != "Null"]

        def clear_keys(keys):
            for k in keys:
                skey = f"{vf_key}_{k}"
                if skey in st.session_state:
                    del st.session_state[skey]

        def pick(label_key: str, options: list, col, title=None, default_override: str | None = None, include_null=True):
            opts = with_null(options) if include_null else list(options)
            label_txt = (title or label_key).replace("_", " ").capitalize()
            skey = f"{vf_key}_{label_key}"

            # ordem de preferência: session_state -> defaults -> default_override -> idx 0
            if skey in st.session_state and st.session_state[skey] in opts:
                idx = opts.index(st.session_state[skey])
            else:
                dv = defaults.get(label_key)
                if dv in opts:
                    idx = opts.index(dv)
                elif default_override in opts:
                    idx = opts.index(default_override)
                else:
                    idx = 0

            val = col.selectbox(label_txt, opts, index=idx, key=skey)
            selected[label_key] = val
            return val
        
        # --- Primeira linha (4 colunas) ---
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            pick("normality", config.VISUAL_FIELD_LABELS["normality"], col1, "Normality",
                default_override="Normal", include_null=False)  # sem "Null" aqui
            pick("reliability", config.VISUAL_FIELD_LABELS["reliability"], col1, "Reliability",
                default_override="Reliable", include_null=False)  # sem "Null" aqui
        
        with col2:
            g1 = pick("gdefect1", config.VISUAL_FIELD_LABELS["gdefect1"], col2, "Glaucoma Defect 1",
                    default_override="Null", include_null=True)
            if g1 != "Null":
                pick("gposition1", config.VISUAL_FIELD_LABELS["gposition1"], col2, "Glaucoma Position 1",
                    default_override="Null", include_null=True)
                g2 = pick("gdefect2", config.VISUAL_FIELD_LABELS["gdefect2"], col2, "Glaucoma Defect 2",
                        default_override="Null", include_null=True)
                if g2 != "Null":
                    pick("gposition2", config.VISUAL_FIELD_LABELS["gposition2"], col2, "Glaucoma Position 2",
                        default_override="Null", include_null=True)
                    g3 = pick("gdefect3", config.VISUAL_FIELD_LABELS["gdefect3"], col2, "Glaucoma Defect 3",
                            default_override="Null", include_null=True)
                    if g3 != "Null":
                        pick("gposition3", config.VISUAL_FIELD_LABELS["gposition3"], col2, "Glaucoma Position 3",
                            default_override="Null", include_null=True)
                else:
                    clear_keys(["gposition2", "gdefect3", "gposition3"])
            else:
                clear_keys(["gposition1", "gdefect2", "gposition2", "gdefect3", "gposition3"])

        with col3:
            ng1 = pick("ngdefect1", config.VISUAL_FIELD_LABELS["ngdefect1"], col3, "Non-Glaucomatous Defect 1",
                    default_override="Null", include_null=True)
            if ng1 != "Null":
                pick("ngposition1", config.VISUAL_FIELD_LABELS["ngposition1"], col3, "Non-Glaucomatous Position 1",
                    default_override="Null", include_null=True)
                ng2 = pick("ngdefect2", config.VISUAL_FIELD_LABELS["ngdefect2"], col3, "Non-Glaucomatous Defect 2",
                        default_override="Null", include_null=True)
                if ng2 != "Null":
                    pick("ngposition2", config.VISUAL_FIELD_LABELS["ngposition2"], col3, "Non-Glaucomatous Position 2",
                        default_override="Null", include_null=True)
                    ng3 = pick("ngdefect3", config.VISUAL_FIELD_LABELS["ngdefect3"], col3, "Non-Glaucomatous Defect 3",
                            default_override="Null", include_null=True)
                    if ng3 != "Null":
                        pick("ngposition3", config.VISUAL_FIELD_LABELS["ngposition3"], col3, "Non-Glaucomatous Position 3",
                            default_override="Null", include_null=True)
                else:
                    clear_keys(["ngposition2", "ngdefect3", "ngposition3"])
            else:
                clear_keys(["ngposition1", "ngdefect2", "ngposition2", "ngdefect3", "ngposition3"])


        with col4:
            a1 = pick("artifact1", config.VISUAL_FIELD_LABELS["artifact1"], col4, "Artifact 1",
                    default_override="Null", include_null=True)
            if a1 != "Null":
                pick("artifact2", config.VISUAL_FIELD_LABELS["artifact2"], col4, "Artifact 2",
                    default_override="Null", include_null=True)
            else:
                clear_keys(["artifact2"])
            
        # --- Segunda linha (1 coluna) ---
        st.markdown("##### Comment")
        selected["comment"] = st.text_area("Comment", value=defaults.get("comment", ""), key=f"{vf_key}_comment")

        return selected

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
