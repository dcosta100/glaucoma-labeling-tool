# ─────────────────────────────────────────────────────────────────────────────
# Glaucoma Progression Interface — Labeling page : Last update September 1, 2025
# ─────────────────────────────────────────────────────────────────────────────
import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import json

from utils.config import VF_IMAGES_DIR, OCT_IMAGES_DIR, DATABASE_PATH
from utils import dataloader
from utils.cache_manager import CacheManager
from utils.image_handler import ImageHandler
from utils.ui_components import UIComponents

from icecream import ic


def initialize_session_state():
    """Initialize session state variables"""
    if 'database' not in st.session_state:
        st.session_state['database'] = pd.read_csv(DATABASE_PATH)
    
    if 'patient_defaults' not in st.session_state:
        st.session_state['patient_defaults'] = {}


def load_patient_data():
    """Load and return patient data from database"""
    df_patients = st.session_state['database']
    
    # Get unique patients with their info
    patients = {}
    for _, row in df_patients.iterrows():
        patient_id = row['Patient']
        if patient_id not in patients:
            patients[patient_id] = {
                "Sex": row['Sex'], 
                "Age": row['Age']
            }
    
    return df_patients, patients


def handle_patient_selection(selected, cache_manager, dl):
    """Handle patient selection and data loading"""
    patient_changed = st.session_state.get('selected_patient', None) != selected
    
    if patient_changed:
        # Load patient data (from cache if available)
        image_data, previous_saved = cache_manager.get_cached_patient_data(selected, dl)
        
        # Show cache status
        is_cached = str(selected) in st.session_state['patient_cache']
        if is_cached:
            st.info(f"📁 Loaded patient {selected} from cache")
        else:
            st.info(f"🔄 Loading patient {selected} data...")
        
        # Initialize defaults for this patient
        patient_defaults = {
            'vf_od': None, 'oct_od': None, 'vf_os': None, 'oct_os': None,
            'd1_vf_od': None, 'd2_vf_od': None, 'd1_vf_os': None, 'd2_vf_os': None,
            'd1_oct_od': None, 'd2_oct_od': None, 'd1_oct_os': None, 'd2_oct_os': None
        }
        
        # Update defaults based on previous saved data
        if previous_saved and "labels" in previous_saved:
            for key in ["vf_od", "oct_od", "vf_os", "oct_os"]:
                label = previous_saved["labels"].get(key, {})
                status = label.get("status", None)
                date1 = label.get("date1", None)
                date2 = label.get("date2", None)
                
                # Set the actual status string (not index)
                if status in ["Progressed", "Not Progressed"]:
                    patient_defaults[key] = status
                else:
                    patient_defaults[key] = None
                    
                # Set dates if they exist and are valid
                if date1 and date1 != "N/A" and date1 != "":
                    try:
                        patient_defaults[f'd1_{key}'] = datetime.strptime(date1, "%Y-%m-%d").date()
                    except:
                        patient_defaults[f'd1_{key}'] = None
                        
                if date2 and date2 != "N/A" and date2 != "":
                    try:
                        patient_defaults[f'd2_{key}'] = datetime.strptime(date2, "%Y-%m-%d").date()
                    except:
                        patient_defaults[f'd2_{key}'] = None
        
        # Store patient-specific defaults
        st.session_state['patient_defaults'][selected] = patient_defaults
        
        # Clear any existing widget states for the new patient to force refresh
        keys_to_clear = []
        for key in st.session_state.keys():
            if key.startswith(('diag_', 'd1_', 'd2_')):
                keys_to_clear.append(key)
        for key in keys_to_clear:
            del st.session_state[key]
        
    st.session_state['selected_patient'] = selected


