# ─────────────────────────────────────────────────────────────────────────────
# Glaucoma Progression Interface — Simple Login : Last update September 18, 2025
# ─────────────────────────────────────────────────────────────────────────────
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from utils import labeling

st.set_page_config(page_title="Glaucoma Progression Interface", layout="wide")

# Load configuration
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Create authenticator
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Login widget
authenticator.login()

# Check authentication
if st.session_state['authentication_status']:
    # User authenticated - show main app
    st.session_state['specialist_name'] = st.session_state['username']
    
    # Logout button in sidebar
    with st.sidebar:
        st.write(f"Welcome **{st.session_state['name']}**")
        authenticator.logout('Logout', 'sidebar')
    
    # Load labeling page
    labeling.labeling_page()

elif st.session_state['authentication_status'] == False:
    # Wrong credentials
    st.error('Username/password is incorrect')

else:
    # Not logged in - show login page
    st.markdown("""
        <h1 style='text-align:center; color:#1f77b4; margin-bottom:30px;'>
            🏥 Glaucoma Progression Interface
        </h1>
        <div style='text-align:center; margin-bottom:30px;'>
            <p>Please login to access the visual field labeling system</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
        <div style='position: fixed; bottom: 0; width: 100%; text-align: center; 
                    background: linear-gradient(90deg, #1f77b4, #1565c0); padding: 15px 0; z-index: 9999;'>
            <p style='color: white; margin: 0; font-weight: 500;'>
                🏥 Glaucoma and Data Science Laboratory | Bascom Palmer Eye Institute
            </p>
        </div>
    """, unsafe_allow_html=True)