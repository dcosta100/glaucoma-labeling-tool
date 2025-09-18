"""
Image Handler for Glaucoma Progression Interface
Handles image loading, processing, and display functionality from DataFrame
"""

import streamlit as st
import pandas as pd
import base64
import os
from utils.config import EXTS
from icecream import ic
from PIL import Image
import fitz
import io
    
def pdf_to_image_fitz(pdf_path: str, page_number: int = 0, zoom: float = 2.0):
    """
    Convert a single page of a PDF to a PIL image using PyMuPDF (fitz).

    :param pdf_path: Path to the PDF file
    :param page_number: Page number to render (starts at 0)
    :param zoom: Zoom factor (e.g., 2.0 for 200% scale)
    :return: PIL.Image or None
    """
    try:
        doc = fitz.open(pdf_path)
        page = doc.load_page(page_number)
        mat = fitz.Matrix(zoom, zoom)  # zoom factor
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_bytes))
        return image
    except Exception as e:
        print(f"Error rendering PDF: {e}")
        return None