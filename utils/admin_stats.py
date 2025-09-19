"""
Admin Statistics Module - Página para visualizar progresso de todos os usuários
"""

import streamlit as st
import pandas as pd
import os
from .patient_tracker import PatientTracker

def show_admin_stats():
    """Mostra estatísticas detalhadas para administradores"""
    
    st.markdown("# 📊 Admin Dashboard - Progress Statistics")
    st.markdown("---")
    
    # Load data using DataLoader (same as labeling.py)
    from .dataloader import DataLoader
    dl = DataLoader()
    
    # Try to load CSV from Google Drive first
    df = None
    data_source = None
    
    with st.spinner("Loading database from cloud..."):
        df = dl.get_csv_from_drive("opv_24-2_prepared.csv")
        if df is not None:
            data_source = "cloud"
            st.success("Database loaded from Google Drive")
    
    # Fallback to local if cloud fails
    if df is None:
        try:
            from .config import CSV_PATH
            if os.path.exists(CSV_PATH):
                df = pd.read_csv(CSV_PATH)
                data_source = "local"
                st.info("Using local database")
            else:
                st.error("Database not found in cloud or locally")
                st.error("Please ensure CSV file is uploaded to Google Drive")
                return
        except Exception as e:
            st.error(f"Error loading database: {e}")
            return
    
    all_patients = df["maskedid"].unique().tolist()
    total_patients = len(all_patients)
    
    tracker = PatientTracker()
    
    # Overall statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Patients", total_patients)
    
    with col2:
        all_users_stats = tracker.get_all_users_stats(total_patients)
        st.metric("Active Users", len(all_users_stats))
    
    with col3:
        if all_users_stats:
            avg_completion = sum(stat['completion_percentage'] for stat in all_users_stats) / len(all_users_stats)
            st.metric("Avg Completion", f"{avg_completion:.1f}%")
        else:
            st.metric("Avg Completion", "0.0%")
    
    st.markdown("---")
    
    # Show data source
    st.caption(f"Data source: {data_source}")
    
    # User progress table
    if all_users_stats:
        st.markdown("## 👥 User Progress Details")
        
        # Create DataFrame for better display
        stats_df = pd.DataFrame(all_users_stats)
        
        # Format the DataFrame
        display_df = stats_df.copy()
        display_df['completion_percentage'] = display_df['completion_percentage'].round(1)
        display_df = display_df.rename(columns={
            'username': 'Username',
            'completed_count': 'Completed',
            'remaining_count': 'Remaining',
            'total_patients': 'Total',
            'completion_percentage': 'Progress (%)',
            'last_patient': 'Last Patient'
        })
        
        # Display with color coding
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Progress visualization
        st.markdown("## 📈 Progress Visualization")
        
        # Bar chart of completion percentages
        chart_df = stats_df[['username', 'completion_percentage']].set_index('username')
        st.bar_chart(chart_df)
        
        # Individual user details
        st.markdown("## 🔍 Individual User Details")
        
        selected_user = st.selectbox(
            "Select user to view details:",
            options=[''] + [stat['username'] for stat in all_users_stats],
            index=0
        )
        
        if selected_user:
            user_stat = next((s for s in all_users_stats if s['username'] == selected_user), None)
            if user_stat:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Completed", user_stat['completed_count'])
                with col2:
                    st.metric("Remaining", user_stat['remaining_count'])
                with col3:
                    st.metric("Progress", f"{user_stat['completion_percentage']:.1f}%")
                with col4:
                    if user_stat['last_patient']:
                        st.metric("Last Patient", user_stat['last_patient'])
                
                # Show completed patients list
                completed = tracker.get_completed_patients(selected_user)
                if completed:
                    st.markdown("### ✅ Completed Patients")
                    completed_list = sorted(list(completed))
                    
                    # Show in columns for better display
                    cols = st.columns(5)
                    for i, patient in enumerate(completed_list):
                        col_idx = i % 5
                        cols[col_idx].write(f"• {patient}")
    
    else:
        st.info("No user progress data available yet.")
    
    st.markdown("---")
    
    # Admin actions
    st.markdown("## ⚙️ Admin Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔄 Reset User Progress")
        if all_users_stats:
            user_to_reset = st.selectbox(
                "Select user to reset:",
                options=[''] + [stat['username'] for stat in all_users_stats],
                key="reset_user_select"
            )
            
            if user_to_reset:
                if st.button(f"Reset {user_to_reset}'s Progress", type="secondary"):
                    if st.checkbox("I confirm this action", key="confirm_reset"):
                        if tracker.reset_user_progress(user_to_reset):
                            st.success(f"✅ Reset progress for {user_to_reset}")
                            st.rerun()
                        else:
                            st.error("Failed to reset progress")
        else:
            st.info("No users with progress to reset")
    
    with col2:
        st.markdown("### 📥 Export Progress Report")
        if st.button("Download Progress Report", type="secondary"):
            report = tracker.export_progress_report()
            
            # Convert to JSON string for download
            import json
            report_json = json.dumps(report, indent=2)
            
            st.download_button(
                label="📋 Download JSON Report",
                data=report_json,
                file_name=f"progress_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )


def add_admin_menu():
    """Adiciona menu admin na sidebar se o usuário for admin"""
    
    # Verifica se usuário é admin (baseado no config.yaml)
    username = st.session_state.get('username')
    if not username:
        return
    
    # Carrega config para verificar role
    import yaml
    from yaml.loader import SafeLoader
    
    try:
        with open('config.yaml') as file:
            config = yaml.load(file, Loader=SafeLoader)
        
        user_roles = config.get('credentials', {}).get('usernames', {}).get(username, {}).get('roles', [])
        
        if 'admin' in user_roles:
            st.sidebar.markdown("---")
            st.sidebar.markdown("### 👑 Admin Panel")
            
            if st.sidebar.button("📊 View Statistics"):
                st.session_state['show_admin_stats'] = True
                st.rerun()
    
    except Exception as e:
        pass  # Silently ignore if can't load config