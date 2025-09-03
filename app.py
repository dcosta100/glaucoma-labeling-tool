# ─────────────────────────────────────────────────────────────────────────────
# Glaucoma Progression Interface — Login page : Last update September 1, 2025
# ─────────────────────────────────────────────────────────────────────────────
import streamlit as st
import base64
from utils.config import HERO_PATH, BADGE_PATH, SPECIALIST_IDS

st.set_page_config(page_title="Glaucoma Progression Interface", layout="wide")

# --------------------------------------------------------------------------- #
# Session-state keys
# --------------------------------------------------------------------------- #
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "specialist_name" not in st.session_state:
    st.session_state.specialist_name = ""

def fancy_login():
    hero_b64 = base64.b64encode(HERO_PATH.read_bytes()).decode() if HERO_PATH.exists() else ""
    badge_b64 = base64.b64encode(BADGE_PATH.read_bytes()).decode()

    # CSS
    st.markdown(f"""
    <style>
        html, body, .stApp {{ height: 100%; margin: 0; background:transparent; }}
        .hero {{
            position: fixed; inset: 0;
            background: url('data:image/jpeg;base64,{hero_b64}') center/cover no-repeat;
            filter: brightness(0.65); z-index: -1;
        }}
        .badge-logo {{ position: absolute; top: 18%; left: -1.5%; width: 171px; z-index: 2; }}
        .login-card {{
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            background-color: rgba(255, 255, 255, 0);
            padding: 40px; border-radius: 12px; width: 800px;
            text-align: left; z-index: 5;
        }}
        div[data-testid="stForm"] {{ border: none !important; box-shadow: none !important; }}
        div[data-baseweb="input"] {{ width: 700px; margin: 0; }}
        #MainMenu, footer {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="hero"></div>', unsafe_allow_html=True)
    st.markdown(f'<img class="badge-logo" src="data:image/gif;base64,{badge_b64}" alt="BPEI badge" />', unsafe_allow_html=True)

    st.markdown('<div class="login-card">', unsafe_allow_html=True)

    st.markdown(
    "<h2 style='color:#fff; font-size:48px; margin-left:156px; margin-bottom:20px;'>"
    "Glaucoma Progression Interface</h2>", unsafe_allow_html=True)

    st.markdown(
        "<p style='color:white; font-size:26px; margin-top:50px; margin-left:15px; margin-bottom:17px;'>"
        "Enter your <b>Access&nbsp;ID</b>:</p>", unsafe_allow_html=True)

    with st.form("login_form"):
        entered = st.text_input("Interface ID", "", placeholder="e.g. 117", label_visibility="collapsed")
        submit = st.form_submit_button("Proceed")

    st.markdown('</div>', unsafe_allow_html=True)

    if submit:
        if entered in SPECIALIST_IDS:
            st.session_state.logged_in = True
            st.session_state.specialist_name = SPECIALIST_IDS[entered]
            st.session_state.show_welcome = True
            st.rerun()
        else:
            st.markdown("""
                <style>
                    .custom-error-box {
                        color: white; background-color: #ff4b4b;
                        padding: 12px 20px; border-radius: 10px;
                        width: 700px; height: 42px;
                        margin-top: 10px; text-align: left;
                        font-weight: 500; font-size: 16px;
                        display: flex; align-items: center;
                    }
                </style>
                <div class="custom-error-box">
                    ❌ Unknown ID. Need access? Email&nbsp;<b>ali.azizi@med.miami.edu</b>.
                </div>
            """, unsafe_allow_html=True)
            st.stop()

    st.markdown("""
        <style>
            .fixed-footer { position: fixed; left: 0; bottom: 0; width: 100%; text-align: center; z-index: 9999; }
            .fixed-footer p { color: #fff; font-size: 16px; margin: 0; }
        </style>
        <div class="fixed-footer">
            <p>Glaucoma and Data Science Laboratory | Bascom Palmer Eye Institute</p>
        </div>
    """, unsafe_allow_html=True)

# ─── Show login or redirect ────────────────────────────────────────────────
if st.session_state.logged_in:
    st.switch_page("pages/labeling.py")
else:
    fancy_login()