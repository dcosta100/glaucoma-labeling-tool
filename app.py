# ─────────────────────────────────────────────────────────────────────────────
# Glaucoma Progression Interface — Login page : Last update September 1, 2025
# ─────────────────────────────────────────────────────────────────────────────
import streamlit as st
import streamlit_authenticator as stauth
import base64
from utils.config import HERO_PATH, BADGE_PATH
import yaml
from yaml.loader import SafeLoader
from utils import labeling


st.set_page_config(page_title="Glaucoma Progression Interface", layout="wide")


with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)


authenticator.login()

st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.get('authentication_status'):
    st.session_state['specialist_name'] = st.session_state.username
    st.session_state.show_welcome = True
    labeling.labeling_page()
    with st.sidebar:
        authenticator.logout(use_container_width=True)
elif st.session_state['authentication_status'] is False:
    st.error('Username/password is incorrect')
else:
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

    st.markdown("""
        <style>
            .fixed-footer { position: fixed; left: 0; bottom: 0; width: 100%; text-align: center; z-index: 9999; }
            .fixed-footer p { color: #fff; font-size: 16px; margin: 0; }
        </style>
        <div class="fixed-footer">
            <p>Glaucoma and Data Science Laboratory | Bascom Palmer Eye Institute</p>
        </div>
    """, unsafe_allow_html=True)