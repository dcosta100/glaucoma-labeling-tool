"""
Patient Tracker - Agora usa Google Sheets em vez de JSON local
"""

import pandas as pd
from typing import Set, List, Dict
from utils.dataloader import DataLoader
import streamlit as st


# ---------------- CACHE HELPERS ---------------- #

@st.cache_data(ttl=30)
def get_progress_df(_dl, sheet_name="progress_tracking") -> pd.DataFrame:
    """Busca progresso do Google Sheets com cache de 30s"""
    service = _dl._get_sheets_service()
    if not service:
        return pd.DataFrame(columns=["username", "completed_patients", "last_patient"])

    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=_dl.spreadsheet_id,
            range=f"{sheet_name}!A1:C"
        ).execute()
        values = result.get("values", [])
        if not values or len(values) < 2:
            return pd.DataFrame(columns=["username", "completed_patients", "last_patient"])

        return pd.DataFrame(values[1:], columns=values[0])
    except Exception as e:
        print(f"[get_progress_df] erro: {e}")
        return pd.DataFrame(columns=["username", "completed_patients", "last_patient"])


@st.cache_data(ttl=30)
def get_all_labels_df(_dl):
    """Busca todas as labels de uma vez e mantém cache curto"""
    service = _dl._get_sheets_service()
    if not service:
        return None

    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=_dl.spreadsheet_id,
            range=f"{_dl.sheet_name}!A:AB"
        ).execute()
        values = result.get("values", [])
        if not values or len(values) < 2:
            return None

        return pd.DataFrame(values[1:], columns=values[0])
    except Exception as e:
        print(f"[get_all_labels_df] erro: {e}")
        return None


# ---------------- PATIENT TRACKER ---------------- #

