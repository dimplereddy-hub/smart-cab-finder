import os

import streamlit as st
from dotenv import load_dotenv

from gitlab_compliance_checker.infrastructure.gitlab.client import GitLabClient
from gitlab_compliance_checker.ui.compliance import render_compliance_mode


def cleanup_gitlab_client(client: GitLabClient):
    """Callback to shut down the client's background thread when the resource is evicted."""
    import logging

    logger = logging.getLogger(__name__)
    logger.info("Cleaning up GitLabClient resource (st.cache_resource eviction)")
    client.close()


@st.cache_resource(on_release=cleanup_gitlab_client)
def get_gitlab_client(url: str, token: str, ssl_verify: bool):
    """
    Cached GitLab client initialization.
    Ensures only one instance (and one background thread) exists for a set of credentials.
    Streamlit handles persistence across reruns automatically.
    """
    import logging

    logger = logging.getLogger(__name__)
    logger.info(f"Creating NEW GitLabClient resource for {url}")
    return GitLabClient(url, token, ssl_verify=ssl_verify)


def main():
    load_dotenv()

    st.title("GitLab Compliance Checker")

    with st.sidebar:
        st.markdown(f"👤 **{st.user.name}**")
        st.caption(st.user.email or "")
        st.button("Logout", on_click=st.logout, use_container_width=True)
        st.divider()

    gitlab_url = os.getenv("GITLAB_URL", "https://code.swecha.org").strip()
    gitlab_token = os.getenv("GITLAB_TOKEN", "").strip()
    ssl_verify = os.getenv("GITLAB_SSL_VERIFY", "True").lower() not in ("false", "0", "f")

    if not gitlab_token:
        st.warning("GITLAB_TOKEN is not set. Please configure it in the .env file.")
        st.stop()

    # Initialize Client (Persistent using st.cache_resource)
    try:
        client = get_gitlab_client(gitlab_url, gitlab_token, ssl_verify)
    except Exception as e:
        st.error(f"Critical Error initializing GitLab client: {e}")
        st.stop()

    render_compliance_mode(client)
