"""
Carregamento do manifest preparado e agrupamento de exames por paciente/olho.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd
import streamlit as st

from utils import config


@st.cache_data(show_spinner=False)
def load_manifest(path_str: str) -> pd.DataFrame:
    """Lê o manifest.csv. Cacheado pelo caminho (string p/ hashing)."""
    df = pd.read_csv(path_str, dtype={"maskedid": str, "eye": str})
    df["visual_field_number"] = df["visual_field_number"].astype(int)
    df = df.sort_values(["maskedid", "eye", "visual_field_number"]).reset_index(drop=True)
    return df


def get_manifest() -> pd.DataFrame:
    if not config.MANIFEST_PATH.exists():
        return pd.DataFrame()
    return load_manifest(str(config.MANIFEST_PATH))


def list_patients(df: pd.DataFrame) -> List[str]:
    """Pacientes em ordem estável (ordem alfabética do maskedid)."""
    return sorted(df["maskedid"].unique().tolist())


def patient_age(df_patient: pd.DataFrame) -> str:
    ages = df_patient["age"].dropna()
    return f"{ages.iloc[0]:.0f}" if not ages.empty else "?"


def exams_by_eye(df_patient: pd.DataFrame, eye: str) -> List[dict]:
    """Exames de um olho, em ordem cronológica (visual_field_number)."""
    sub = df_patient[df_patient["eye"] == eye].sort_values("visual_field_number")
    return sub.to_dict("records")


def image_path(image_filename: str) -> Path:
    return config.IMAGES_DIR / image_filename
