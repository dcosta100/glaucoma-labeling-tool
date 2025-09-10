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
from PIL import Image
import fitz
import io

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
    
def pdf_to_image_fitz(pdf_path: str, page_number: int = 0, zoom: float = 2.0):
    """
    Convert a single page of a PDF to a PIL image using PyMuPDF (fitz).

    :param pdf_path: Path to the PDF file
    :param page_number: Page number to render (starts at 0)
    :param zoom: Zoom factor (e.g., 2.0 for 200% scale)
    :return: PIL.Image or None
    """
    try:
        doc = fitz.open(pdf_path)
        page = doc.load_page(page_number)
        mat = fitz.Matrix(zoom, zoom)  # zoom factor
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_bytes))
        return image
    except Exception as e:
        print(f"Error rendering PDF: {e}")
        return None