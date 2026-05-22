"""
Persistência local dos rótulos e do progresso.

Layout de saída (por labeler):
    <output_dir>/<labeler>/
        progress.json                 -> pacientes concluídos
        json/<maskedid>__<eye>__<vf>.json   -> backup granular por exame
        labels_<labeler>.csv          -> consolidado (1 linha por campo visual)

O CSV consolidado é o arquivo que você junta de todos os labelers no final.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from utils import config

# Metadados copiados do manifest para cada linha salva
META_FIELDS = ["exam_date", "age", "testpattern", "md", "psd", "vfi", "ght",
               "image_filename", "pdf_filename", "opv_filename"]

CSV_COLUMNS = (
    ["labeler", "maskedid", "eye", "visual_field_number"]
    + config.LABEL_FIELDS
    + META_FIELDS
    + ["last_updated"]
)


# ---------------- caminhos ---------------- #

def _user_dir(labeler: str) -> Path:
    d = config.OUTPUT_DIR / labeler
    (d / "json").mkdir(parents=True, exist_ok=True)
    return d


def _progress_path(labeler: str) -> Path:
    return _user_dir(labeler) / "progress.json"


def _json_path(labeler: str, maskedid: str, eye: str, vf: int) -> Path:
    return _user_dir(labeler) / "json" / f"{maskedid}__{eye}__{vf}.json"


def _csv_path(labeler: str) -> Path:
    return _user_dir(labeler) / f"labels_{labeler}.csv"


# ---------------- progresso ---------------- #

def load_progress(labeler: str) -> dict:
    p = _progress_path(labeler)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            pass
    return {"completed": [], "last": None}


def get_completed(labeler: str) -> set:
    return set(load_progress(labeler).get("completed", []))


def mark_completed(labeler: str, maskedid: str) -> None:
    prog = load_progress(labeler)
    completed = set(prog.get("completed", []))
    completed.add(maskedid)
    prog["completed"] = sorted(completed)
    prog["last"] = maskedid
    _progress_path(labeler).write_text(
        json.dumps(prog, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def unmark_completed(labeler: str, maskedid: str) -> None:
    prog = load_progress(labeler)
    completed = set(prog.get("completed", []))
    completed.discard(maskedid)
    prog["completed"] = sorted(completed)
    _progress_path(labeler).write_text(
        json.dumps(prog, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def get_last_viewed(labeler: str) -> Optional[str]:
    """maskedid do último paciente aberto (para retomar de onde parou)."""
    return load_progress(labeler).get("last_viewed")


def set_last_viewed(labeler: str, maskedid: str) -> None:
    prog = load_progress(labeler)
    if prog.get("last_viewed") == maskedid:
        return  # evita reescrita desnecessária a cada rerun
    prog["last_viewed"] = maskedid
    _progress_path(labeler).write_text(
        json.dumps(prog, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# ---------------- rótulos por exame ---------------- #

def load_exam_label(labeler: str, maskedid: str, eye: str, vf: int) -> Optional[dict]:
    p = _json_path(labeler, maskedid, eye, vf)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return None
    return None


def load_patient_labels(labeler: str, maskedid: str) -> Dict[str, dict]:
    """Retorna {f'{eye}|{vf}': record} para todos os exames salvos do paciente."""
    out: Dict[str, dict] = {}
    json_dir = _user_dir(labeler) / "json"
    for f in json_dir.glob(f"{maskedid}__*.json"):
        try:
            rec = json.loads(f.read_text(encoding="utf-8"))
            out[f"{rec['eye']}|{rec['visual_field_number']}"] = rec
        except Exception:  # noqa: BLE001
            continue
    return out


def save_exam_label(labeler: str, maskedid: str, eye: str, vf: int,
                    labels: dict, meta: dict) -> None:
    """Grava o JSON do exame e faz upsert no CSV consolidado."""
    record = {
        "labeler": labeler,
        "maskedid": maskedid,
        "eye": eye,
        "visual_field_number": int(vf),
        "last_updated": datetime.now().isoformat(timespec="seconds"),
    }
    for k in config.LABEL_FIELDS:
        record[k] = labels.get(k, config.default_value(k))
    for k in META_FIELDS:
        record[k] = meta.get(k, "")

    # 1) JSON granular
    _json_path(labeler, maskedid, eye, vf).write_text(
        json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # 2) Upsert no CSV consolidado
    _upsert_csv(labeler, record)


def _upsert_csv(labeler: str, record: dict) -> None:
    path = _csv_path(labeler)
    rows: List[dict] = []
    if path.exists():
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

    key = (record["maskedid"], record["eye"], str(record["visual_field_number"]))
    row_str = {c: ("" if record.get(c) is None else str(record.get(c, ""))) for c in CSV_COLUMNS}

    replaced = False
    for i, r in enumerate(rows):
        if (r.get("maskedid"), r.get("eye"), str(r.get("visual_field_number"))) == key:
            rows[i] = row_str
            replaced = True
            break
    if not replaced:
        rows.append(row_str)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