def create_md_chart(df_patient, eye_label):
    """Create MD trend chart for given eye"""
    # Sort by timepoint and ensure we have valid data
    df_patient = df_patient.sort_values("Timepoint").copy()
    
    # Get the correct column name for the eye
    if eye_label == "OD":
        md_column = "OD_vf"
    else:
        md_column = "OS_vf"
    
    # Filter out any rows with missing MD values
    df_patient = df_patient.dropna(subset=[md_column])
    
    if len(df_patient) == 0:
        # Return empty chart if no data
        fig = go.Figure()
        fig.add_annotation(
            text=f"No {eye_label} visual field data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle'
        )
        fig.update_layout(
            xaxis_title="Date", yaxis_title="MD (dB)",
            template="plotly_white"
        )
        return fig
    
    # Use actual timepoints if they're datetime, otherwise create a range
    if pd.api.types.is_datetime64_any_dtype(df_patient['Timepoint']):
        dates = df_patient['Timepoint'].tolist()
    else:
        # Create date range based on number of timepoints
        dates = pd.date_range(
            start='2016-01-01', 
            end='2025-04-30', 
            periods=len(df_patient)
        ).tolist()
    
    # Get MD values
    md_values = df_patient[md_column].astype(float).tolist()

    # Create dataframe for plotting
    md_data = pd.DataFrame({
        "Date": dates,
        f"{eye_label} MD (dB)": md_values
    })

    # Calculate trend line
    if len(md_data) > 1:
        years = (md_data["Date"] - md_data["Date"].iloc[0]).dt.days / 365.25
        slope, intercept = np.polyfit(years, md_data[f"{eye_label} MD (dB)"], 1)
        trend_y = slope * years + intercept
    else:
        slope = 0
        trend_y = md_values

    # Create plot
    fig = go.Figure()
    
    # Add data points
    fig.add_trace(go.Scatter(
        x=md_data["Date"], 
        y=md_data[f"{eye_label} MD (dB)"],
        mode="lines+markers", 
        name=f"{eye_label} MD",
        hovertemplate=f"Date: %{{x|%Y-%m-%d}}<br>{eye_label} MD: %{{y:.2f}} dB<extra></extra>"
    ))
    
    # Add trend line if we have multiple points
    if len(md_data) > 1:
        fig.add_trace(go.Scatter(
            x=md_data["Date"], 
            y=trend_y,
            mode="lines", 
            line=dict(dash="dash", color="orange"),
            name=f"{eye_label} slope: {slope:.2f} dB/yr",
            hovertemplate=f"Trend: %{{y:.2f}} dB<extra></extra>"
        ))
    
    fig.update_layout(
        xaxis_title="Date", 
        yaxis_title="MD (dB)",
        hovermode="x unified", 
        template="plotly_white",
        showlegend=True
    )
    
    return fig


def save_labels_data(selected, timestamp, dl, cache_manager):
    """Save labels data and update cache"""
    labels = {
        "timestamp": timestamp,
        "specialist": st.session_state.get("specialist_name", ""),
        "patient": selected,
        "labels": {
            "vf_od": {
                "status": st.session_state.get("diag_vf_od", ""),
                "date1": str(st.session_state.get("d1_vf_od", "")),
                "date2": str(st.session_state.get("d2_vf_od", "")),
            },
            "oct_od": {
                "status": st.session_state.get("diag_oct_od", ""),
                "date1": str(st.session_state.get("d1_oct_od", "")),
                "date2": str(st.session_state.get("d2_oct_od", "")),
            },
            "vf_os": {
                "status": st.session_state.get("diag_vf_os", ""),
                "date1": str(st.session_state.get("d1_vf_os", "")),
                "date2": str(st.session_state.get("d2_vf_os", "")),
            },
            "oct_os": {
                "status": st.session_state.get("diag_oct_os", ""),
                "date1": str(st.session_state.get("d1_oct_os", "")),
                "date2": str(st.session_state.get("d2_oct_os", "")),
            },
        }
    }
    
    # Save json to labels directory
    success = dl.save_labels(selected, st.session_state.get("specialist_name", ""), labels)
    
    # Update the patient defaults after saving
    st.session_state['patient_defaults'][selected] = {
        'vf_od': st.session_state.get("diag_vf_od", ""),
        'oct_od': st.session_state.get("diag_oct_od", ""),
        'vf_os': st.session_state.get("diag_vf_os", ""),
        'oct_os': st.session_state.get("diag_oct_os", ""),
        'd1_vf_od': st.session_state.get("d1_vf_od", None),
        'd2_vf_od': st.session_state.get("d2_vf_od", None),
        'd1_vf_os': st.session_state.get("d1_vf_os", None),
        'd2_vf_os': st.session_state.get("d2_vf_os", None),
        'd1_oct_od': st.session_state.get("d1_oct_od", None),
        'd2_oct_od': st.session_state.get("d2_oct_od", None),
        'd1_oct_os': st.session_state.get("d1_oct_os", None),
        'd2_oct_os': st.session_state.get("d2_oct_os", None),
    }
    
    # Update labels cache with new data
    cache_manager.update_labels_cache(selected, labels)
    
    return labels


