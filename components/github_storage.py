import json
import base64
import requests
import streamlit as st
from components.data_helpers import get_default_data, migrate_data


class ConflictError(Exception):
    pass


def _headers():
    return {
        "Authorization": f"Bearer {st.secrets['GITHUB_TOKEN']}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _file_url():
    repo = st.secrets["GITHUB_REPO"]
    return f"https://api.github.com/repos/{repo}/contents/data/user_data.json"


def load_data():
    resp = requests.get(_file_url(), headers=_headers(), timeout=15)
    if resp.status_code == 200:
        content = resp.json()
        raw = base64.b64decode(content["content"]).decode("utf-8")
        data = json.loads(raw)
        return migrate_data(data), content["sha"]
    elif resp.status_code == 404:
        data = get_default_data()
        sha = _create_file(data)
        return data, sha
    else:
        raise Exception(f"GitHub API error {resp.status_code}: {resp.text}")


def _create_file(data):
    encoded = base64.b64encode(json.dumps(data, indent=2).encode("utf-8")).decode("utf-8")
    body = {
        "message": "Initialise user data",
        "content": encoded,
    }
    resp = requests.put(_file_url(), headers=_headers(), json=body, timeout=15)
    if resp.status_code in (200, 201):
        return resp.json()["content"]["sha"]
    else:
        raise Exception(f"GitHub API error creating file {resp.status_code}: {resp.text}")


def save_data(data, sha):
    encoded = base64.b64encode(json.dumps(data, indent=2).encode("utf-8")).decode("utf-8")
    body = {
        "message": "Update user data",
        "content": encoded,
        "sha": sha,
    }
    resp = requests.put(_file_url(), headers=_headers(), json=body, timeout=15)
    if resp.status_code in (200, 201):
        return resp.json()["content"]["sha"]
    elif resp.status_code == 409:
        raise ConflictError("Data was modified externally. Please refresh and try again.")
    else:
        raise Exception(f"GitHub API error {resp.status_code}: {resp.text}")


def ensure_data_loaded():
    if "user_data" not in st.session_state:
        try:
            data, sha = load_data()
            st.session_state["user_data"] = data
            st.session_state["data_sha"] = sha
        except Exception as e:
            st.error(f"Failed to load data: {e}")
            st.session_state["user_data"] = get_default_data()
            st.session_state["data_sha"] = None


def save_and_sync():
    data = st.session_state.get("user_data")
    sha = st.session_state.get("data_sha")
    if data is None:
        return False
    try:
        new_sha = save_data(data, sha)
        st.session_state["data_sha"] = new_sha
        return True
    except ConflictError:
        st.warning("Data was modified elsewhere. Reloading...")
        data, sha = load_data()
        st.session_state["user_data"] = data
        st.session_state["data_sha"] = sha
        return False
    except Exception as e:
        st.error(f"Save failed: {e}")
        return False


def force_reload():
    try:
        data, sha = load_data()
        st.session_state["user_data"] = data
        st.session_state["data_sha"] = sha
        return True
    except Exception as e:
        st.error(f"Reload failed: {e}")
        return False
