
import pathlib


VF_IMAGES_DIR = "./data/"
OCT_IMAGES_DIR = "./data/"

HERO_PATH = pathlib.Path("./source/AdobeStock_743049872-2500x1092.jpeg")
BADGE_PATH = pathlib.Path("./source/BPEI_animated.gif")


# ------------  Helper funcs ------------------------------------------ #
EXTS = (".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG", ".tiff", ".TIFF", ".bmp", ".BMP", ".gif", ".GIF", ".pdf", ".PDF", ".eps", ".EPS", ".svg", ".SVG", ".webp", ".WEBP", ".heic", ".HEIC", ".raw", ".RAW", ".cr2", ".CR2", ".nef", ".NEF", ".orf", ".ORF", ".sr2", ".SR2")


# Default values for form fields (kept for backward compatibility)
DEFAULTS = {
    'vf_od': None,
    'oct_od': None,
    'vf_os': None,
    'oct_os': None,
    'd1_vf_od': None,
    'd2_vf_od': None,
    'd1_vf_os': None,
    'd2_vf_os': None,
    'd1_oct_od': None,
    'd2_oct_od': None,
    'd1_oct_os': None,
    'd2_oct_os': None
}

# Cache settings
MAX_CACHE_SIZE = 5
CACHE_EXPIRY_HOURS = 24

# File paths
LABELS_DIR = "labels"
DATABASE_PATH = "data/fake_patients_interface.csv"

# UI Settings
PAGE_TITLE = "Glaucoma Progression Interface - Labeling"
LAYOUT = "wide"
SIDEBAR_STATE = "expanded"

# Image display settings
SCROLLABLE_BOX_HEIGHT = 450
IMAGE_QUALITY = 'high'

# Date format for saving
DATE_FORMAT = "%Y-%m-%d"
TIMESTAMP_FORMAT = "%Y-%m-%d, %H:%M:%S"
FILENAME_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"

# Validation settings
MAX_IMAGE_SIZE_MB = 50
SUPPORTED_MODALITIES = ['VF', 'OCT']
SUPPORTED_EYES = ['OD', 'OS']

# Progress status options
PROGRESSION_STATUS_OPTIONS = ["Progressed", "Not Progressed"]

# Specialist evaluation keys
EVALUATION_KEYS = ["vf_od", "oct_od", "vf_os", "oct_os"]

# Organization info
ORGANIZATION_NAME = "Glaucoma and Data Science Laboratory"
INSTITUTION_NAME = "Bascom Palmer Eye Institute"