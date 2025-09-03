# ─────────────────────────────────────────────────────────────────────────────
# Data loader for Glaucoma Progression Interface : Last update September 3, 2025
# ─────────────────────────────────────────────────────────────────────────────
import json
import os
import pandas as pd
import streamlit as st
from datetime import datetime
from typing import Dict, List, Any, Optional
import base64

class DataLoader:
    def __init__(self, labels_dir: str = "labels"):
        self.labels_dir = labels_dir
        self.ensure_labels_dir()
    
    def ensure_labels_dir(self):
        """Create labels directory if it doesn't exist"""
        if not os.path.exists(self.labels_dir):
            os.makedirs(self.labels_dir)
    
    def get_label_file_path(self, patient_id: str, specialist_name: str) -> str:
        """Generate label file path for a specific patient and specialist"""
        filename = f"{patient_id}_{specialist_name.replace(' ', '_')}.json"
        return os.path.join(self.labels_dir, filename)
    
    def save_labels(self, patient_id: str, specialist_name: str, labels_data: Dict[str, Any]) -> bool:
        """Save labels to JSON file"""
        try:
            filepath = self.get_label_file_path(patient_id, specialist_name)
            
            # Add metadata
            labels_data.update({
                "patient_id": patient_id,
                "specialist_name": specialist_name,
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            })
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(labels_data, f, indent=2, default=str)
            
            return True
        except Exception as e:
            st.error(f"Error saving labels: {str(e)}")
            return False
    
    def load_labels(self, patient_id: str, specialist_name: str) -> Optional[Dict[str, Any]]:
        """Load labels from JSON file"""
        try:
            filepath = self.get_label_file_path(patient_id, specialist_name)
            
            if not os.path.exists(filepath):
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading labels: {str(e)}")
            return None
    
    def get_all_patient_labels(self, patient_id: str) -> Dict[str, Dict[str, Any]]:
        """Get all labels for a patient from all specialists"""
        all_labels = {}
        
        for filename in os.listdir(self.labels_dir):
            if filename.startswith(f"{patient_id}_") and filename.endswith(".json"):
                specialist_name = filename.replace(f"{patient_id}_", "").replace(".json", "").replace("_", " ")
                labels = self.load_labels(patient_id, specialist_name)
                if labels:
                    all_labels[specialist_name] = labels
        
        return all_labels
    
    def labels_to_dataframe(self, labels_data: Dict[str, Any]) -> pd.DataFrame:
        """Convert labels dictionary to DataFrame format"""
        if not labels_data:
            return pd.DataFrame()
        
        rows = []
        timestamp = labels_data.get("last_updated", datetime.now().isoformat())
        patient_id = labels_data.get("patient_id", "")
        
        # Extract evaluation data
        evaluations = labels_data.get("evaluations", {})
        
        for key, evaluation in evaluations.items():
            # Parse key to extract eye and modality
            if "_" in key:
                parts = key.split("_")
                if len(parts) >= 2:
                    modality = parts[0].upper()  # VF or OCT
                    eye = parts[1].upper()       # OD or OS
                else:
                    continue
            else:
                continue
            
            rows.append({
                "Patient ID": patient_id,
                "Eye": eye,
                "Modality": modality,
                "Progression": evaluation.get("status", ""),
                "First": evaluation.get("first_date", "N/A"),
                "Second": evaluation.get("second_date", "N/A"),
                "Time": timestamp
            })
        
        return pd.DataFrame(rows)
    
    def dataframe_to_labels(self, df: pd.DataFrame, patient_id: str, specialist_name: str) -> Dict[str, Any]:
        """Convert DataFrame to labels dictionary format"""
        labels_data = {
            "patient_id": patient_id,
            "specialist_name": specialist_name,
            "evaluations": {}
        }
        
        for _, row in df.iterrows():
            key = f"{row['Modality'].lower()}_{row['Eye'].lower()}"
            labels_data["evaluations"][key] = {
                "status": row["Progression"],
                "first_date": row["First"] if row["First"] != "N/A" else None,
                "second_date": row["Second"] if row["Second"] != "N/A" else None
            }
        
        return labels_data

@st.cache_data
def load_and_cache_images(image_paths: List[str]) -> Dict[str, str]:
    """Load and cache images as base64 strings"""
    cached_images = {}
    
    for path in image_paths:
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    image_data = f.read()
                    b64_string = base64.b64encode(image_data).decode()
                    cached_images[path] = b64_string
            except Exception as e:
                st.warning(f"Could not load image {path}: {str(e)}")
    
    return cached_images

@st.cache_data
def get_cached_labels_dataframe(patient_id: str, specialist_name: str) -> pd.DataFrame:
    """Cache labels DataFrame for current session"""
    loader = DataLoader()
    labels_data = loader.load_labels(patient_id, specialist_name)
    
    if labels_data:
        return loader.labels_to_dataframe(labels_data)
    else:
        # Return empty DataFrame with correct structure
        return pd.DataFrame(columns=["Patient ID", "Eye", "Modality", "Progression", "First", "Second", "Time"])

def clear_cache():
    """Clear all cached data"""
    st.cache_data.clear()

def update_cached_labels(patient_id: str, specialist_name: str, labels_data: Dict[str, Any]):
    """Update cached labels after saving"""
    loader = DataLoader()
    
    # Save to file
    if loader.save_labels(patient_id, specialist_name, labels_data):
        # Clear cache to force reload
        clear_cache()
        return True
    return False