# utils/config.py
from pathlib import Path
import os

# -----------------------------
# Raiz do projeto (pasta acima de utils/)
# -----------------------------
ROOT_DIR = Path(__file__).resolve().parents[1]

# -----------------------------
# Caminhos principais (como Path)
# -----------------------------
DATA_DIR = ROOT_DIR / "data"
LABELS_DIR = ROOT_DIR / "labels"
PDF_DIR = DATA_DIR / "pdfs"

# Imagens/ativos opcionais (ajuste se sua estrutura diferir)
HERO_PATH = ROOT_DIR / "source" / "AdobeStock_743049872-2500x1092.jpeg"
BADGE_PATH = ROOT_DIR / "source" / "BPEI_animated.gif"

# Arquivo CSV padrão
CSV_PATH = DATA_DIR / "opv_24-2_prepared.csv"
PDF_DIR = "C:\\Users\\dxr1276\\Box\\PROJECTS\\VF_GRADINGS\\hfa_printouts"

# -----------------------------
# Overrides por variável de ambiente (opcional)
# -----------------------------
CSV_PATH = Path(os.getenv("CSV_PATH", CSV_PATH))
PDF_DIR = Path(os.getenv("PDF_DIR", PDF_DIR))
LABELS_DIR = Path(os.getenv("LABELS_DIR", LABELS_DIR))

# Garante que a pasta de labels exista
LABELS_DIR.mkdir(parents=True, exist_ok=True)

# Versões em string (para libs que exigem str)
CSV_PATH_STR = str(CSV_PATH)
PDF_DIR_STR = str(PDF_DIR)
LABELS_DIR_STR = str(LABELS_DIR)

# -----------------------------
# Constantes de UI/rotulagem
# -----------------------------
VISUAL_FIELD_LABELS = {
    'normality': ['Normal', 'Abnormal'],
    'reliability': ['Reliable', 'Unreliable'],
    'gdefect1': ['Central Loss', 'Paracentral Loss', 'Nasal Step', 'Temporal Wedge',
                 'Particual Arcuate Defect', 'Complete Arcuate Defect', 'Atitudinal Defect',
                 'Generalized Constrcition', 'Generalized Reduced Sensitivity', 'Total Loss of Field', 'Unclassifiable'],
    'gdefect2': ['Central Loss', 'Paracentral Loss', 'Nasal Step', 'Temporal Wedge',
                 'Particual Arcuate Defect', 'Complete Arcuate Defect', 'Atitudinal Defect',
                 'Generalized Constrcition', 'Generalized Reduced Sensitivity', 'Total Loss of Field', 'Unclassifiable'],
    'gdefect3': ['Central Loss', 'Paracentral Loss', 'Nasal Step', 'Temporal Wedge',
                 'Particual Arcuate Defect', 'Complete Arcuate Defect', 'Atitudinal Defect',
                 'Generalized Constrcition', 'Generalized Reduced Sensitivity', 'Total Loss of Field', 'Unclassifiable'],
    'gposition1': ['Superior', 'Inferior'],
    'gposition2': ['Superior', 'Inferior'],
    'gposition3': ['Superior', 'Inferior'],
    'ngdefect1': ['Hemianopia', 'Quadranopia', 'Non-glaucomatous Central Loss', 'Enlarged Blind Spot'],
    'ngdefect2': ['Hemianopia', 'Quadranopia', 'Non-glaucomatous Central Loss', 'Enlarged Blind Spot'],
    'ngdefect3': ['Hemianopia', 'Quadranopia', 'Non-glaucomatous Central Loss', 'Enlarged Blind Spot'],
    'ngposition1': ['Nasal', 'Temporal', 'Superior Nasal', 'Inferior Nasal', 'Superior Temporal', 'Inferior Temporal'],
    'ngposition2': ['Nasal', 'Temporal', 'Superior Nasal', 'Inferior Nasal', 'Superior Temporal', 'Inferior Temporal'],
    'ngposition3': ['Nasal', 'Temporal', 'Superior Nasal', 'Inferior Nasal', 'Superior Temporal', 'Inferior Temporal'],
    'artifact1': ['Upper Eyelid Artifact', 'Lens Rim Artifact/ Peripheral Rim', 'Cloverleaf Defect', 'Blind Spot Absence', 'Trigger Happy'],
    'artifact2': ['Upper Eyelid Artifact', 'Lens Rim Artifact/ Peripheral Rim', 'Cloverleaf Defect', 'Blind Spot Absence', 'Trigger Happy'],
    'comment': ''
}

EYES = ["R", "L"]

# Extensões aceitas
EXTS = (".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG", ".tiff", ".TIFF",
        ".bmp", ".BMP", ".gif", ".GIF", ".pdf", ".PDF", ".eps", ".EPS",
        ".svg", ".SVG", ".webp", ".WEBP", ".heic", ".HEIC", ".raw", ".RAW",
        ".cr2", ".CR2", ".nef", ".NEF", ".orf", ".ORF", ".sr2", ".SR2")

# Valores padrão/compatibilidade
DEFAULTS = {
    'vf_od': None, 'oct_od': None, 'vf_os': None, 'oct_os': None,
    'd1_vf_od': None, 'd2_vf_od': None, 'd1_vf_os': None, 'd2_vf_os': None,
    'd1_oct_od': None, 'd2_oct_od': None, 'd1_oct_os': None, 'd2_oct_os': None
}

# Cache
MAX_CACHE_SIZE = 5
CACHE_EXPIRY_HOURS = 24

# UI
PAGE_TITLE = "Glaucoma Progression Interface - Labeling"
LAYOUT = "wide"
SIDEBAR_STATE = "expanded"
SCROLLABLE_BOX_HEIGHT = 450
IMAGE_QUALITY = 'high'

# Datas / formatos
DATE_FORMAT = "%Y-%m-%d"
TIMESTAMP_FORMAT = "%Y-%m-%d, %H:%M:%S"
FILENAME_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"

# Validações
MAX_IMAGE_SIZE_MB = 50
SUPPORTED_MODALITIES = ['VF', 'OCT']
SUPPORTED_EYES = ['OD', 'OS']
PROGRESSION_STATUS_OPTIONS = ["Progressed", "Not Progressed"]
EVALUATION_KEYS = ["vf_od", "oct_od", "vf_os", "oct_os"]

# Organização
ORGANIZATION_NAME = "Glaucoma and Data Science Laboratory"
INSTITUTION_NAME = "Bascom Palmer Eye Institute"

# Exposição explícita dos símbolos principais (útil para linters/auto-complete)
__all__ = [
    "ROOT_DIR", "DATA_DIR", "LABELS_DIR", "PDF_DIR", "CSV_PATH",
    "HERO_PATH", "BADGE_PATH",
    "CSV_PATH_STR", "PDF_DIR_STR", "LABELS_DIR_STR",
    "VISUAL_FIELD_LABELS", "EYES", "EXTS", "DEFAULTS",
    "MAX_CACHE_SIZE", "CACHE_EXPIRY_HOURS",
    "PAGE_TITLE", "LAYOUT", "SIDEBAR_STATE", "SCROLLABLE_BOX_HEIGHT", "IMAGE_QUALITY",
    "DATE_FORMAT", "TIMESTAMP_FORMAT", "FILENAME_TIMESTAMP_FORMAT",
    "MAX_IMAGE_SIZE_MB", "SUPPORTED_MODALITIES", "SUPPORTED_EYES",
    "PROGRESSION_STATUS_OPTIONS", "EVALUATION_KEYS",
    "ORGANIZATION_NAME", "INSTITUTION_NAME"
]
