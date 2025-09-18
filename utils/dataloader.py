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
    def __init__(self, label_dir="labels"):
        self.label_dir = label_dir
        os.makedirs(label_dir, exist_ok=True)

    def get_label_path(self, username: str, maskedid: str, eye: str, vf_number: int) -> str:
        """Gera caminho do arquivo com username para evitar conflitos"""
        return os.path.join(self.label_dir, f"{username}_{maskedid}_{eye}_{vf_number}.json")

    def save_labels(self, username: str, maskedid: str, eye: str, vf_number: int, labels_dict: dict) -> bool:
        """Salva labels com username no nome do arquivo"""
        try:
            filepath = self.get_label_path(username, maskedid, eye, vf_number)
            with open(filepath, 'w') as f:
                json.dump(labels_dict, f, indent=2)
            return True
        except Exception as e:
            st.error(f"Error saving labels: {e}")
            return False

    def load_labels(self, username: str, maskedid: str, eye: str, vf_number: int) -> Optional[dict]:
        """Carrega labels específicos do usuário"""
        try:
            filepath = self.get_label_path(username, maskedid, eye, vf_number)
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    return json.load(f)
        except Exception as e:
            st.error(f"Error loading labels: {e}")
        return None
    
    def get_user_labels_for_patient(self, username: str, maskedid: str) -> List[dict]:
        """Retorna todos os labels de um usuário para um paciente específico"""
        labels = []
        label_files = [f for f in os.listdir(self.label_dir) 
                      if f.startswith(f"{username}_{maskedid}_") and f.endswith('.json')]
        
        for file in label_files:
            try:
                with open(os.path.join(self.label_dir, file), 'r') as f:
                    labels.append(json.load(f))
            except Exception as e:
                st.error(f"Error loading {file}: {e}")
        
        return labels
    
    def delete_user_labels_for_patient(self, username: str, maskedid: str) -> bool:
        """Deleta todos os labels de um usuário para um paciente (útil para reset)"""
        try:
            label_files = [f for f in os.listdir(self.label_dir) 
                          if f.startswith(f"{username}_{maskedid}_") and f.endswith('.json')]
            
            for file in label_files:
                os.remove(os.path.join(self.label_dir, file))
            
            return True
        except Exception as e:
            st.error(f"Error deleting labels: {e}")
            return False