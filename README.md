# Visual Field Labeling Tool (local)

Streamlit tool for grading visual fields (HFA 24-2 / 30-2) of glaucoma patients.
It runs **locally** on each machine: labelers receive the prepared images and the
labels are saved on their own computer, to be consolidated later.

Created by Douglas Costa MD PhD.

---

## Overall workflow

1. **You (preparation)** run `scripts/prepare_data.py` to generate:
   - `data/prepared/manifest.csv` — one exam per row (patient, eye, field number,
     age, date, MD/PSD/VFI/GHT, image filename);
   - `data/prepared/images/*.png` — the printouts converted from PDF to PNG.
2. **Distribution** — send each labeler: the code, `manifest.csv`, the `images/`
   folder and the `reference/` guide. (The `.dta` and original PDFs stay with you.)
3. **Each labeler** fills in `labeler_config.yaml` with their name and runs the app.
4. **Collection** — each labeler sends you back their `labels/<name>/` folder,
   especially the consolidated `labels_<name>.csv`.

---

## Data preparation (you)

```bash
pip install -r requirements.txt
python scripts/prepare_data.py            # generate manifest + PNGs
python scripts/prepare_data.py --force    # re-convert existing PNGs
python scripts/prepare_data.py --no-images  # update the manifest only
```

The script reads `data/opv_export_masked_20220901.dta`, keeps only the exams whose
PDF is present in `data/hfa_gradings/`, computes the patient age and the visual
field number (chronological order per eye) and converts each PDF to PNG. It is safe
to re-run as new PDFs arrive — PNGs that already exist are skipped.

---

## Packaging for labelers (no Python install)

To hand the tool to someone who does not have Python, build a self-contained
package on your machine:

```powershell
powershell -ExecutionPolicy Bypass -File build_package.ps1
```

This produces `dist/glaucoma-labeling-tool.zip` containing the app, the prepared
data and a bundled `uv.exe`. The labeler unzips it and **double-clicks
`Start Labeling.bat`** — the first run downloads Python and dependencies
automatically (needs internet once), then the app opens in the browser. The app
asks for their name on first launch and remembers it.

## Labeler usage (manual / development)

1. Run the app:
   ```bash
   pip install streamlit pandas pyyaml pillow
   streamlit run app.py
   ```
   On the first launch it asks for your name and saves it to `labeler_config.yaml`.
2. For each patient, all visual fields are shown side by side:
   **right eye (R) in the left column**, **left eye (L) in the right column**,
   in chronological order.

### Automatic replication (cascade)

- The **first field (oldest)** of each eye is the source.
- The following fields of the same eye **automatically copy** the source labels.
- Editing **any label of a following field** changes only that field — it becomes
  independent and stops following the source.
- A **"↻ Copy from #1"** button lets you re-attach a field to the source.

The **Save** and **Save and next patient** buttons store every field of the patient.

### Reference guide

The sidebar has a **download button** for the Visual Field Patterns grading guide,
available whenever in doubt about a classification.

---

## Where labels are saved

```
labels/<name>/
  progress.json                       # completed patients + resume point
  json/<maskedid>__<eye>__<n>.json    # per-exam backup
  labels_<name>.csv                   # consolidated (one row per visual field)
```

The `labels_<name>.csv` is the file to consolidate across all labelers.
