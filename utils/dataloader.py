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

# Google APIs imports
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
        
        # Google Drive folder IDs
        self.main_folder_id = "1SrtUAd26Y5LZdbZtvve5aa4NB3aLpSvr"
        self.pdfs_folder_id = "18a3tuxtwP84nZ6-hFu7BVz3jiePKGuNI"
        self.data_folder_id = "1X_sp-ME4haIcCkpcmG1v_Hhot3yAlvK-"
        
        # Google Sheets ID - SUBSTITUA PELO ID DA SUA PLANILHA
        self.spreadsheet_id = "1zM68Wb5fbyM9b-arFbEyFm4eP2EzPQuPE2ki54BGYnU"  
        self.sheet_name = "labels_spreadsheet"

    def _get_drive_service(self):
        """Get Google Drive service using credentials from secrets or file"""
        if not GOOGLE_AVAILABLE:
            return None
            
        try:
            if hasattr(st, 'secrets') and 'google_drive' in st.secrets:
                credentials_dict = dict(st.secrets['google_drive'])
                credentials = service_account.Credentials.from_service_account_info(
                    credentials_dict,
                    scopes=['https://www.googleapis.com/auth/drive.readonly']
                )
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

    def _get_sheets_service(self):
        """Get Google Sheets service using credentials"""
        if not GOOGLE_AVAILABLE:
            return None
            
        try:
            if hasattr(st, 'secrets') and 'google_drive' in st.secrets:
                credentials_dict = dict(st.secrets['google_drive'])
                credentials = service_account.Credentials.from_service_account_info(
                    credentials_dict,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
            elif os.path.exists('credentials.json'):
                credentials = service_account.Credentials.from_service_account_file(
                    'credentials.json',
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
            else:
                return None
                
            return build('sheets', 'v4', credentials=credentials)
            
        except Exception as e:
            st.error(f"Error creating Sheets service: {e}")
            return None

    def get_label_path(self, username: str, maskedid: str, eye: str, vf_number: int) -> str:
        """Gera caminho do arquivo com username para evitar conflitos"""
        return os.path.join(self.label_dir, f"{username}_{maskedid}_{eye}_{vf_number}.json")

    def save_labels(self, username: str, maskedid: str, eye: str, vf_number: int, labels_dict: dict) -> bool:
        """Salva labels localmente E no Google Sheets"""
        
        # 1. Salvar local (mantém backup)
        local_saved = False
        try:
            filepath = self.get_label_path(username, maskedid, eye, vf_number)
            with open(filepath, 'w') as f:
                json.dump(labels_dict, f, indent=2)
            local_saved = True
        except Exception as e:
            st.error(f"Error saving labels locally: {e}")
        
        # 2. Salvar no Google Sheets
        sheets_saved = self._save_to_sheets(username, maskedid, eye, vf_number, labels_dict)
        
        return local_saved or sheets_saved

    def _save_to_sheets(self, username: str, maskedid: str, eye: str, vf_number: int, labels_dict: dict) -> bool:
        """Salva labels como linha no Google Sheets"""
        service = self._get_sheets_service()
        if not service:
            return False
        
        try:
            # Preparar dados da linha (incluindo campos do CSV)
            row_data = [
                username,
                maskedid,
                eye,
                vf_number,
                labels_dict.get('pdf_filename', ''),        # Campo do CSV
                labels_dict.get('opv_filename', ''),        # Campo do CSV  
                labels_dict.get('aeexamdate_shift', ''),    # Campo do CSV
                labels_dict.get('age', ''),                 # Campo do CSV
                labels_dict.get('normality', ''),
                labels_dict.get('reliability', ''),
                labels_dict.get('gdefect1', ''),
                labels_dict.get('gposition1', ''),
                labels_dict.get('gdefect2', ''),
                labels_dict.get('gposition2', ''),
                labels_dict.get('gdefect3', ''),
                labels_dict.get('gposition3', ''),
                labels_dict.get('ngdefect1', ''),
                labels_dict.get('ngposition1', ''),
                labels_dict.get('ngdefect2', ''),
                labels_dict.get('ngposition2', ''),
                labels_dict.get('ngdefect3', ''),
                labels_dict.get('ngposition3', ''),
                labels_dict.get('artifact1', ''),
                labels_dict.get('artifact2', ''),
                labels_dict.get('comment', ''),
                labels_dict.get('last_updated', ''),
                labels_dict.get('specialist_name', username),
                labels_dict.get('data_source', '')          # Info sobre fonte dos dados
            ]
            
            # Verificar se já existe entry para este label
            existing_row = self._find_existing_row(service, username, maskedid, eye, vf_number)
            
            if existing_row:
                # Atualizar linha existente
                range_name = f"{self.sheet_name}!A{existing_row}:AB{existing_row}"
                body = {
                    'values': [row_data],
                    'majorDimension': 'ROWS'
                }
                service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_name,
                    valueInputOption='USER_ENTERED',
                    body=body
                ).execute()
                print(f"✅ Label atualizado no Sheets: linha {existing_row}")
            else:
                # Adicionar nova linha
                body = {
                    'values': [row_data],
                    'majorDimension': 'ROWS'
                }
                service.spreadsheets().values().append(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{self.sheet_name}!A1",
                    valueInputOption='USER_ENTERED',
                    insertDataOption='INSERT_ROWS',
                    body=body
                ).execute()
                print("✅ Novo label adicionado ao Sheets")
            
            return True
            
        except Exception as e:
            st.error(f"Error saving to Google Sheets: {e}")
            return False

    def _find_existing_row(self, service, username: str, maskedid: str, eye: str, vf_number: int) -> int:
        """Encontra linha existente para este label específico"""
        try:
            # Ler todas as linhas da planilha (apenas colunas A-D para busca)
            range_name = f"{self.sheet_name}!A:D"
            result = service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            # Procurar por linha que match username, maskedid, eye, vf_number
            for i, row in enumerate(values):
                if len(row) >= 4 and (
                    row[0] == username and 
                    row[1] == maskedid and 
                    row[2] == eye and 
                    str(row[3]) == str(vf_number)
                ):
                    return i + 1  # Sheets usa 1-indexing
            
            return None  # Não encontrou
            
        except Exception as e:
            print(f"Error finding existing row: {e}")
            return None

    def load_labels_from_sheets(self, username: str, maskedid: str, eye: str, vf_number: int) -> Optional[dict]:
        """Carrega labels do Google Sheets"""
        service = self._get_sheets_service()
        if not service:
            return None
        
        try:
            existing_row = self._find_existing_row(service, username, maskedid, eye, vf_number)
            if not existing_row:
                return None
            
            # Ler a linha específica
            range_name = f"{self.sheet_name}!A{existing_row}:AB{existing_row}"
            result = service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [[]])
            if not values or not values[0]:
                return None
            
            row = values[0]
            
            # Mapear de volta para dict
            labels = {}
            column_mapping = [
                'username', 'maskedid', 'eye', 'vf_number',
                'pdf_filename', 'opv_filename', 'aeexamdate_shift', 'age',
                'normality', 'reliability',
                'gdefect1', 'gposition1', 'gdefect2', 'gposition2', 'gdefect3', 'gposition3',
                'ngdefect1', 'ngposition1', 'ngdefect2', 'ngposition2', 'ngdefect3', 'ngposition3',
                'artifact1', 'artifact2', 'comment', 'last_updated', 'specialist_name', 'data_source'
            ]
            
            for i, key in enumerate(column_mapping):
                if i < len(row) and row[i]:
                    labels[key] = row[i]
            
            return labels
            
        except Exception as e:
            print(f"Error loading from sheets: {e}")
            return None

    def load_labels(self, username: str, maskedid: str, eye: str, vf_number: int) -> Optional[dict]:
        """Carrega labels - tenta local primeiro, depois Sheets"""
        # Tentar local primeiro
        try:
            filepath = self.get_label_path(username, maskedid, eye, vf_number)
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    return json.load(f)
        except Exception as e:
            pass
        
        # Fallback para Sheets
        return self.load_labels_from_sheets(username, maskedid, eye, vf_number)

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