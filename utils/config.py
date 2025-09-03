
import pathlib


VF_IMAGES_DIR = "/home/fmedeiros/Downloads/glaucoma_interface/data/sample/ali_vf_images/"
OCT_IMAGES_DIR = "/home/fmedeiros/Downloads/glaucoma_interface/data/sample/ali_oct_images/"

# --------------------------------------------------------------------------- #
# 1️⃣ Approved specialists
# --------------------------------------------------------------------------- #
SPECIALIST_IDS = {
    "110": "Felipe A. Medeiros",   "111": "Swarup S. Swaminathan",
    "112": "Gustavo A. Samico",    "113": "Ali Azizi",
    "114": "Rafael Scherer",       "115": "Douglas Da Costa",
    "116": "Aaron S. Rabinowitz",  "117": "Gustavo R. Gameiro",
    "118": "Rohit Muralidhar",     "119": "Natalia Palazoni",
    "120": "Vitoria Palazoni",     "121": "Davina A. Malek",
}

HERO_PATH = pathlib.Path("/home/fmedeiros/Downloads/glaucoma_interface/source/AdobeStock_743049872-2500x1092.jpeg")
BADGE_PATH = pathlib.Path("/home/fmedeiros/Downloads/glaucoma_interface/source/BPEI_animated.gif")


# ------------  Helper funcs ------------------------------------------ #
EXTS = (".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG", ".tiff", ".TIFF", ".bmp", ".BMP", ".gif", ".GIF", ".pdf", ".PDF", ".eps", ".EPS", ".svg", ".SVG", ".webp", ".WEBP", ".heic", ".HEIC", ".raw", ".RAW", ".cr2", ".CR2", ".nef", ".NEF", ".orf", ".ORF", ".sr2", ".SR2")
