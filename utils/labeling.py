# ─────────────────────────────────────────────────────────────────────────────
# Visual Field Grading Interface — Labeling page : Updated with preload & cache
# ─────────────────────────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import os
import tempfile
from pathlib import Path
from datetime import datetime
import threading

from utils.dataloader import DataLoader
from utils.ui_components import UIComponents
from utils.image_handler import pdf_to_image_fitz
from utils.patient_tracker import PatientTracker
from utils.dataloader import GOOGLE_AVAILABLE


# ---------------- Helpers ---------------- #

def preload_patient(maskedid: str, df, cache: dict):
    """Carrega PDFs e dados do paciente e guarda no session_state"""
    df_patient = df[df["maskedid"] == maskedid]
    pdf_images = []

    for _, row in df_patient.iterrows():
        try:
            img = pdf_to_image_fitz(row["pdf_filename"])
            pdf_images.append(img)
        except Exception as e:
            print(f"[preload_patient] erro renderizando {row['pdf_filename']}: {e}")

    cache[maskedid] = {
        "df": df_patient,
        "pdf_images": pdf_images,
    }


def update_local_progress(username: str, maskedid: str):
    """Atualiza snapshot local de progresso (sem esperar Sheets)"""
    if "progress_cache" not in st.session_state:
        st.session_state["progress_cache"] = {}
    st.session_state["progress_cache"].setdefault(username, set()).add(maskedid)


# ---------------- Main Page ---------------- #

