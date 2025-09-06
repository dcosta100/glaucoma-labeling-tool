"""
Cache Manager for Glaucoma Progression Interface
Handles caching of patient data, images, and labels for performance optimization
"""

import streamlit as st
from collections import OrderedDict
from datetime import datetime
from utils.image_handler import ImageHandler


class CacheManager:
    """Manages caching system for patient data, images, and labels"""
    
    def __init__(self, max_cache_size=5):
        self.max_cache_size = max_cache_size
        self.image_handler = ImageHandler()
        self._initialize_caches()
    
    def _initialize_caches(self):
        """Initialize cache structures in session state"""
        if 'patient_cache' not in st.session_state:
            st.session_state['patient_cache'] = OrderedDict()
        
        if 'image_cache' not in st.session_state:
            st.session_state['image_cache'] = OrderedDict()
        
        if 'labels_cache' not in st.session_state:
            st.session_state['labels_cache'] = OrderedDict()
    
    def update_cache_order(self, patient_id, cache_dict):
        """Update cache order and maintain max size"""
        if patient_id in cache_dict:
            # Move to end (most recent)
            cache_dict.move_to_end(patient_id)
        else:
            # Add new entry
            cache_dict[patient_id] = {}
            # Remove oldest if exceeding max size
            while len(cache_dict) > self.max_cache_size:
                cache_dict.popitem(last=False)
    
    def cache_patient_images(self, patient_id):
        """Cache images for a patient"""
        if patient_id in st.session_state['image_cache']:
            return st.session_state['image_cache'][patient_id]
        
        # Load images using ImageHandler
        from utils.config import VF_IMAGES_DIR, OCT_IMAGES_DIR
        
        vf_od = self.image_handler.get_eye_images(VF_IMAGES_DIR, "VF", patient_id, "OD")
        vf_os = self.image_handler.get_eye_images(VF_IMAGES_DIR, "VF", patient_id, "OS")
        oct_od = self.image_handler.get_eye_images(OCT_IMAGES_DIR, "OCT", patient_id, "OD")
        oct_os = self.image_handler.get_eye_images(OCT_IMAGES_DIR, "OCT", patient_id, "OS")
        
        # Cache the image paths
        image_data = {
            'vf_od': vf_od,
            'vf_os': vf_os,
            'oct_od': oct_od,
            'oct_os': oct_os,
            'loaded_at': datetime.now()
        }
        
        self.update_cache_order(patient_id, st.session_state['image_cache'])
        st.session_state['image_cache'][patient_id] = image_data
        
        return image_data
    
    def cache_patient_labels(self, patient_id, dl):
        """Cache labels for a patient"""
        if patient_id in st.session_state['labels_cache']:
            return st.session_state['labels_cache'][patient_id]
        
        # Load labels using DataLoader
        previous_saved = dl.load_labels(
            patient_id, 
            specialist_name=st.session_state.get("specialist_name", "")
        )
        
        self.update_cache_order(patient_id, st.session_state['labels_cache'])
        st.session_state['labels_cache'][patient_id] = previous_saved
        
        return previous_saved
    
    def get_cached_patient_data(self, patient_id, dl):
        """Get all cached data for a patient or load it"""
        # Update patient cache order
        self.update_cache_order(patient_id, st.session_state['patient_cache'])
        
        # Get or load images
        image_data = self.cache_patient_images(patient_id)
        
        # Get or load labels
        labels_data = self.cache_patient_labels(patient_id, dl)
        
        return image_data, labels_data
    
    def update_labels_cache(self, patient_id, labels_data):
        """Update labels cache with new data"""
        st.session_state['labels_cache'][patient_id] = labels_data
    
    def clear_cache(self):
        """Clear all caches"""
        st.session_state['patient_cache'].clear()
        st.session_state['image_cache'].clear()
        st.session_state['labels_cache'].clear()
    
    def get_cache_statistics(self):
        """Get cache statistics for display"""
        return {
            'patients_cached': len(st.session_state['patient_cache']),
            'max_cache_size': self.max_cache_size,
            'images_cached': len(st.session_state['image_cache']),
            'labels_cached': len(st.session_state['labels_cache']),
            'cache_order': list(st.session_state['patient_cache'].keys())
        }
    
    def get_recently_cached_patients(self, limit=3):
        """Get list of recently cached patients for display"""
        cached_patients = list(st.session_state['patient_cache'].keys())
        if not cached_patients:
            return []
        
        recent = cached_patients[-limit:]
        if len(cached_patients) > limit:
            return f"...{', '.join(recent)}"
        return ', '.join(recent)
    
    def is_patient_cached(self, patient_id):
        """Check if patient is in cache"""
        return patient_id in st.session_state['patient_cache']