"""
Image Handler for Glaucoma Progression Interface
Handles image loading, processing, and display functionality from DataFrame
"""

import streamlit as st
import pandas as pd
import base64
import os
from utils.config import EXTS
from icecream import ic


class ImageHandler:
    """Handles image operations for the labeling interface"""
    
    def __init__(self, df=None, data_dir="./data/"):
        """
        Initialize ImageHandler with DataFrame and data directory
        
        Args:
            df: DataFrame containing patient data and filenames
            data_dir: Base directory where image files are stored
        """
        self.df = df
        self.data_dir = data_dir
    
    def set_dataframe(self, df):
        """Set or update the DataFrame"""
        self.df = df
    
    def get_patient_data(self, patient_id, timepoint=None):
        """Get patient data from DataFrame"""
        if self.df is None:
            return None
            
        # Filter by patient ID
        patient_data = self.df[self.df['Patient'] == patient_id]
        
        # If timepoint specified, filter by timepoint
        if timepoint is not None:
            patient_data = patient_data[patient_data['Timepoint'] == timepoint]
        
        return patient_data if not patient_data.empty else None
    
    def get_eye_images(self, patient_id, modality, eye, timepoint=None):
        """
        Get list of image files for specific eye and modality from DataFrame
        
        Args:
            patient_id: Patient identifier
            modality: 'vf' for visual field or 'oct' for OCT
            eye: 'OS' or 'OD'
            timepoint: Optional timepoint filter
            
        Returns:
            List of full file paths
        """  
        # ic(patient_id, modality, eye, timepoint)  # Debug inputs
        
        
        patient_data = self.get_patient_data(patient_id, timepoint)

        if patient_data is None:
            return []
        
        # Construct column name based on modality and eye
        filename_col = f"filename_{modality.lower()}_{eye}"
        # ic(filename_col)
        
        if filename_col not in patient_data.columns:
            return []
        
        image_files = []
        for _, row in patient_data.iterrows():
            filename = row.get(filename_col)
            if pd.notna(filename) and filename:  # Check for non-null, non-empty filename
                full_path = os.path.join(self.data_dir, filename)
                image_files.append(full_path)

        return sorted(image_files)
    
    def get_all_patient_images(self, patient_id, timepoint=None):
        """
        Get all images for a patient across all modalities and eyes
        
        Returns:
            Dictionary with structure: {modality: {eye: [image_paths]}}
        """
        result = {
            'vf': {'OS': [], 'OD': []},
            'oct': {'OS': [], 'OD': []}
        }
        
        for modality in ['vf', 'oct']:
            for eye in ['OS', 'OD']:
                result[modality][eye] = self.get_eye_images(patient_id, modality, eye, timepoint)
        
        return result
    
    def get_patient_timepoints(self, patient_id):
        """Get all available timepoints for a patient"""
        if self.df is None:
            return []
            
        patient_data = self.df[self.df['Patient'] == patient_id]
        if patient_data.empty:
            return []
        
        return sorted(patient_data['Timepoint'].unique().tolist())
    
    def get_all_patients(self):
        """Get list of all unique patients"""
        if self.df is None:
            return []
        
        return sorted(self.df['Patient'].unique().tolist())
    
    def encode_image_to_base64(self, image_path):
        """Encode image file to base64 string"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode()
        except (OSError, IOError, PermissionError):
            return None
    
    def create_image_html(self, image_paths):
        """Create HTML string for displaying multiple images"""
        html = ""
        for image_path in image_paths:
            if os.path.exists(image_path):
                b64_image = self.encode_image_to_base64(image_path)
                if b64_image:
                    # Extract just the filename for display
                    filename = os.path.basename(image_path)
                    html += f"<img src='data:image/png;base64,{b64_image}' style='width:100%; margin-bottom:10px;'/>"
                else:
                    # Show error message for failed image loading
                    filename = os.path.basename(image_path)
                    html += f"<p style='color:red;'>Error loading image: {filename}</p>"
            else:
                # Show message for missing files
                filename = os.path.basename(image_path)
                html += f"<p style='color:orange;'>Image not found: {filename}</p>"
        
        return html
    
    def display_scrollable_images(self, image_paths, height=450, title=None):
        """Display images in a scrollable container"""
        if not image_paths:
            st.write("No images found for this selection.")
            return
        
        if title:
            st.subheader(title)
        
        html_content = self.create_image_html(image_paths)
        
        if html_content:
            st.markdown(
                f"""
                <div class='scrollable-box' style='
                    height:{height}px; 
                    overflow-y:auto; 
                    border:1px solid #ddd; 
                    padding:10px; 
                    border-radius:5px;
                '>
                    {html_content}
                </div>
                """, 
                unsafe_allow_html=True
            )
        else:
            st.write("No valid images could be loaded.")
    
    def get_image_count(self, image_paths):
        """Get count of valid images"""
        if not image_paths:
            return 0
        
        valid_count = 0
        for path in image_paths:
            if os.path.exists(path):
                valid_count += 1
        
        return valid_count
    
    def validate_image_paths(self, image_paths):
        """Validate image paths and return status"""
        if not image_paths:
            return {
                'total': 0,
                'valid': 0,
                'missing': 0,
                'errors': []
            }
        
        total = len(image_paths)
        valid = 0
        missing = 0
        errors = []
        
        for path in image_paths:
            if os.path.exists(path):
                try:
                    # Try to read the file to ensure it's accessible
                    with open(path, 'rb') as f:
                        f.read(1)  # Read just one byte to test
                    valid += 1
                except (OSError, IOError, PermissionError) as e:
                    errors.append(f"{os.path.basename(path)}: {str(e)}")
            else:
                missing += 1
        
        return {
            'total': total,
            'valid': valid,
            'missing': missing,
            'errors': errors
        }
    
    def get_patient_summary(self, patient_id):
        """Get summary of available images for a patient"""
        if self.df is None:
            return None
            
        patient_data = self.get_patient_data(patient_id)
        if patient_data is None:
            return None
        
        summary = {
            'patient_id': patient_id,
            'timepoints': self.get_patient_timepoints(patient_id),
            'total_records': len(patient_data),
            'modalities': {}
        }
        
        # Count images by modality and eye
        for modality in ['vf', 'oct']:
            summary['modalities'][modality] = {}
            for eye in ['OS', 'OD']:
                images = self.get_eye_images(patient_id, modality, eye)
                validation = self.validate_image_paths(images)
                summary['modalities'][modality][eye] = {
                    'total_files': validation['total'],
                    'valid_files': validation['valid'],
                    'missing_files': validation['missing']
                }
        
        return summary
    
    def preload_images_for_cache(self, image_paths):
        """Preload and validate images for caching"""
        validated_paths = []
        
        for path in image_paths:
            if os.path.exists(path):
                try:
                    # Validate the image can be read
                    with open(path, 'rb') as f:
                        f.read(1)
                    validated_paths.append(path)
                except (OSError, IOError, PermissionError):
                    # Skip invalid files
                    continue
        
        return validated_paths
    
    def display_patient_overview(self, patient_id):
        """Display overview of all images for a patient"""
        summary = self.get_patient_summary(patient_id)
        if not summary:
            st.error(f"No data found for patient {patient_id}")
            return
        
        st.write(f"**Patient:** {patient_id}")
        
        # Format timepoints based on type
        timepoints = summary['timepoints']
        if timepoints and isinstance(timepoints[0], pd.Timestamp):
            # Format datetime objects nicely
            formatted_timepoints = [tp.strftime('%Y-%m-%d') for tp in timepoints]
            st.write(f"**Timepoints:** {', '.join(formatted_timepoints)}")
        else:
            st.write(f"**Timepoints:** {', '.join(map(str, timepoints))}")
        
        st.write(f"**Total Records:** {summary['total_records']}")
        
        # Create columns for each modality
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Visual Field (VF)**")
            for eye in ['OS', 'OD']:
                eye_data = summary['modalities']['VF'][eye]
                st.write(f"- {eye}: {eye_data['valid_files']}/{eye_data['total_files']} valid")
        
        with col2:
            st.write("**OCT**")
            for eye in ['OS', 'OD']:
                eye_data = summary['modalities']['OCT'][eye]
                st.write(f"- {eye}: {eye_data['valid_files']}/{eye_data['total_files']} valid")