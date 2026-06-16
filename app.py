import streamlit as st

from gitlab_compliance_checker.ui.main import main

# --- Page Config ---
st.set_page_config(
    page_title="GitLab Compliance Checker",
    page_icon="🔍",
    layout="wide",
)

# --- Auth Gate ---
if not st.user.is_logged_in:
    st.title("GitLab Compliance Checker")
    st.markdown("Log in with your GitLab account to continue.")
    st.button("Login with GitLab", on_click=st.login)
    st.stop()

main()
