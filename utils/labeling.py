# ─────────────────────────────────────────────────────────────────────────────
# Visual Field Grading Interface — Labeling page : Last update December 20, 2024
# ─────────────────────────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import os
import tempfile
from pathlib import Path
from datetime import datetime

from utils.dataloader import DataLoader
from utils.ui_components import UIComponents
from utils.image_handler import pdf_to_image_fitz
from utils.patient_tracker import PatientTracker


def labeling_page():
    """
    Main labeling page function - called after successful authentication
    Handles the complete visual field labeling workflow with cloud integration
    """
    
    # Get current authenticated username
    username = st.session_state.get('specialist_name', 'unknown')

    st.write(f"GOOGLE_AVAILABLE: {dl.GOOGLE_AVAILABLE if hasattr(dl, 'GOOGLE_AVAILABLE') else 'Not found'}")
    st.write(f"Has secrets: {hasattr(st, 'secrets')}")
    if hasattr(st, 'secrets'):
        st.write(f"Secrets keys: {list(st.secrets.keys())}")
        if 'google_drive' in st.secrets:
            st.write("google_drive section found")
        else:
            st.write("google_drive section NOT found")

    service = dl._get_drive_service()
    st.write(f"Drive service created: {service is not None}")
    st.write("==================")
    
    # Initialize data loader for cloud/local operations
    dl = DataLoader()
    
    # Load database - try Google Drive first, fallback to local
    df = None
    data_source = None
    
    # Attempt to load CSV from Google Drive
    with st.spinner("Loading database from cloud..."):
        df = dl.get_csv_from_drive("opv_24-2_prepared.csv")
        if df is not None:
            data_source = "cloud"
            st.success("Database loaded from Google Drive")
    
    # Fallback to local CSV if cloud fails
    if df is None:
        try:
            # Try to load from local config path
            from utils.config import CSV_PATH
            if os.path.exists(CSV_PATH):
                df = pd.read_csv(CSV_PATH)
                data_source = "local"
                st.info("Using local database file")
            else:
                st.error("Database file not found in cloud or locally")
                st.error("Please ensure CSV file is uploaded to Google Drive or available locally")
                st.stop()
        except Exception as e:
            st.error(f"Error loading database: {e}")
            st.stop()
    
    # Validate dataframe structure
    required_columns = ["maskedid", "eye", "visual_field_number", "pdf_filename", "age"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(f"Database missing required columns: {missing_columns}")
        st.stop()

    # Get all unique patients from database
    all_patients = df["maskedid"].unique().tolist()
    
    if not all_patients:
        st.error("No patients found in database")
        st.stop()
    
    # Initialize patient progress tracker
    tracker = PatientTracker()
    
    # Auto-detect patients already completed by this user
    # This scans existing label files and marks patients as complete
    newly_completed = tracker.auto_mark_completed_patients(username, all_patients, df)
    if newly_completed:
        st.sidebar.success(f"Found {len(newly_completed)} already completed patients")
    
    # Get list of patients not yet completed by this user
    available_patients = tracker.get_available_patients(username, all_patients)
    
    # Handle case where user has completed all patients
    if not available_patients:
        st.success("Congratulations! You have completed labeling for all patients!")
        st.info(f"Total patients completed: {len(all_patients)}")
        
        # Show completion statistics
        stats = tracker.get_user_stats(username, len(all_patients))
        st.metric("Completion Rate", f"{stats['completion_percentage']:.1f}%")
        
        # Admin option to reset progress
        if st.button("Reset Progress (Admin Only)", help="This will reset all your progress!"):
            if st.checkbox("I confirm I want to reset ALL my progress"):
                tracker.reset_user_progress(username)
                st.success("Progress reset! Refresh the page.")
                st.rerun()
        return
    
    # Display user progress in sidebar
    stats = tracker.get_user_stats(username, len(all_patients))
    with st.sidebar:
        st.markdown("### Your Progress")
        st.metric("Completed", stats['completed_count'])
        st.metric("Remaining", stats['remaining_count']) 
        st.progress(stats['completion_percentage'] / 100)
        st.caption(f"{stats['completion_percentage']:.1f}% Complete")
        
        if stats['last_patient']:
            st.caption(f"Last completed: {stats['last_patient']}")
        
        # Show data source information
        st.markdown("---")
        st.caption(f"Data source: {data_source}")

    # Track current patient index within available patients
    if "current_patient_idx" not in st.session_state:
        st.session_state["current_patient_idx"] = 0

    patient_idx = st.session_state["current_patient_idx"]
    
    # Ensure patient index is within bounds of available patients
    if patient_idx >= len(available_patients):
        st.session_state["current_patient_idx"] = 0
        patient_idx = 0
    
    # Get current patient ID
    maskedid = available_patients[patient_idx]

    # Filter database for current patient
    df_patient = df[df["maskedid"] == maskedid]
    
    # Extract patient age (handle missing values)
    age = df_patient["age"].dropna().iloc[0] if not df_patient["age"].isnull().all() else "Unknown"

    # Initialize UI components helper
    ui = UIComponents()

    # Display patient header with ID and age
    ui.show_top_header(maskedid, age)
    
    # Show navigation information
    st.markdown(f"**Patient {patient_idx + 1} of {len(available_patients)} remaining** | Specialist: {username}")
    st.markdown("---")

    # Create two-column layout for right eye (R) and left eye (L)
    col_r, col_l = ui.create_dual_column_layout()

    # Process each eye separately
    for eye, col in zip(["R", "L"], [col_r, col_l]):
        # Filter data for current eye and sort by visual field number
        eye_df = df_patient[df_patient["eye"] == eye].sort_values("visual_field_number")

        with col:
            if eye_df.empty:
                # No visual field tests available for this eye
                ui.no_fields_warning(eye)
            else:
                # Get all visual field numbers for this eye
                vf_numbers = sorted(eye_df["visual_field_number"].astype(int).tolist())
                
                # Process each visual field test for this eye
                for idx, (_, row) in enumerate(eye_df.iterrows()):
                    vf_number = int(row["visual_field_number"])
                    vf_key = f"{maskedid}_{eye}_{vf_number}"
                    pdf_filename = row["pdf_filename"]

                    # Display section title for this visual field
                    ui.label_section_title(eye, vf_number)

                    # Load and display PDF from cloud or local storage
                    try:
                        pdf_displayed = False
                        
                        # Try to load PDF from Google Drive
                        if data_source == "cloud":
                            with st.spinner(f"Loading PDF from cloud: {pdf_filename}"):
                                pdf_content = dl.get_pdf_from_drive(pdf_filename)
                                
                                if pdf_content:
                                    # Create temporary file for PDF processing
                                    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_pdf:
                                        tmp_pdf.write(pdf_content.getvalue())
                                        tmp_pdf_path = tmp_pdf.name
                                    
                                    try:
                                        # Convert PDF to image for display
                                        image = pdf_to_image_fitz(tmp_pdf_path)
                                        if image:
                                            st.image(image, use_container_width=True)
                                            pdf_displayed = True
                                        else:
                                            st.warning(f"Could not render PDF: {pdf_filename}")
                                    finally:
                                        # Clean up temporary file
                                        os.unlink(tmp_pdf_path)
                                else:
                                    st.error(f"Could not load PDF from cloud: {pdf_filename}")
                        
                        # Fallback to local PDF if cloud fails or not available
                        if not pdf_displayed:
                            from utils.config import PDF_DIR
                            local_pdf_path = Path(PDF_DIR) / pdf_filename
                            
                            if local_pdf_path.exists():
                                image = pdf_to_image_fitz(str(local_pdf_path))
                                if image:
                                    st.image(image, use_container_width=True)
                                    pdf_displayed = True
                                else:
                                    st.warning(f"Could not render local PDF: {local_pdf_path}")
                            else:
                                st.error(f"PDF not found in cloud or locally: {pdf_filename}")
                        
                    except Exception as e:
                        st.error(f"Error loading PDF {pdf_filename}: {e}")

                    # Load any existing labels for this visual field
                    defaults = dl.load_labels(username, maskedid, eye, vf_number)

                    # Render the labeling form with current/default values
                    labels = ui.render_labels_for_field(vf_key, defaults)
                    
                    # Add metadata to labels
                    labels.update({
                        "maskedid": maskedid,
                        "eye": eye,
                        "vf_number": vf_number,
                        "pdf_filename": pdf_filename,
                        "specialist_name": username,
                        "last_updated": datetime.now().isoformat(),
                        "data_source": data_source
                    })

                    # Store labels in session state for saving
                    st.session_state[f"labels_{vf_key}"] = labels

                    # Show copy labels button for first field if multiple fields exist
                    if idx == 0 and len(vf_numbers) > 1:
                        # Get target fields (all except current one)
                        target_vfs = [vf for vf in vf_numbers if vf != vf_number]
                        ui.show_copy_labels_button(maskedid, eye, vf_number, target_vfs, df_patient)

    # Display action buttons at bottom
    st.markdown("---")
    save, flag, next_btn = ui.show_save_buttons()

    # Handle save button clicks
    if save or next_btn:
        saved_count = 0
        
        # Save labels for all visual fields of current patient
        for _, row in df_patient.iterrows():
            vf_number = int(row["visual_field_number"])
            key = f"{maskedid}_{row['eye']}_{vf_number}"
            labels = st.session_state.get(f"labels_{key}", {})
            
            if labels:
                if dl.save_labels(username, maskedid, row["eye"], vf_number, labels):
                    saved_count += 1

        # Provide feedback on save operation
        if saved_count > 0:
            ui.show_success_message(f"Labels saved successfully for {saved_count} field(s).")
            
            # Check if patient is now completely labeled
            if tracker.check_patient_completion(username, maskedid, df_patient):
                # Mark patient as completed
                if tracker.mark_patient_completed(username, maskedid):
                    st.success(f"Patient {maskedid} completed!")
                    
                    # Update available patients list
                    available_patients = tracker.get_available_patients(username, all_patients)
                    
                    # Check if all patients are now complete
                    if not available_patients:
                        st.balloons()
                        st.success("ALL PATIENTS COMPLETED! Excellent work!")
                        return
        else:
            ui.show_error_message("No labels were saved.")

        # Handle next patient button
        if next_btn:
            # Move to next available patient (circular)
            available_patients = tracker.get_available_patients(username, all_patients)
            if available_patients:
                st.session_state["current_patient_idx"] = (patient_idx + 1) % len(available_patients)
            st.rerun()

    # Handle flag button
    if flag:
        ui.show_warning_message("Case flagged for review.")
        # TODO: Implement flagging system (save flag file, database entry, etc.)


if __name__ == "__main__":
    labeling_page()