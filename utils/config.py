"""
Configuração do app de labeling (versão local/offline).

Caminhos de dados e a taxonomia de rótulos de campo visual. Os caminhos podem ser
sobrescritos pelo labeler_config.yaml na raiz do projeto.
"""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT_DIR = Path(__file__).resolve().parents[1]

# -----------------------------
# Configuração por máquina (labeler_config.yaml)
# -----------------------------
_CONFIG_PATH = ROOT_DIR / "labeler_config.yaml"


def _load_machine_config() -> dict:
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


_cfg = _load_machine_config()

LABELER_NAME: str = str(_cfg.get("labeler_name", "")).strip()

# Caminhos (relativos à raiz, a menos que absolutos no yaml)
def _resolve(key: str, default: Path) -> Path:
    val = _cfg.get(key)
    if not val:
        return default
    p = Path(val)
    return p if p.is_absolute() else (ROOT_DIR / p)


MANIFEST_PATH = _resolve("manifest_path", ROOT_DIR / "data" / "prepared" / "manifest.csv")
IMAGES_DIR = _resolve("images_dir", ROOT_DIR / "data" / "prepared" / "images")
OUTPUT_DIR = _resolve("output_dir", ROOT_DIR / "labels")

# -----------------------------
# UI
# -----------------------------
PAGE_TITLE = "Visual Field Labeling Tool"
ORGANIZATION_NAME = "Glaucoma and Data Science Laboratory"
INSTITUTION_NAME = "Bascom Palmer Eye Institute"

# Olhos: R (direito) -> coluna esquerda; L (esquerdo) -> coluna direita
EYES = ["R", "L"]
EYE_LABELS = {"R": "Right Eye (OD)", "L": "Left Eye (OS)"}

# -----------------------------
# Taxonomia de rótulos
# -----------------------------
# Coluna 1: sempre visível, sem opção "Null"
NORMALITY = ["Normal", "Abnormal"]
RELIABILITY = ["Reliable", "Unreliable"]

# Coluna 2: defeitos glaucomatosos (revelação progressiva, começam em "Null")
G_DEFECT = [
    "Null", "Central Loss", "Paracentral Loss", "Nasal Step", "Temporal Wedge",
    "Partial Arcuate Defect", "Complete Arcuate Defect", "Altitudinal Defect",
    "Generalized Constriction", "Generalized Reduced Sensitivity",
    "Total Loss of Field", "Unclassifiable",
]
G_POSITION = ["Null", "Superior", "Inferior"]

# Coluna 3: defeitos não-glaucomatosos
NG_DEFECT = [
    "Null", "Hemianopia", "Quadranopia", "Non-glaucomatous Central Loss",
    "Enlarged Blind Spot",
]
NG_POSITION = [
    "Null", "Nasal", "Temporal", "Superior Nasal", "Inferior Nasal",
    "Superior Temporal", "Inferior Temporal",
]

# Coluna 4: artefatos
ARTIFACT = [
    "Null", "Upper Eyelid Artifact", "Lens Rim Artifact / Peripheral Rim",
    "Cloverleaf Defect", "Blind Spot Absence", "Trigger Happy",
]

# Opções por chave de rótulo
OPTIONS = {
    "normality": NORMALITY,
    "reliability": RELIABILITY,
    "gdefect1": G_DEFECT, "gposition1": G_POSITION,
    "gdefect2": G_DEFECT, "gposition2": G_POSITION,
    "gdefect3": G_DEFECT, "gposition3": G_POSITION,
    "ngdefect1": NG_DEFECT, "ngposition1": NG_POSITION,
    "ngdefect2": NG_DEFECT, "ngposition2": NG_POSITION,
    "ngdefect3": NG_DEFECT, "ngposition3": NG_POSITION,
    "artifact1": ARTIFACT,
    "artifact2": ARTIFACT,
}

# Ordem canônica de todos os campos de rótulo (para salvar/copiar/CSV)
LABEL_FIELDS = [
    "normality", "reliability",
    "gdefect1", "gposition1", "gdefect2", "gposition2", "gdefect3", "gposition3",
    "ngdefect1", "ngposition1", "ngdefect2", "ngposition2", "ngdefect3", "ngposition3",
    "artifact1", "artifact2",
    "comment",
]

# Cadeias de defeito/posição com revelação progressiva (coluna -> lista de pares)
G_CHAIN = [("gdefect1", "gposition1"), ("gdefect2", "gposition2"), ("gdefect3", "gposition3")]
NG_CHAIN = [("ngdefect1", "ngposition1"), ("ngdefect2", "ngposition2"), ("ngdefect3", "ngposition3")]


def default_value(field: str) -> str:
    """Valor inicial de um campo: 'Null' quando existe, senão a 1ª opção."""
    if field == "comment":
        return ""
    opts = OPTIONS.get(field, [])
    if "Null" in opts:
        return "Null"
    return opts[0] if opts else ""
