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

    def render_labels_for_field(self, vf_key: str, defaults: dict | None = None) -> dict:
        """
        Coluna 1 (normality/reliability): sempre visível (sem "Null").
        Colunas 2–4 (glaucoma, não-glaucoma, artefato): iniciam em "Null" e revelam progressivamente.
        Todo seletor recém-revelado abre já em "Null".
        """
        import streamlit as st
        from utils import config  # ajuste o import se seu config estiver em outro caminho

        st.markdown("##### Labels")

        selected: dict = {}
        defaults = defaults or {}

        # ---- helpers de chave e opções ----
        def sk(label_key: str) -> str:
            return f"{vf_key}_{label_key}"

        def with_null(options: list) -> list:
            return ["Null"] + [opt for opt in options if opt != "Null"]

        def clear_keys(keys: list[str]):
            for k in keys:
                st.session_state.pop(sk(k), None)

        # ---- inicialização por vf_key: força colunas 2–4 a começar em "Null" na primeira carga ----
        init_flag = f"{vf_key}__init_done"
        if not st.session_state.get(init_flag, False):
            dep_keys = [
                # glaucoma
                "gdefect1", "gposition1", "gdefect2", "gposition2", "gdefect3", "gposition3",
                # não-glaucoma
                "ngdefect1", "ngposition1", "ngdefect2", "ngposition2", "ngdefect3", "ngposition3",
                # artefatos
                "artifact1", "artifact2",
            ]
            for k in dep_keys:
                st.session_state[sk(k)] = "Null"
            st.session_state[init_flag] = True

        # ---- selectbox com controle de default/Null ----
        def pick(label_key: str, options: list, col, title: str | None = None,
                include_null: bool = True, prefer_null_default: bool = False):
            """
            prefer_null_default=True: se não houver valor no session_state, inicia em 'Null' (ignorando defaults).
            Ordem: session_state -> (prefer Null?) -> defaults -> "Null" (se existir) -> primeiro item.
            """
            opts = with_null(options) if include_null else list(options)
            label_txt = (title or label_key).replace("_", " ").capitalize()
            s_key = sk(label_key)

            if s_key in st.session_state and st.session_state[s_key] in opts:
                idx = opts.index(st.session_state[s_key])
            else:
                if prefer_null_default and "Null" in opts:
                    idx = opts.index("Null")
                else:
                    dv = defaults.get(label_key)
                    if dv in opts:
                        idx = opts.index(dv)
                    else:
                        idx = opts.index("Null") if "Null" in opts else 0

            val = col.selectbox(label_txt, opts, index=idx, key=s_key)
            selected[label_key] = val
            return val

        # ---- layout ----
        col1, col2, col3, col4 = st.columns(4)

        # Coluna 1: fixa (sem Null)
        with col1:
            pick("normality", config.VISUAL_FIELD_LABELS["normality"], col1, "Normality", include_null=False)
            pick("reliability", config.VISUAL_FIELD_LABELS["reliability"], col1, "Reliability", include_null=False)

        # Cadeia defeito/posição com abertura progressiva e forçando "Null" ao revelar
        def chain(prefix_def: str, prefix_pos: str, count: int, col, title_def: str, title_pos: str):
            for i in range(1, count + 1):
                dkey = f"{prefix_def}{i}"
                pkey = f"{prefix_pos}{i}"

                # Primeiro defeito da coluna deve preferir "Null" como default
                dval = pick(
                    dkey,
                    config.VISUAL_FIELD_LABELS[dkey],
                    col,
                    f"{title_def} {i}",
                    include_null=True,
                    prefer_null_default=(i == 1)
                )

                if dval == "Null":
                    # limpa position atual e tudo adiante (defects/positions subsequentes)
                    to_clear = [pkey] + \
                            [f"{prefix_def}{j}" for j in range(i + 1, count + 1)] + \
                            [f"{prefix_pos}{j}" for j in range(i + 1, count + 1)]
                    clear_keys(to_clear)
                    break
                else:
                    # ao revelar o position i, garanta que abra como "Null" se ainda não existir
                    if sk(pkey) not in st.session_state:
                        st.session_state[sk(pkey)] = "Null"
                    pick(
                        pkey,
                        config.VISUAL_FIELD_LABELS[pkey],
                        col,
                        f"{title_pos} {i}",
                        include_null=True,
                        prefer_null_default=True
                    )

                    # prepara o próximo defect para abrir como "Null" quando for revelado
                    if i < count:
                        ndkey = f"{prefix_def}{i + 1}"
                        if sk(ndkey) not in st.session_state:
                            st.session_state[sk(ndkey)] = "Null"

        # Coluna 2: Glaucomatoso
        with col2:
            chain("gdefect", "gposition", 3, col2, "Glaucoma Defect", "Glaucoma Position")

        # Coluna 3: Não-glaucomatoso
        with col3:
            chain("ngdefect", "ngposition", 3, col3, "Non-Glaucomatous Defect", "Non-Glaucomatous Position")

        # Coluna 4: Artefato (1 -> 2)
        with col4:
            a1 = pick("artifact1", config.VISUAL_FIELD_LABELS["artifact1"], col4, "Artifact 1",
                    include_null=True, prefer_null_default=True)
            if a1 == "Null":
                clear_keys(["artifact2"])
            else:
                # ao revelar artifact2, força abrir como "Null"
                if sk("artifact2") not in st.session_state:
                    st.session_state[sk("artifact2")] = "Null"
                pick("artifact2", config.VISUAL_FIELD_LABELS["artifact2"], col4, "Artifact 2",
                    include_null=True, prefer_null_default=True)

        # Comentário
        st.markdown("##### Comment")
        selected["comment"] = st.text_area("Comment", value=defaults.get("comment", ""), key=sk("comment"))

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