class PatientTracker:
    def __init__(self, sheet_name: str = "progress_tracking"):
        """
        :param sheet_name: Nome da aba no Google Sheets dedicada ao tracking
        """
        self.dl = DataLoader()
        self.sheet_name = sheet_name

    def _write_progress_df(self, df: pd.DataFrame) -> bool:
        """Escreve o progresso atualizado na planilha"""
        service = self.dl._get_sheets_service()
        if not service:
            return False

        try:
            body = {
                "values": [df.columns.tolist()] + df.values.tolist(),
                "majorDimension": "ROWS"
            }
            service.spreadsheets().values().update(
                spreadsheetId=self.dl.spreadsheet_id,
                range=f"{self.sheet_name}!A1",
                valueInputOption="RAW",
                body=body
            ).execute()
            return True
        except Exception as e:
            print(f"Error writing progress to Sheets: {e}")
            return False

    def get_completed_patients(self, username: str) -> Set[str]:
        df = get_progress_df(self.dl, self.sheet_name)
        row = df[df["username"] == username]
        if row.empty:
            return set()
        completed = row.iloc[0]["completed_patients"]
        return set(completed.split(";")) if completed else set()

    def mark_patient_completed(self, username: str, maskedid: str) -> bool:
        df = get_progress_df(self.dl, self.sheet_name)
        if username not in df["username"].values:
            # usuário novo
            new_row = pd.DataFrame([{
                "username": username,
                "completed_patients": maskedid,
                "last_patient": maskedid
            }])
            df = pd.concat([df, new_row], ignore_index=True)
        else:
            idx = df.index[df["username"] == username][0]
            completed = df.at[idx, "completed_patients"]
            completed_set = set(completed.split(";")) if completed else set()
            if maskedid not in completed_set:
                completed_set.add(maskedid)
                df.at[idx, "completed_patients"] = ";".join(sorted(completed_set))
                df.at[idx, "last_patient"] = maskedid

        return self._write_progress_df(df)

    def get_available_patients(self, username: str, all_patients: List[str]) -> List[str]:
        completed = self.get_completed_patients(username)
        available = [p for p in all_patients if p not in completed]
        return sorted(available)

    def get_user_stats(self, username: str, total_patients: int) -> Dict:
        completed = self.get_completed_patients(username)
        completed_count = len(completed)
        remaining_count = total_patients - completed_count
        completion_percentage = (completed_count / total_patients * 100) if total_patients > 0 else 0

        # carregar last_patient da planilha
        df = get_progress_df(self.dl, self.sheet_name)
        last_patient = None
        row = df[df["username"] == username]
        if not row.empty:
            last_patient = row.iloc[0]["last_patient"]

        return {
            "username": username,
            "completed_count": completed_count,
            "remaining_count": remaining_count,
            "total_patients": total_patients,
            "completion_percentage": completion_percentage,
            "last_patient": last_patient
        }

    def get_all_users_stats(self, total_patients: int) -> List[Dict]:
        df = get_progress_df(self.dl, self.sheet_name)
        stats = []
        for _, row in df.iterrows():
            completed = set(row["completed_patients"].split(";")) if row["completed_patients"] else set()
            stats.append({
                "username": row["username"],
                "completed_count": len(completed),
                "remaining_count": total_patients - len(completed),
                "total_patients": total_patients,
                "completion_percentage": (len(completed) / total_patients * 100) if total_patients > 0 else 0,
                "last_patient": row["last_patient"]
            })
        return sorted(stats, key=lambda x: x["completion_percentage"], reverse=True)

    def reset_user_progress(self, username: str) -> bool:
        df = get_progress_df(self.dl, self.sheet_name)
        if username in df["username"].values:
            df = df[df["username"] != username]
            return self._write_progress_df(df)
        return False

    def export_progress_report(self) -> Dict:
        df = get_progress_df(self.dl, self.sheet_name)
        report = {
            "export_timestamp": pd.Timestamp.now().isoformat(),
            "total_users": len(df),
            "users": {}
        }
        for _, row in df.iterrows():
            completed = set(row["completed_patients"].split(";")) if row["completed_patients"] else set()
            report["users"][row["username"]] = {
                "completed_patients": list(completed),
                "total_completed": len(completed),
                "last_patient": row["last_patient"],
            }
        return report

    def auto_mark_completed_patients(self, username: str, all_patients: List[str], df: pd.DataFrame) -> List[str]:
        """
        Varre e marca pacientes já completados pelo usuário, sem estourar quota
        e SEM confundir pacientes (filtro por maskedid).
        """
        newly_completed = []
        labels_df = get_all_labels_df(self.dl)
        if labels_df is None:
            return newly_completed

        try:
            # Normaliza tipos e filtra por usuário atual
            labels_df["maskedid"] = labels_df["maskedid"].astype(str)
            labels_df["eye"] = labels_df["eye"].astype(str)
            labels_df["vf_number"] = labels_df["vf_number"].astype(str)
            labels_user = labels_df[labels_df["username"] == username]

            for maskedid in all_patients:
                if maskedid in self.get_completed_patients(username):
                    continue

                df_patient = df[df["maskedid"] == maskedid]
                if df_patient.empty:
                    continue

                # Esperado para ESTE paciente
                expected = {(str(r["eye"]), str(int(r["visual_field_number"]))) for _, r in df_patient.iterrows()}

                # ENCONTRADO somente para ESTE paciente
                labels_patient = labels_user[labels_user["maskedid"] == str(maskedid)]
                found = {(row["eye"], row["vf_number"]) for _, row in labels_patient.iterrows()}

                if expected.issubset(found):
                    if self.mark_patient_completed(username, maskedid):
                        newly_completed.append(maskedid)

            return newly_completed

        except Exception as e:
            print(f"[auto_mark_completed_patients] erro: {e}")
            return []

    def check_patient_completion(self, username: str, maskedid: str, df_patient: pd.DataFrame) -> bool:
        """
        Confere se TODOS os exames do paciente estão salvos na planilha para ESTE usuário.
        """
        labels_df = get_all_labels_df(self.dl)
        if labels_df is None:
            return False

        try:
            # Filtra por usuário e paciente
            labels_df["maskedid"] = labels_df["maskedid"].astype(str)
            labels_df["eye"] = labels_df["eye"].astype(str)
            labels_df["vf_number"] = labels_df["vf_number"].astype(str)

            labels_user = labels_df[labels_df["username"] == username]
            labels_patient = labels_user[labels_user["maskedid"] == str(maskedid)]

            expected = {(str(r["eye"]), str(int(r["visual_field_number"]))) for _, r in df_patient.iterrows()}
            found = {(row["eye"], row["vf_number"]) for _, row in labels_patient.iterrows()}

            return expected.issubset(found)

        except Exception as e:
            print(f"[check_patient_completion] erro: {e}")
            return False
