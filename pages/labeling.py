# ─────────────────────────────────────────────────────────────────────────────
# Glaucoma Progression Interface — Labeling page : Last update September 1, 2025
# ─────────────────────────────────────────────────────────────────────────────
import streamlit as st
import numpy as np
import pandas as pd
import base64
import os
from datetime import datetime
from io import BytesIO
import plotly.graph_objects as go
from utils.config import VF_IMAGES_DIR, OCT_IMAGES_DIR, EXTS
from utils import dataloader

# Redirect to login if not authenticated
if not st.session_state.get("logged_in", False):
    st.switch_page("app.py")

st.set_page_config(page_title="Glaucoma Progression Interface - Labeling", layout="wide", initial_sidebar_state="expanded")

timestamp = datetime.now().strftime("%Y-%m-%d, %H:%M:%S")

# --------------------------------------------------------------------------- #
# Main interface
# --------------------------------------------------------------------------- #
if st.session_state.get("show_welcome", False):
    st.success(f"Welcome, Dr. {st.session_state.specialist_name}!")
    st.session_state.show_welcome = False

# Logged in as
st.markdown(
    f"<p style='text-align:right; color:gray;'>Logged in as: "
    f"<strong>Dr. {st.session_state.specialist_name}</strong></p>",
    unsafe_allow_html=True,
)

