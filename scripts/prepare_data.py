"""
Prepara os dados para distribuição local do app de labeling.

Lê o export Stata (.dta), mantém apenas os exames cujo PDF existe na pasta de
origem, calcula idade e número do campo visual, escreve um manifest.csv enxuto e
converte cada PDF em PNG. Apenas o manifest + a pasta de PNGs precisam ser
distribuídos aos labelers — o .dta e os PDFs originais ficam com você.

Uso:
    python scripts/prepare_data.py
    python scripts/prepare_data.py --zoom 2.0 --force

Re-rodar é seguro: PNGs já gerados são pulados (use --force para refazer).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DTA_PATH = ROOT / "data" / "opv_export_masked_20220901.dta"
PDF_DIR = ROOT / "data" / "hfa_gradings"
OUT_DIR = ROOT / "data" / "prepared"
IMG_DIR = OUT_DIR / "images"
MANIFEST_PATH = OUT_DIR / "manifest.csv"

# Colunas clínicas opcionais que ajudam o labeler (coalescidas/renomeadas no manifest)
CLINICAL = {
    "psd": "psd",
    "vfi": "vfi",
    "ght": "ght",
    "fixation_loss": "fixation_loss",
    "falsepositivepercent": "false_pos",
    "falsenegativepercent": "false_neg",
}


def build_manifest(pdf_names: set[str]) -> pd.DataFrame:
    df = pd.read_stata(DTA_PATH, convert_categoricals=False)

    # Mantém só exames cujo PDF está presente na pasta de origem
    df = df[df["pdf_filename"].isin(pdf_names)].copy()
    if df.empty:
        return df

    # Idade no momento do exame
    dob = pd.to_datetime(df["aedob_shift"], errors="coerce")
    exam = pd.to_datetime(df["aeexamdate_shift"], errors="coerce")
    df["exam_date"] = exam.dt.strftime("%Y-%m-%d")
    df["age"] = ((exam - dob).dt.days / 365.25).round(1)

    # MD: usa 24-2 quando disponível, senão 30-2
    md_242 = pd.to_numeric(df.get("md_242"), errors="coerce")
    md_302 = pd.to_numeric(df.get("md_302"), errors="coerce")
    df["md"] = md_242.fillna(md_302).round(2)

    # Número do campo visual: ordem cronológica dentro de cada (paciente, olho)
    df = df.sort_values(["maskedid", "eye", "exam_date"])
    df["visual_field_number"] = df.groupby(["maskedid", "eye"]).cumcount() + 1

    # Nome do PNG (mesmo stem do PDF)
    df["image_filename"] = df["pdf_filename"].str.replace(r"\.pdf$", ".png", regex=True)

    cols = [
        "maskedid", "eye", "visual_field_number", "exam_date", "age",
        "testpattern", "md", "image_filename", "pdf_filename", "opv_filename",
    ]
    for src, dst in CLINICAL.items():
        if src in df.columns:
            df[dst] = df[src]
            cols.append(dst)

    out = df[[c for c in cols if c in df.columns]].reset_index(drop=True)
    return out


def convert_pdfs(manifest: pd.DataFrame, zoom: float, force: bool) -> tuple[int, int]:
    import fitz  # PyMuPDF

    IMG_DIR.mkdir(parents=True, exist_ok=True)
    converted = skipped = 0
    total = len(manifest)

    for i, row in manifest.reset_index(drop=True).iterrows():
        png_path = IMG_DIR / row["image_filename"]
        if png_path.exists() and not force:
            skipped += 1
            continue
        pdf_path = PDF_DIR / row["pdf_filename"]
        if not pdf_path.exists():
            print(f"  ! PDF ausente, pulando: {row['pdf_filename']}")
            continue
        try:
            doc = fitz.open(str(pdf_path))
            page = doc.load_page(0)
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
            pix.save(str(png_path))
            doc.close()
            converted += 1
        except Exception as e:  # noqa: BLE001
            print(f"  ! erro convertendo {row['pdf_filename']}: {e}")
        if (i + 1) % 25 == 0 or i + 1 == total:
            print(f"  {i + 1}/{total} processados...")

    return converted, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zoom", type=float, default=2.0,
                        help="Fator de zoom na rasterização do PDF (default 2.0).")
    parser.add_argument("--force", action="store_true",
                        help="Reconverte PNGs mesmo que já existam.")
    parser.add_argument("--no-images", action="store_true",
                        help="Só gera o manifest, sem converter imagens.")
    args = parser.parse_args()

    if not DTA_PATH.exists():
        print(f"ERRO: .dta não encontrado em {DTA_PATH}")
        return 1
    if not PDF_DIR.exists():
        print(f"ERRO: pasta de PDFs não encontrada em {PDF_DIR}")
        return 1

    pdf_names = {p.name for p in PDF_DIR.glob("*.pdf")}
    print(f"PDFs encontrados na origem: {len(pdf_names)}")

    print("Construindo manifest a partir do .dta...")
    manifest = build_manifest(pdf_names)
    if manifest.empty:
        print("Nenhum exame casou com os PDFs presentes. Nada a fazer.")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(MANIFEST_PATH, index=False)
    n_patients = manifest["maskedid"].nunique()
    print(f"Manifest escrito: {MANIFEST_PATH}")
    print(f"  {len(manifest)} exames | {n_patients} pacientes")

    if args.no_images:
        return 0

    print("Convertendo PDFs -> PNG...")
    converted, skipped = convert_pdfs(manifest, args.zoom, args.force)
    print(f"Concluído: {converted} convertidos, {skipped} já existentes.")
    print(f"PNGs em: {IMG_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