def labeling_page():
    st.set_page_config(
        page_title="Glaucoma Progression Interface - Labeling", 
        layout="wide", 
        initial_sidebar_state="expanded"
    )

    # Initialize components
    initialize_session_state()
    dl = dataloader.DataLoader(labels_dir="labels")
    
    # Initialize ImageHandler with DataFrame and set it in CacheManager
    image_handler = ImageHandler(df=st.session_state['database'], data_dir=VF_IMAGES_DIR)
    cache_manager = CacheManager()
    cache_manager.set_image_handler(image_handler)
    
    ui_components = UIComponents()
    timestamp = datetime.now().strftime("%Y-%m-%d, %H:%M:%S")

    # Setup UI
    ui_components.setup_page_style()
    ui_components.show_welcome_message()
    ui_components.show_user_info()
    ui_components.show_header()

    # Load patient data
    df_patients, patients = load_patient_data()
    
    # Sidebar patient selection
    selected = ui_components.show_patient_sidebar(patients, cache_manager)
    
    # Handle patient selection and data loading
    handle_patient_selection(selected, cache_manager, dl)

    # Load images from cache or fresh
    cache_key = str(selected)
    if cache_key in st.session_state['image_cache']:
        image_data = st.session_state['image_cache'][cache_key]
        vf_od = image_data['vf_od']
        vf_os = image_data['vf_os']
        oct_od = image_data['oct_od']
        oct_os = image_data['oct_os']
        
    else:
        # This shouldn't happen since we cache above, but fallback
        vf_od = image_handler.get_eye_images(VF_IMAGES_DIR, "VF", selected, "OD")
        vf_os = image_handler.get_eye_images(VF_IMAGES_DIR, "VF", selected, "OS")
        oct_od = image_handler.get_eye_images(OCT_IMAGES_DIR, "OCT", selected, "OD")
        oct_os = image_handler.get_eye_images(OCT_IMAGES_DIR, "OCT", selected, "OS")

    # Get patient data for charts
    df_patient = df_patients[df_patients["Patient"] == selected]

    # Right Eye Section
    with st.expander("Right Eye (OD)", expanded=False):
        c1, c2 = st.columns(2)

        with c1:
            st.subheader("VF Printouts (OD)")
            image_handler.display_scrollable_images(vf_od)

            # MD Trend for OD
            with st.expander("Mean Deviation Trend (OD)", expanded=False):
                fig_od = create_md_chart(df_patient, "OD")
                st.plotly_chart(fig_od, use_container_width=True)

            # Evaluation for OD VF
            d_vf_od, d1_vf_od, d2_vf_od = ui_components.eval_section("vf_od", selected)

        with c2:
            st.subheader("OCT Printouts (OD)")
            image_handler.display_scrollable_images(oct_od)
            d_oct_od, d1_oct_od, d2_oct_od = ui_components.eval_section("oct_od", selected)

    # Left Eye Section
    with st.expander("Left Eye (OS)", expanded=False):
        c1, c2 = st.columns(2)

        with c1:
            st.subheader("VF Printouts (OS)")
            image_handler.display_scrollable_images(vf_os)

            # MD Trend for OS
            with st.expander("Mean Deviation Trend (OS)", expanded=False):
                fig_os = create_md_chart(df_patient, "OS")
                st.plotly_chart(fig_os, use_container_width=True)

            # Evaluation for OS VF
            d_vf_os, d1_vf_os, d2_vf_os = ui_components.eval_section("vf_os", selected)

        with c2:
            st.subheader("OCT Printouts (OS)")
            image_handler.display_scrollable_images(oct_os)
            d_oct_os, d1_oct_os, d2_oct_os = ui_components.eval_section("oct_os", selected)
            
    # Save Labels Section
    if st.button("Save Labels", use_container_width=True):
        labels = save_labels_data(selected, timestamp, dl, cache_manager)
        json_str = json.dumps(labels, indent=4, default=str)
        
        st.download_button(
            label="Download Labels as JSON",
            data=json_str,
            file_name=f"{selected}_labels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
        st.success("Labels saved! Download your JSON file.")

    # Cache management
    ui_components.show_cache_management(cache_manager)

    st.markdown("---")
    st.write("Glaucoma and Data Science Laboratory | Bascom Palmer Eye Institute")


if __name__ == "__main__":
    labeling_page()