#------------  CSS ---------------------------------------------------- #
st.markdown(
    """
    <style>
        .scrollable-box{height:450px; overflow-y:scroll; padding-right:10px;
                        border:1px solid #ddd;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------  Header ------------------------------------------------- #
st.markdown(
    """
    <h1 style='text-align:center;'>Glaucoma Progression Interface</h1>
    <p style='text-align:center; font-size:18px; color:gray;'>
        A Collaborative Platform for Glaucoma Specialists
    </p>
    """,
    unsafe_allow_html=True,
)
st.markdown("---")

# ------------  Dummy patient list ------------------------------------ #
patients = {
    "Patient_001": {"Sex": "Male",   "Age": 65},
    "Patient_002": {"Sex": "Female", "Age": 72},
    "Patient_003": {"Sex": "Male",   "Age": 58},
    "Patient_004": {"Sex": "Female", "Age": 67},
    "Patient_005": {"Sex": "Male",   "Age": 75},
}
selected = st.sidebar.selectbox("Select Patient", list(patients.keys()))
if selected:
    st.sidebar.markdown("---")
    st.sidebar.subheader(f"Patient Information: {selected}")
    for k, v in patients[selected].items():
        st.sidebar.write(f"{k}: {v}")

def find_folder(base, pid):
    for fld in os.listdir(base):
        if pid.lower() in fld.lower():
            return os.path.join(base, fld)
    return None

def eye_imgs(base, mod, pid, eye):
    fld = find_folder(base, pid)
    if not fld: return []
    prefix = f"{mod}_{pid}_{eye}_"
    return [os.path.join(fld, f) for f in sorted(os.listdir(fld))
            if f.startswith(prefix) and f.endswith(EXTS)]

def scroll_imgs(img_list, h=450):
    html = ""
    for p in img_list:
        if os.path.exists(p):
            b64 = base64.b64encode(open(p, "rb").read()).decode()
            html += f"<img src='data:image/png;base64,{b64}' style='width:100%; margin-bottom:10px;'/>"
    st.markdown(f"<div class='scrollable-box'>{html}</div>", unsafe_allow_html=True)

def eval_section(key):
    st.markdown("##### Specialist Evaluation")
    stat = st.radio("Progression status:", ["Progressed", "Not Progressed"], key=f"diag_{key}")
    if stat == "Progressed":
        d1, d2 = st.columns(2)
        with d1:
            date1 = st.date_input("First date progression seen:", key=f"d1_{key}")
        with d2:
            date2 = st.date_input("Second date progression seen:", key=f"d2_{key}")
    else:
        date1 = date2 = "N/A"
        st.write("First date progression seen: N/A")
        st.write("Second date progression seen: N/A")
    return stat, date1, date2

# ------------  Load images ------------------------------------------- #
vf_od  = eye_imgs(VF_IMAGES_DIR,  "VF",  selected, "OD")
vf_os  = eye_imgs(VF_IMAGES_DIR,  "VF",  selected, "OS")
oct_od = eye_imgs(OCT_IMAGES_DIR, "OCT", selected, "OD")
oct_os = eye_imgs(OCT_IMAGES_DIR, "OCT", selected, "OS")

# ------------  MD Records Section ------------------------------------ #
date_range = pd.date_range(start='2016-01-01', end='2025-04-30', periods=6)

base_md = {
    "Patient_001": {"OD": [-4, -5, -6, -7, -8, -9],
                    "OS": [-3, -4, -5, -6, -7, -8]},
    "Patient_002": {"OD": [-15.51, -15.10, -16.01, -16.55, -19.97, -21.00],
                    "OS": [-13.70, -13.80, -15.01, -16.50, -16.97, -20.00]},
    "Patient_003": {"OD": [-10, -11, -12, -13, -14, -15],
                    "OS": [-9, -10, -11, -12, -13, -14]},
    "Patient_004": {"OD": [-6, -6.5, -7, -8, -9, -9.5],
                    "OS": [-5, -5.5, -6, -7, -8, -8.5]},
    "Patient_005": {"OD": [-12, -13, -14, -15, -16, -17],
                    "OS": [-11, -12, -13, -14, -15, -16]},
}

md_data = pd.DataFrame({
    "Date": date_range,
    "OD MD (dB)": base_md[selected]["OD"],
    "OS MD (dB)": base_md[selected]["OS"]
})

years = (md_data["Date"] - md_data["Date"].iloc[0]).dt.days / 365.25
slope_od, intercept_od = np.polyfit(years, md_data["OD MD (dB)"], 1)
slope_os, intercept_os = np.polyfit(years, md_data["OS MD (dB)"], 1)

# ------------  Right Eye Section ------------------------------------- #
with st.expander("Right Eye (OD)", expanded=False):
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("VF Printouts (OD)")
        scroll_imgs(vf_od)

        # MD Trend for OD
        with st.expander("Mean Deviation Trend (OD)", expanded=False):
            fig_od = go.Figure()
            fig_od.add_trace(go.Scatter(
                x=md_data["Date"], y=md_data["OD MD (dB)"],
                mode="lines+markers", name="OD",
                hovertemplate="Date: %{x|%Y-%m-%d}<br>OD MD: %{y:.2f} dB"
            ))
            fig_od.add_trace(go.Scatter(
                x=md_data["Date"], y=slope_od * years + intercept_od,
                mode="lines", line=dict(dash="dash", color="orange"),
                name=f"OD slope: {slope_od:.2f} dB/yr"
            ))
            fig_od.update_layout(
                xaxis_title="Date", yaxis_title="MD (dB)",
                hovermode="x unified", template="plotly_white"
            )
            st.plotly_chart(fig_od, use_container_width=True)

        # Evaluation for OD VF
        d_vf_od, d1_vf_od, d2_vf_od = eval_section("vf_od")

    with c2:
        st.subheader("OCT Printouts (OD)")
        scroll_imgs(oct_od)
        d_oct_od, d1_oct_od, d2_oct_od = eval_section("oct_od")

# ------------  Left Eye Section -------------------------------------- #
with st.expander("Left Eye (OS)", expanded=False):
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("VF Printouts (OS)")
        scroll_imgs(vf_os)

        # MD Trend for OS
        with st.expander("Mean Deviation Trend (OS)", expanded=False):
            fig_os = go.Figure()
            fig_os.add_trace(go.Scatter(
                x=md_data["Date"], y=md_data["OS MD (dB)"],
                mode="lines+markers", name="OS",
                hovertemplate="Date: %{x|%Y-%m-%d}<br>OS MD: %{y:.2f} dB"
            ))
            fig_os.add_trace(go.Scatter(
                x=md_data["Date"], y=slope_os * years + intercept_os,
                mode="lines", line=dict(dash="dash", color="orange"),
                name=f"OS slope: {slope_os:.2f} dB/yr"
            ))
            fig_os.update_layout(
                xaxis_title="Date", yaxis_title="MD (dB)",
                hovermode="x unified", template="plotly_white"
            )
            st.plotly_chart(fig_os, use_container_width=True)

        # Evaluation for OS VF
        d_vf_os, d1_vf_os, d2_vf_os = eval_section("vf_os")

    with c2:
        st.subheader("OCT Printouts (OS)")
        scroll_imgs(oct_os)
        d_oct_os, d1_oct_os, d2_oct_os = eval_section("oct_os")

# ------------  Export ------------------------------------------------- #
df = pd.DataFrame([
    {"Patient ID": selected, "Eye": "OD", "Modality": "VF",
     "Progression": d_vf_od,  "First": d1_vf_od,  "Second": d2_vf_od, "Time": timestamp},
    {"Patient ID": selected, "Eye": "OD", "Modality": "OCT",
     "Progression": d_oct_od, "First": d1_oct_od, "Second": d2_oct_od, "Time": timestamp},
    {"Patient ID": selected, "Eye": "OS", "Modality": "VF",
     "Progression": d_vf_os,  "First": d1_vf_os,  "Second": d2_vf_os, "Time": timestamp},
    {"Patient ID": selected, "Eye": "OS", "Modality": "OCT",
     "Progression": d_oct_os, "First": d1_oct_os, "Second": d2_oct_os, "Time": timestamp},
])
buffer = BytesIO()
df.to_excel(buffer, index=False, sheet_name="Progression Evaluations")
st.download_button("📥 Download Excel File",
                   data=buffer.getvalue(),
                   file_name=f"{selected}_progression_evaluations.xlsx",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.markdown("---")
st.write("Glaucoma and Data Science Laboratory | Bascom Palmer Eye Institute")