"""
UI Components for Glaucoma Progression Interface
Handles user interface elements and interactions
"""

import streamlit as st
from datetime import datetime


class UIComponents:
    """Handles UI components and interactions for the labeling interface"""
    
    def __init__(self):
        pass
    
    def setup_page_style(self):
        """Setup page styling and CSS"""
        st.markdown(
            """
            <style>
                .scrollable-box{
                    height:450px; 
                    overflow-y:scroll; 
                    padding-right:10px;
                    border:1px solid #ddd;
                }
                .cache-info {
                    background-color: #f0f2f6;
                    padding: 5px 10px;
                    border-radius: 5px;
                    font-size: 12px;
                    margin-bottom: 10px;
                }
                .patient-info {
                    background-color: #f8f9fa;
                    padding: 10px;
                    border-radius: 5px;
                    margin-bottom: 10px;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )
    
    def show_welcome_message(self):
        """Show welcome message if needed"""
        if st.session_state.get("show_welcome", False):
            st.success(f"Welcome, Dr. {st.session_state.specialist_name}!")
            st.session_state.show_welcome = False
    
    def show_user_info(self):
        """Display logged in user information"""
        specialist_name = st.session_state.get("specialist_name", "Unknown")
        st.markdown(
            f"<p style='text-align:right; color:gray;'>Logged in as: "
            f"<strong>Dr. {specialist_name}</strong></p>",
            unsafe_allow_html=True,
        )
    
    def show_header(self):
        """Display page header"""
        st.markdown(
            """
            <h1 style='text-align:center;'>Glaucoma Progression Interface</h1>
            <p style='text-align:center; font-size:18px; color:gray;'>
                A Collaborative Platform for Glaucoma Specialists
            </p>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("---")
    
    def show_patient_sidebar(self, patients, cache_manager):
        """Display patient selection sidebar"""
        selected = st.sidebar.selectbox("Select Patient", list(patients.keys()))
        
        # Display cache status in sidebar
        cached_patients = cache_manager.get_recently_cached_patients()
        if cached_patients:
            st.sidebar.markdown("---")
            st.sidebar.markdown("**Recently Loaded Patients:**")
            st.sidebar.markdown(
                f"<div class='cache-info'>📁 {cached_patients}</div>", 
                unsafe_allow_html=True
            )
        
        if selected:
            st.sidebar.markdown("---")
            st.sidebar.subheader(f"Patient Information: {selected}")
            for key, value in patients[selected].items():
                st.sidebar.write(f"{key}: {value}")
        
        return selected
    
    def eval_section(self, key, selected_patient):
        """Create evaluation section for progression status"""
        st.markdown("##### Specialist Evaluation")
        
        # Get patient-specific defaults
        patient_defaults = st.session_state['patient_defaults'].get(selected_patient, {})
        default_status = patient_defaults.get(key, None)
        
        # Convert status to index for radio button
        default_index = None
        if default_status == "Progressed":
            default_index = 0
        elif default_status == "Not Progressed":
            default_index = 1
            
        stat = st.radio(
            "Progression status:", 
            ["Progressed", "Not Progressed"], 
            key=f"diag_{key}", 
            index=default_index
        )
        
        if stat == "Progressed":
            d1, d2 = st.columns(2)
            with d1:
                default_date1 = patient_defaults.get(f"d1_{key}", None)
                date1 = st.date_input(
                    "First date progression seen:", 
                    key=f"d1_{key}", 
                    value=default_date1 if default_date1 else "today"
                )
            with d2:
                default_date2 = patient_defaults.get(f"d2_{key}", None)
                date2 = st.date_input(
                    "Second date progression seen:", 
                    key=f"d2_{key}", 
                    value=default_date2 if default_date2 else "today"
                )
        else:
            date1 = date2 = "N/A"
            st.write("First date progression seen: N/A")
            st.write("Second date progression seen: N/A")
        
        return stat, date1, date2
    
    def show_cache_management(self, cache_manager):
        """Display cache management controls and statistics"""
        # Cache management button
        if st.sidebar.button("🗑️ Clear Cache"):
            cache_manager.clear_cache()
            st.success("Cache cleared successfully!")
            st.rerun()

        # Display cache statistics in sidebar
        cache_stats = cache_manager.get_cache_statistics()
        
        if st.sidebar.expander("Cache Statistics", expanded=False):
            st.sidebar.write(f"Cached patients: {cache_stats['patients_cached']}/{cache_stats['max_cache_size']}")
            st.sidebar.write(f"Images cached: {cache_stats['images_cached']}")
            st.sidebar.write(f"Labels cached: {cache_stats['labels_cached']}")
            
            if cache_stats['cache_order']:
                st.sidebar.write("**Cache order (oldest → newest):**")
                current_patient = st.session_state.get('selected_patient', None)
                
                for i, patient in enumerate(cache_stats['cache_order'], 1):
                    status = "🟢" if patient == current_patient else "⚪"
                    st.sidebar.write(f"{i}. {status} {patient}")
    
    def show_patient_info_card(self, patient_id, patient_data):
        """Display patient information in a card format"""
        with st.container():
            st.markdown(f"**Patient ID:** {patient_id}")
            for key, value in patient_data.items():
                st.markdown(f"**{key}:** {value}")
    
    def show_loading_indicator(self, message="Loading..."):
        """Show loading indicator"""
        with st.spinner(message):
            pass
    
    def show_success_message(self, message):
        """Show success message"""
        st.success(message)
    
    def show_error_message(self, message):
        """Show error message"""
        st.error(message)
    
    def show_info_message(self, message):
        """Show info message"""
        st.info(message)
    
    def show_warning_message(self, message):
        """Show warning message"""
        st.warning(message)
    
    def create_download_button(self, data, filename, label="Download", mime_type="application/json"):
        """Create download button for data"""
        return st.download_button(
            label=label,
            data=data,
            file_name=filename,
            mime=mime_type
        )
    
    def create_save_button(self, label="Save Labels", use_container_width=True):
        """Create save button"""
        return st.button(label, use_container_width=use_container_width)
    
    def show_footer(self):
        """Display page footer"""
        st.markdown("---")
        st.write("Glaucoma and Data Science Laboratory | Bascom Palmer Eye Institute")
    
    def create_two_column_layout(self):
        """Create two-column layout"""
        return st.columns(2)
    
    def create_expander(self, title, expanded=False):
        """Create expander section"""
        return st.expander(title, expanded=expanded)
    
    def show_subheader(self, text):
        """Show subheader"""
        st.subheader(text)
    
    def display_plotly_chart(self, figure, use_container_width=True):
        """Display plotly chart"""
        st.plotly_chart(figure, use_container_width=use_container_width)