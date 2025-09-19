# ─────────────────────────────────────────────────────────────────────────────
# Data loader for Glaucoma Progression Interface : Last update December 20, 2024
# ─────────────────────────────────────────────────────────────────────────────
import json
import os
import pandas as pd
import streamlit as st
from datetime import datetime
from typing import Dict, List, Any, Optional
import base64
import tempfile
import requests
from io import BytesIO

# Google Drive imports
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

class DataLoader:
    def __init__(self, label_dir="labels"):
        self.label_dir = label_dir
        os.makedirs(label_dir, exist_ok=True)
        self.main_folder_id = "1SrtUAd26Y5LZdbZtvve5aa4NB3aLpSvr"
        self.pdfs_folder_id = "18a3tuxtwP84nZ6-hFu7BVz3jiePKGuNI"
        self.data_folder_id = "1X_sp-ME4haIcCkpcmG1v_Hhot3yAlvK-"
        self.labels_folder_id = "NOT_FOUND"

    def _get_drive_service(self):
        """Get Google Drive service using credentials from secrets or file"""
        if not GOOGLE_AVAILABLE:
            return None
            
        try:
            # Try Streamlit secrets first (for production)
            if hasattr(st, 'secrets') and 'google_drive' in st.secrets:
                credentials_dict = dict(st.secrets['google_drive'])
                credentials = service_account.Credentials.from_service_account_info(
                    credentials_dict,
                    scopes=['https://www.googleapis.com/auth/drive.readonly']
                )
            # Fallback to local file (for development)
            elif os.path.exists('credentials.json'):
                credentials = service_account.Credentials.from_service_account_file(
                    'credentials.json',
                    scopes=['https://www.googleapis.com/auth/drive.readonly']
                )
            else:
                return None
                
            return build('drive', 'v3', credentials=credentials)
            
        except Exception as e:
            st.error(f"Error creating Drive service: {e}")
            return None

    def get_label_path(self, username: str, maskedid: str, eye: str, vf_number: int) -> str:
        """Gera caminho do arquivo com username para evitar conflitos"""
        return os.path.join(self.label_dir, f"{username}_{maskedid}_{eye}_{vf_number}.json")

    def save_labels(self, username: str, maskedid: str, eye: str, vf_number: int, labels_dict: dict) -> bool:
        """Salva labels apenas localmente (cloud storage para labels desabilitado)"""
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

    def get_pdf_from_drive(self, pdf_filename: str) -> Optional[BytesIO]:
        """Baixa PDF do Google Drive e retorna como BytesIO"""
        service = self._get_drive_service()
        if not service:
            return None
        
        try:
            # Busca o arquivo PDF na pasta PDFs
            results = service.files().list(
                q=f"name='{pdf_filename}' and parents in '{self.pdfs_folder_id}'"
            ).execute()
            
            files = results.get('files', [])
            if not files:
                return None
            
            # Download do arquivo
            file_id = files[0]['id']
            request = service.files().get_media(fileId=file_id)
            
            file_content = BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            file_content.seek(0)
            return file_content
            
        except Exception as e:
            st.error(f"Error downloading PDF {pdf_filename}: {e}")
            return None

    def get_csv_from_drive(self, csv_filename: str = "opv_24-2_prepared.csv") -> Optional[pd.DataFrame]:
        """Baixa CSV do Google Drive e retorna como DataFrame"""
        service = self._get_drive_service()
        if not service:
            return None
        
        try:
            # Busca o arquivo CSV na pasta data
            results = service.files().list(
                q=f"name='{csv_filename}' and parents in '{self.data_folder_id}'"
            ).execute()
            
            files = results.get('files', [])
            if not files:
                return None
            
            # Download do arquivo
            file_id = files[0]['id']
            request = service.files().get_media(fileId=file_id)
            
            file_content = BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            file_content.seek(0)
            
            # Converte para DataFrame
            df = pd.read_csv(file_content)
            return df
            
        except Exception as e:
            st.error(f"Error downloading CSV {csv_filename}: {e}")
            return None

    @st.cache_data
    def get_pdf_as_public_url(_self, pdf_filename: str) -> Optional[str]:
        """Tenta obter URL público do PDF (se compartilhado publicamente)"""
        service = _self._get_drive_service()
        if not service:
            return None
        
        try:
            # Busca o arquivo
            results = service.files().list(
                q=f"name='{pdf_filename}' and parents in '{_self.pdfs_folder_id}'"
            ).execute()
            
            files = results.get('files', [])
            if not files:
                return None
            
            file_id = files[0]['id']
            
            # Verifica se o arquivo está compartilhado publicamente
            try:
                permissions = service.permissions().list(fileId=file_id).execute()
                
                # Se tiver permissão pública, retorna URL de visualização
                for permission in permissions.get('permissions', []):
                    if permission.get('type') == 'anyone':
                        return f"https://drive.google.com/file/d/{file_id}/view"
                
                return None
                
            except:
                return None
                
        except Exception as e:
            return None
    
    def get_user_labels_for_patient(self, username: str, maskedid: str) -> List[dict]:
        """Retorna todos os labels de um usuário para um paciente específico"""
        labels = []
        if not os.path.exists(self.label_dir):
            return labels
            
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
            if not os.path.exists(self.label_dir):
                return True
                
            label_files = [f for f in os.listdir(self.label_dir) 
                          if f.startswith(f"{username}_{maskedid}_") and f.endswith('.json')]
            
            for file in label_files:
                os.remove(os.path.join(self.label_dir, file))
            
            return True
        except Exception as e:
            st.error(f"Error deleting labels: {e}")
            return False

    def cache_pdf_locally(self, pdf_filename: str) -> Optional[str]:
        """Baixa e cacheía PDF localmente para melhor performance"""
        cache_dir = "pdf_cache"
        os.makedirs(cache_dir, exist_ok=True)
        
        cached_path = os.path.join(cache_dir, pdf_filename)
        
        # Se já está em cache, retorna
        if os.path.exists(cached_path):
            return cached_path
        
        # Baixa do Drive
        pdf_content = self.get_pdf_from_drive(pdf_filename)
        if pdf_content:
            try:
                with open(cached_path, 'wb') as f:
                    f.write(pdf_content.getvalue())
                return cached_path
            except Exception as e:
                st.error(f"Error caching PDF: {e}")
        
        return None