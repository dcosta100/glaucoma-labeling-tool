# ─────────────────────────────────────────────────────────────────────────────
# Visual Field Grading Interface — Labeling page : Last update September 10, 2025
# ─────────────────────────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
from utils import labeling

from utils.dataloader import DataLoader
from utils.ui_components import UIComponents
from utils.config import CSV_PATH, PDF_DIR 
from .image_handler import pdf_to_image_fitz


def labeling_page():
    st.set_page_config(
        page_title="Visual Field Labeling Interface",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Load database
    df = pd.read_csv(CSV_PATH)

    # Get patient list
    patients = df["maskedid"].unique().tolist()

    # Track current patient index
    if "current_patient_idx" not in st.session_state:
        st.session_state["current_patient_idx"] = 0

    patient_idx = st.session_state["current_patient_idx"]
    maskedid = patients[patient_idx]

    # Filter patient rows
    df_patient = df[df["maskedid"] == maskedid]
    age = df_patient["age"].dropna().iloc[0] if not df_patient["age"].isnull().all() else "Unknown"

    # Init helpers
    ui = UIComponents()
    dl = DataLoader()

    # --- HEADER ---
    ui.show_top_header(maskedid, age)

    # --- TWO COLUMN LAYOUT (OD | OS) ---
    col_r, col_l = ui.create_dual_column_layout()

    for eye, col in zip(["R", "L"], [col_r, col_l]):
        eye_df = df_patient[df_patient["eye"] == eye].sort_values("visual_field_number")

        with col:
            if eye_df.empty:
                ui.no_fields_warning(eye)
            else:
                # Get all visual field numbers for this eye
                vf_numbers = sorted(eye_df["visual_field_number"].astype(int).tolist())
                
                for idx, (_, row) in enumerate(eye_df.iterrows()):
                    vf_number = int(row["visual_field_number"])
                    vf_key = f"{maskedid}_{eye}_{vf_number}"
                    pdf_path = PDF_DIR / row["pdf_filename"]

                    ui.label_section_title(eye, vf_number)

                    # Show PDF
                    image = pdf_to_image_fitz(str(pdf_path))
                    if image:
                        st.image(image, use_container_width=True)
                    else:
                        st.warning("Could not render PDF page as image.")
                    # ui.display_pdf(str(pdf_path), height=450)

                    # Load previous labels if any
                    defaults = dl.load_labels(maskedid, eye, vf_number)

                    # Render labeling form
                    labels = ui.render_labels_for_field(vf_key, defaults)
                    labels.update({
                        "maskedid": maskedid,
                        "eye": eye,
                        "vf_number": vf_number,
                        "pdf_filename": row["pdf_filename"],
                        "specialist_name": st.session_state.get("specialist_name", "unknown"),
                        "last_updated": datetime.now().isoformat()
                    })

                    st.session_state[f"labels_{vf_key}"] = labels

                    # Show copy button only for the first field (index 0) if there are more fields
                    if idx == 0 and len(vf_numbers) > 1:
                        # Get target fields (all except the current one)
                        target_vfs = [vf for vf in vf_numbers if vf != vf_number]
                        ui.show_copy_labels_button(maskedid, eye, vf_number, target_vfs, df_patient)

    # --- SAVE BUTTONS ---
    save, flag, next_btn = ui.show_save_buttons()

    if save or next_btn:
        # Save all fields of current patient
        for _, row in df_patient.iterrows():
            vf_number = int(row["visual_field_number"])
            key = f"{maskedid}_{row['eye']}_{vf_number}"
            labels = st.session_state.get(f"labels_{key}", {})
            if labels:
                dl.save_labels(maskedid, row["eye"], vf_number, labels)

        ui.show_success_message("✅ Labels saved successfully.")

        if next_btn:
            st.session_state["current_patient_idx"] = (patient_idx + 1) % len(patients)
            st.rerun()

    if flag:
        ui.show_warning_message("⚠️ Case flagged for review.")


if __name__ == "__main__":
    labeling_page()