def labeling_page():
    """
    Main labeling page function - called after successful authentication
    Handles the complete visual field labeling workflow with cloud integration
    """

    # Get current authenticated username
    username = st.session_state.get('specialist_name', 'unknown')

    # Initialize data loader
    dl = DataLoader()

    # Load database (prefer cloud)
    df = None
    data_source = None

    with st.spinner("Loading database from cloud..."):
        df = dl.get_csv_from_drive("opv_24-2_prepared.csv")
        if df is not None:
            data_source = "cloud"
            st.success("Database loaded from Google Drive")

    if df is None:
        try:
            from utils.config import CSV_PATH
            if os.path.exists(CSV_PATH):
                df = pd.read_csv(CSV_PATH)
                data_source = "local"
                st.info("Using local database file")
            else:
                st.error("Database not found in cloud or locally")
                st.stop()
        except Exception as e:
            st.error(f"Error loading database: {e}")
            st.stop()

    # Validate dataframe
    required_columns = ["maskedid", "eye", "visual_field_number", "pdf_filename", "age"]
    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        st.error(f"Database missing required columns: {missing}")
        st.stop()

    # Unique patients
    all_patients = df["maskedid"].unique().tolist()
    if not all_patients:
        st.error("No patients found in database")
        st.stop()

    # Patient tracker
    tracker = PatientTracker()

    # Detect already completed
    newly_completed = tracker.auto_mark_completed_patients(username, all_patients, df)
    if newly_completed:
        st.sidebar.success(f"Found {len(newly_completed)} already completed patients")

    # Available patients
    available_patients = tracker.get_available_patients(username, all_patients)
    if not available_patients:
        st.success("Congratulations! All patients completed!")
        st.info(f"Total patients: {len(all_patients)}")
        stats = tracker.get_user_stats(username, len(all_patients))
        st.metric("Completion Rate", f"{stats['completion_percentage']:.1f}%")
        return

    # Progress stats
    stats = tracker.get_user_stats(username, len(all_patients))

    # --- snapshot local ---
    if "progress_cache" not in st.session_state:
        st.session_state["progress_cache"] = {}
    if username in st.session_state["progress_cache"]:
        completed_local = st.session_state["progress_cache"][username]
        stats["completed_count"] = len(completed_local)
        stats["remaining_count"] = len(all_patients) - len(completed_local)
        stats["completion_percentage"] = (len(completed_local) / len(all_patients) * 100)

    # Sidebar progress
    with st.sidebar:
        st.markdown("### Your Progress")
        st.metric("Completed", stats['completed_count'])
        st.metric("Remaining", stats['remaining_count'])
        st.progress(stats['completion_percentage'] / 100)
        st.caption(f"{stats['completion_percentage']:.1f}% Complete")
        if stats['last_patient']:
            st.caption(f"Last: {stats['last_patient']}")
        st.markdown("---")
        st.caption(f"Data source: {data_source}")

    # Current patient index
    if "current_patient_idx" not in st.session_state:
        st.session_state["current_patient_idx"] = 0
    patient_idx = st.session_state["current_patient_idx"]

    if patient_idx >= len(available_patients):
        st.session_state["current_patient_idx"] = 0
        patient_idx = 0

    maskedid = available_patients[patient_idx]

    # --- Preload manager ---
    if "preloaded_patients" not in st.session_state:
        st.session_state["preloaded_patients"] = {}

    if maskedid in st.session_state["preloaded_patients"]:
        preload = st.session_state["preloaded_patients"].pop(maskedid)
        df_patient = preload["df"]
        preload_images = preload["pdf_images"]
    else:
        df_patient = df[df["maskedid"] == maskedid]
        preload_images = None

    # Age
    age = df_patient["age"].dropna().iloc[0] if not df_patient["age"].isnull().all() else "Unknown"

    # UI helper
    ui = UIComponents()

    # Header
    ui.show_top_header(maskedid, age)
    st.markdown(f"**Patient {patient_idx + 1} of {len(available_patients)}** | Specialist: {username}")
    st.markdown("---")

    # Layout: R and L eyes
    col_r, col_l = ui.create_dual_column_layout()

    # Loop eyes
    for eye, col in zip(["R", "L"], [col_r, col_l]):
        eye_df = df_patient[df_patient["eye"] == eye].sort_values("visual_field_number")
        with col:
            if eye_df.empty:
                ui.no_fields_warning(eye)
            else:
                vf_numbers = sorted(eye_df["visual_field_number"].astype(int).tolist())
                for idx, (_, row) in enumerate(eye_df.iterrows()):
                    vf_number = int(row["visual_field_number"])
                    vf_key = f"{maskedid}_{eye}_{vf_number}"
                    pdf_filename = row["pdf_filename"]

                    ui.label_section_title(eye, vf_number)

                    # Display image
                    try:
                        image = None
                        if preload_images:
                            # usa imagem já carregada
                            image = preload_images.pop(0) if preload_images else None
                        if not image:
                            if data_source == "cloud":
                                pdf_content = dl.get_pdf_from_drive(pdf_filename)
                                if pdf_content:
                                    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
                                        tmp_pdf.write(pdf_content.getvalue())
                                        tmp_pdf_path = tmp_pdf.name
                                    image = pdf_to_image_fitz(tmp_pdf_path)
                                    os.unlink(tmp_pdf_path)
                            if not image:
                                from utils.config import PDF_DIR
                                local_pdf = Path(PDF_DIR) / pdf_filename
                                if local_pdf.exists():
                                    image = pdf_to_image_fitz(str(local_pdf))
                        if image is not None:
                            st.image(image, use_container_width=True)
                        else:
                            st.warning(f"Could not render PDF: {pdf_filename}")
                    except Exception as e:
                        st.error(f"Error loading PDF {pdf_filename}: {e}")

                    # Defaults + form
                    defaults = dl.load_labels(username, maskedid, eye, vf_number)
                    labels = ui.render_labels_for_field(vf_key, defaults)
                    labels.update({
                        "maskedid": maskedid,
                        "eye": eye,
                        "vf_number": vf_number,
                        "pdf_filename": pdf_filename,
                        "opv_filename": row.get("opv_filename", ""),
                        "aeexamdate_shift": row.get("aeexamdate_shift", ""),
                        "specialist_name": username,
                        "last_updated": datetime.now().isoformat(),
                        "data_source": data_source
                    })
                    st.session_state[f"labels_{vf_key}"] = labels

                    if idx == 0 and len(vf_numbers) > 1:
                        targets = [vf for vf in vf_numbers if vf != vf_number]
                        ui.show_copy_labels_button(maskedid, eye, vf_number, targets, df_patient)

    # Buttons
    st.markdown("---")
    save, flag, next_btn = ui.show_save_buttons()

    if save or next_btn:
        saved_count = 0
        for _, row in df_patient.iterrows():
            vf_number = int(row["visual_field_number"])
            key = f"{maskedid}_{row['eye']}_{vf_number}"
            labels = st.session_state.get(f"labels_{key}", {})
            if labels:
                if dl.save_labels(username, maskedid, row["eye"], vf_number, labels):
                    saved_count += 1

        if saved_count > 0:
            ui.show_success_message(f"Saved {saved_count} field(s).")
            if tracker.check_patient_completion(username, maskedid, df_patient):
                if tracker.mark_patient_completed(username, maskedid):
                    update_local_progress(username, maskedid)
                    st.success(f"Patient {maskedid} completed!")

                    available_patients = tracker.get_available_patients(username, all_patients)
                    if not available_patients:
                        st.balloons()
                        st.success("ALL PATIENTS COMPLETED!")
                        return
        else:
            ui.show_error_message("No labels were saved.")

        if next_btn:
            available_patients = tracker.get_available_patients(username, all_patients)
            if available_patients:
                st.session_state["current_patient_idx"] = (patient_idx + 1) % len(available_patients)

                # --- dispara preload ---
                next_idx = (patient_idx + 1) % len(available_patients)
                if next_idx < len(available_patients):
                    nxt = available_patients[next_idx]
                    if nxt not in st.session_state["preloaded_patients"]:
                        threading.Thread(
                            target=preload_patient,
                            args=(nxt, df, st.session_state["preloaded_patients"]),
                            daemon=True,
                        ).start()
            st.rerun()

    if flag:
        ui.show_warning_message("Case flagged for review.")
        # TODO: implement flag save


if __name__ == "__main__":
    labeling_page()
