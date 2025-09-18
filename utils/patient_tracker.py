"""
Patient Tracker - Sistema para rastrear quais pacientes cada usuário já rotulou
"""

import json
import os
import pandas as pd
from pathlib import Path
from typing import Set, List, Dict, Optional
from utils.config import LABELS_DIR

class PatientTracker:
    def __init__(self, labels_dir: str = None):
        self.labels_dir = Path(labels_dir or LABELS_DIR)
        self.progress_file = self.labels_dir / "user_progress.json"
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Garante que os diretórios necessários existem"""
        self.labels_dir.mkdir(parents=True, exist_ok=True)
        
        # Cria arquivo de progresso se não existir
        if not self.progress_file.exists():
            self._save_progress({})
    
    def _load_progress(self) -> Dict:
        """Carrega o arquivo de progresso dos usuários"""
        try:
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_progress(self, progress: Dict):
        """Salva o arquivo de progresso dos usuários"""
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
    
    def get_completed_patients(self, username: str) -> Set[str]:
        """Retorna set de pacientes já completados pelo usuário"""
        progress = self._load_progress()
        return set(progress.get(username, {}).get('completed_patients', []))
    
    def mark_patient_completed(self, username: str, maskedid: str):
        """Marca um paciente como completado para o usuário"""
        progress = self._load_progress()
        
        if username not in progress:
            progress[username] = {
                'completed_patients': [],
                'total_completed': 0,
                'last_patient': None
            }
        
        completed_patients = set(progress[username]['completed_patients'])
        
        if maskedid not in completed_patients:
            completed_patients.add(maskedid)
            progress[username]['completed_patients'] = list(completed_patients)
            progress[username]['total_completed'] = len(completed_patients)
            progress[username]['last_patient'] = maskedid
            
            self._save_progress(progress)
            return True
        return False
    
    def get_available_patients(self, username: str, all_patients: List[str]) -> List[str]:
        """Retorna lista de pacientes ainda não rotulados pelo usuário"""
        completed = self.get_completed_patients(username)
        available = [p for p in all_patients if p not in completed]
        return sorted(available)  # Ordenado para consistência
    
    def get_user_stats(self, username: str, total_patients: int) -> Dict:
        """Retorna estatísticas do progresso do usuário"""
        progress = self._load_progress()
        user_progress = progress.get(username, {})
        
        completed_count = len(user_progress.get('completed_patients', []))
        remaining_count = total_patients - completed_count
        completion_percentage = (completed_count / total_patients * 100) if total_patients > 0 else 0
        
        return {
            'username': username,
            'completed_count': completed_count,
            'remaining_count': remaining_count,
            'total_patients': total_patients,
            'completion_percentage': completion_percentage,
            'last_patient': user_progress.get('last_patient', None)
        }
    
    def has_completed_patient(self, username: str, maskedid: str) -> bool:
        """Verifica se o usuário já completou um paciente específico"""
        completed = self.get_completed_patients(username)
        return maskedid in completed
    
    def check_patient_completion(self, username: str, maskedid: str, df_patient: pd.DataFrame) -> bool:
        """
        Verifica se todos os campos visuais de um paciente foram rotulados
        Retorna True se o paciente está completo para este usuário
        """
        # Verifica se existem arquivos de label para todos os campos visuais
        all_labeled = True
        
        for _, row in df_patient.iterrows():
            eye = row['eye']
            vf_number = int(row['visual_field_number'])
            
            # Verifica se existe arquivo de label para este campo
            label_file = self.labels_dir / f"{maskedid}_{eye}_{vf_number}.json"
            
            if not label_file.exists():
                all_labeled = False
                break
            
            # Verifica se o label foi feito pelo usuário atual
            try:
                with open(label_file, 'r') as f:
                    label_data = json.load(f)
                    if label_data.get('specialist_name') != username:
                        all_labeled = False
                        break
            except (FileNotFoundError, json.JSONDecodeError):
                all_labeled = False
                break
        
        return all_labeled
    
    def auto_mark_completed_patients(self, username: str, all_patients: List[str], df: pd.DataFrame):
        """
        Varre automaticamente e marca pacientes já completados pelo usuário
        Útil para sincronização inicial
        """
        newly_completed = []
        
        for maskedid in all_patients:
            if not self.has_completed_patient(username, maskedid):
                df_patient = df[df['maskedid'] == maskedid]
                
                if self.check_patient_completion(username, maskedid, df_patient):
                    self.mark_patient_completed(username, maskedid)
                    newly_completed.append(maskedid)
        
        return newly_completed
    
    def reset_user_progress(self, username: str):
        """Remove todo progresso de um usuário (para admin/debug)"""
        progress = self._load_progress()
        if username in progress:
            del progress[username]
            self._save_progress(progress)
            return True
        return False
    
    def get_all_users_stats(self, total_patients: int) -> List[Dict]:
        """Retorna estatísticas de todos os usuários"""
        progress = self._load_progress()
        stats = []
        
        for username in progress.keys():
            stats.append(self.get_user_stats(username, total_patients))
        
        return sorted(stats, key=lambda x: x['completion_percentage'], reverse=True)
    
    def export_progress_report(self) -> Dict:
        """Exporta relatório completo de progresso"""
        progress = self._load_progress()
        
        report = {
            'export_timestamp': pd.Timestamp.now().isoformat(),
            'total_users': len(progress),
            'users': {}
        }
        
        for username, user_data in progress.items():
            report['users'][username] = {
                'completed_patients': user_data.get('completed_patients', []),
                'total_completed': user_data.get('total_completed', 0),
                'last_patient': user_data.get('last_patient', None),
                'last_activity': user_data.get('last_activity', None)
            }
        
        return report