"""
Cache Manager for Glaucoma Progression Interface
Handles caching of patient data, images, and labels for performance optimization
"""

import streamlit as st
import pandas as pd
from collections import OrderedDict
from datetime import datetime


class CacheManager:
    """Manages caching system for patient data, images, and labels"""
    
    def __init__(self, max_cache_size=5, image_handler=None):
        self.max_cache_size = max_cache_size
        self.image_handler = image_handler
        self._initialize_caches()
    
    def set_image_handler(self, image_handler):
        """Set the image handler instance"""
        self.image_handler = image_handler
    
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
        # Convert patient_id to string for consistent handling
        patient_key = str(patient_id)
        
        if patient_key in cache_dict:
            # Move to end (most recent)
            cache_dict.move_to_end(patient_key)
        else:
            # Add new entry
            cache_dict[patient_key] = {}
            # Remove oldest if exceeding max size
            while len(cache_dict) > self.max_cache_size:
                cache_dict.popitem(last=False)
    
    def cache_patient_images(self, patient_id, timepoint=None):
        """Cache images for a patient"""
        patient_key = str(patient_id)
        # Use timepoint in image cache since ImageHandler supports it
        cache_key = f"{patient_key}_{timepoint}" if timepoint else patient_key
        
        if cache_key in st.session_state['image_cache']:
            return st.session_state['image_cache'][cache_key]
        
        if not self.image_handler:
            st.error("Image handler not initialized")
            return {}
        
        # Load images using ImageHandler with original signature
        #    def get_eye_images(self, patient_id, modality, eye, timepoint=None):
        vf_od = self.image_handler.get_eye_images(modality="VF", eye="OD", patient_id=patient_id, timepoint=timepoint)
        vf_os = self.image_handler.get_eye_images(modality="VF", eye="OS", patient_id=patient_id, timepoint=timepoint)
        oct_od = self.image_handler.get_eye_images(modality="OCT", eye="OD", patient_id=patient_id, timepoint=timepoint)
        oct_os = self.image_handler.get_eye_images(modality="OCT", eye="OS", patient_id=patient_id, timepoint=timepoint)

        # Cache the image paths with validation
        image_data = {
            'vf_od': self.image_handler.preload_images_for_cache(vf_od),
            'vf_os': self.image_handler.preload_images_for_cache(vf_os),
            'oct_od': self.image_handler.preload_images_for_cache(oct_od),
            'oct_os': self.image_handler.preload_images_for_cache(oct_os),
            'loaded_at': datetime.now(),
            'patient_id': patient_id,
            'timepoint': timepoint
        }
        
        self.update_cache_order(cache_key, st.session_state['image_cache'])
        st.session_state['image_cache'][cache_key] = image_data
        
        return image_data
    
    def cache_patient_labels(self, patient_id, dl, timepoint=None):
        """Cache labels for a patient"""
        patient_key = str(patient_id)
        cache_key = f"{patient_key}_{timepoint}" if timepoint else patient_key
        
        if cache_key in st.session_state['labels_cache']:
            return st.session_state['labels_cache'][cache_key]
        
        # Load labels using DataLoader
        previous_saved = dl.load_labels(
            patient_id, 
            specialist_name=st.session_state.get("specialist_name", ""),
        )
        
        self.update_cache_order(cache_key, st.session_state['labels_cache'])
        st.session_state['labels_cache'][cache_key] = previous_saved
        
        return previous_saved
    
    def get_cached_patient_data(self, patient_id, dl, timepoint=None):
        """Get all cached data for a patient or load it"""
        patient_key = str(patient_id)
        
        # Update patient cache order
        self.update_cache_order(patient_key, st.session_state['patient_cache'])
        
        # Get or load images (don't pass timepoint for now)
        image_data = self.cache_patient_images(patient_id)
        
        # Get or load labels (don't pass timepoint for now)
        labels_data = self.cache_patient_labels(patient_id, dl)
        
        return image_data, labels_data
    
    def update_labels_cache(self, patient_id, labels_data, timepoint=None):
        """Update labels cache with new data"""
        patient_key = str(patient_id)
        cache_key = f"{patient_key}_{timepoint}" if timepoint else patient_key
        st.session_state['labels_cache'][cache_key] = labels_data
    
    def clear_cache(self):
        """Clear all caches"""
        st.session_state['patient_cache'].clear()
        st.session_state['image_cache'].clear()
        st.session_state['labels_cache'].clear()
    
    def clear_patient_cache(self, patient_id):
        """Clear cache for specific patient"""
        patient_key = str(patient_id)
        
        # Remove from all caches
        if patient_key in st.session_state['patient_cache']:
            del st.session_state['patient_cache'][patient_key]
        
        # Remove all timepoint variations from image and labels cache
        keys_to_remove = []
        for key in st.session_state['image_cache'].keys():
            if key.startswith(patient_key):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del st.session_state['image_cache'][key]
        
        keys_to_remove = []
        for key in st.session_state['labels_cache'].keys():
            if key.startswith(patient_key):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del st.session_state['labels_cache'][key]
    
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
        
        # Convert all to strings to avoid TypeError
        recent_str = [str(patient_id) for patient_id in recent]
        
        if len(cached_patients) > limit:
            return f"...{', '.join(recent_str)}"
        return ', '.join(recent_str)
    
    def is_patient_cached(self, patient_id):
        """Check if patient is in cache"""
        patient_key = str(patient_id)
        return patient_key in st.session_state['patient_cache']
    
    def get_cached_timepoints(self, patient_id):
        """Get cached timepoints for a patient"""
        patient_key = str(patient_id)
        timepoints = []
        
        for cache_key in st.session_state['image_cache'].keys():
            if cache_key.startswith(patient_key):
                if '_' in cache_key:
                    # Extract timepoint from cache key
                    timepoint_str = cache_key.split('_', 1)[1]
                    if timepoint_str != 'None':
                        try:
                            # Try to parse as datetime if needed
                            timepoint = pd.to_datetime(timepoint_str)
                            timepoints.append(timepoint)
                        except:
                            timepoints.append(timepoint_str)
        
        return sorted(set(timepoints))
    
    def invalidate_patient_cache(self, patient_id):
        """Mark patient cache as invalid without removing it"""
        patient_key = str(patient_id)
        
        # Add invalidation timestamp
        if patient_key in st.session_state['patient_cache']:
            st.session_state['patient_cache'][patient_key]['invalidated_at'] = datetime.now()
    
    def get_cache_memory_info(self):
        """Get approximate memory usage information"""
        total_images = 0
        total_labels = 0
        
        for cache_data in st.session_state['image_cache'].values():
            if isinstance(cache_data, dict):
                for modality_data in ['vf_od', 'vf_os', 'oct_od', 'oct_os']:
                    if modality_data in cache_data:
                        total_images += len(cache_data[modality_data])
        
        for labels_data in st.session_state['labels_cache'].values():
            if isinstance(labels_data, dict):
                total_labels += len(labels_data)
        
        return {
            'total_cached_images': total_images,
            'total_cached_labels': total_labels,
            'cache_entries': {
                'patients': len(st.session_state['patient_cache']),
                'images': len(st.session_state['image_cache']),
                'labels': len(st.session_state['labels_cache'])
            }
        }