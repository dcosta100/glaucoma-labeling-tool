# ─────────────────────────────────────────────────────────────────────────────
# Visual Field Grading Interface — Labeling page : Last update September 10, 2025
# ─────────────────────────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime

from utils.dataloader import DataLoader
from utils.ui_components import UIComponents
from utils.config import CSV_PATH, PDF_DIR 
from utils.image_handler import pdf_to_image_fitz
from utils.patient_tracker import PatientTracker


def labeling_page():
    """Main labeling page function - called after successful authentication"""
    
    # Load database
    try:
        df = pd.read_csv(CSV_PATH)
    except FileNotFoundError:
        st.error(f"Database file not found: {CSV_PATH}")
        st.stop()
    except Exception as e:
        st.error(f"Error loading database: {e}")
        st.stop()

    # Get current username
    username = st.session_state.get('specialist_name', 'unknown')
    
    # Get all patients from database
    all_patients = df["maskedid"].unique().tolist()
    
    # Initialize patient tracker
    tracker = PatientTracker()
    
    # Auto-detect completed patients for this user
    newly_completed = tracker.auto_mark_completed_patients(username, all_patients, df)
    if newly_completed:
        st.sidebar.success(f"✅ Found {len(newly_completed)} already completed patients")
    
    # Get only patients not yet completed by this user
    available_patients = tracker.get_available_patients(username, all_patients)
    
    if not available_patients:
        st.success("🎉 **Congratulations!** You have completed labeling for all patients!")
        st.info(f"Total patients completed: {len(all_patients)}")
        
        # Show completion stats
        stats = tracker.get_user_stats(username, len(all_patients))
        st.metric("Completion Rate", f"{stats['completion_percentage']:.1f}%")
        
        # Option to reset progress (for admins)
        if st.button("🔄 Reset Progress (Admin Only)", help="This will reset all your progress!"):
            if st.checkbox("I confirm I want to reset ALL my progress"):
                tracker.reset_user_progress(username)
                st.success("Progress reset! Refresh the page.")
                st.rerun()
        return
    
    # Show progress in sidebar
    stats = tracker.get_user_stats(username, len(all_patients))
    with st.sidebar:
        st.markdown("### 📊 Your Progress")
        st.metric("Completed", stats['completed_count'])
        st.metric("Remaining", stats['remaining_count']) 
        st.progress(stats['completion_percentage'] / 100)
        st.caption(f"{stats['completion_percentage']:.1f}% Complete")
        
        if stats['last_patient']:
            st.caption(f"Last: {stats['last_patient']}")

    # Track current patient index within available patients
    if "current_patient_idx" not in st.session_state:
        st.session_state["current_patient_idx"] = 0

    patient_idx = st.session_state["current_patient_idx"]
    
    # Ensure patient index is within bounds of available patients
    if patient_idx >= len(available_patients):
        st.session_state["current_patient_idx"] = 0
        patient_idx = 0
    
    maskedid = available_patients[patient_idx]

    # Filter patient rows
    df_patient = df[df["maskedid"] == maskedid]
    age = df_patient["age"].dropna().iloc[0] if not df_patient["age"].isnull().all() else "Unknown"

    # Init helpers
    ui = UIComponents()
    dl = DataLoader()

    # --- HEADER ---
    ui.show_top_header(maskedid, age)
    
    # Show navigation info
    st.markdown(f"**Patient {patient_idx + 1} of {len(available_patients)} remaining** | Specialist: {username}")
    st.markdown("---")

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
                    pdf_path = Path(PDF_DIR) / row["pdf_filename"]

                    ui.label_section_title(eye, vf_number)

                    # Show PDF as image
                    try:
                        image = pdf_to_image_fitz(str(pdf_path))
                        if image:
                            st.image(image, use_container_width=True)
                        else:
                            st.warning(f"Could not render PDF: {pdf_path}")
                    except Exception as e:
                        st.error(f"Error loading PDF {pdf_path}: {e}")

                    # Load previous labels if any (específicos do usuário)
                    defaults = dl.load_labels(username, maskedid, eye, vf_number)

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
    st.markdown("---")
    save, flag, next_btn = ui.show_save_buttons()

    if save or next_btn:
        # Save all fields of current patient
        saved_count = 0
        for _, row in df_patient.iterrows():
            vf_number = int(row["visual_field_number"])
            key = f"{maskedid}_{row['eye']}_{vf_number}"
            labels = st.session_state.get(f"labels_{key}", {})
            if labels:
                if dl.save_labels(username, maskedid, row["eye"], vf_number, labels):
                    saved_count += 1

        if saved_count > 0:
            ui.show_success_message(f"✅ Labels saved successfully for {saved_count} field(s).")
            
            # Check if patient is now complete
            if tracker.check_patient_completion(username, maskedid, df_patient):
                # Mark patient as completed
                if tracker.mark_patient_completed(username, maskedid):
                    st.success(f"🎉 Patient {maskedid} completed!")
                    
                    # Update available patients list
                    available_patients = tracker.get_available_patients(username, all_patients)
                    
                    if not available_patients:
                        st.balloons()
                        st.success("🏆 **ALL PATIENTS COMPLETED!** Great work!")
                        return
        else:
            ui.show_error_message("❌ No labels were saved.")

        if next_btn:
            # Move to next available patient
            available_patients = tracker.get_available_patients(username, all_patients)
            if available_patients:
                st.session_state["current_patient_idx"] = (patient_idx + 1) % len(available_patients)
            st.rerun()

    if flag:
        ui.show_warning_message("⚠️ Case flagged for review.")
        # Here you could add logic to save a flag file or mark in database


if __name__ == "__main__":
    labeling_page()