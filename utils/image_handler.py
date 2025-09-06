"""
Image Handler for Glaucoma Progression Interface
Handles image loading, processing, and display functionality
"""

import streamlit as st
import base64
import os
from utils.config import EXTS


class ImageHandler:
    """Handles image operations for the labeling interface"""
    
    def __init__(self):
        pass
    
    def find_folder(self, base_dir, patient_id):
        """Find patient folder in base directory"""
        if not os.path.exists(base_dir):
            return None
            
        for folder in os.listdir(base_dir):
            if patient_id.lower() in folder.lower():
                return os.path.join(base_dir, folder)
        return None
    
    def get_eye_images(self, base_dir, modality, patient_id, eye):
        """Get list of image files for specific eye and modality"""
        folder = self.find_folder(base_dir, patient_id)
        if not folder:
            return []
        
        if not os.path.exists(folder):
            return []
            
        prefix = f"{modality}_{patient_id}_{eye}_"
        image_files = []
        
        try:
            for filename in sorted(os.listdir(folder)):
                if filename.startswith(prefix) and filename.endswith(EXTS):
                    image_files.append(os.path.join(folder, filename))
        except (OSError, PermissionError):
            # Handle case where folder exists but can't be read
            return []
            
        return image_files
    
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
    
    def display_scrollable_images(self, image_paths, height=450):
        """Display images in a scrollable container"""
        if not image_paths:
            st.write("No images found for this patient/eye combination.")
            return
        
        html_content = self.create_image_html(image_paths)
        
        if html_content:
            st.markdown(
                f"<div class='scrollable-box' style='height:{height}px;'>{html_content}</div>", 
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