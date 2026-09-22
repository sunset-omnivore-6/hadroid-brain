"""Reads and writes the task file.

Normally the file lives on GitHub and the app talks to GitHub directly (GitHubStore).
For trying the app on your own computer without GitHub, set the environment variable
TASKS_LOCAL_FILE to a file path and the app reads and writes that file instead (LocalStore).

Both stores work the same way:
  text, version = store.read()
  new_version = store.write(new_text, version, "message")
The version is GitHub's stamp for the file. Writing with an old stamp raises ConflictError,
which means someone (usually Claude) saved first: read again and try once more.
"""
import base64
import hashlib

import requests

API = "https://api.github.com"


class StoreError(Exception):
    """Something the app should explain to the reader in plain words."""


class AuthError(StoreError):
    """GitHub refused the key (expired, wrong, or not allowed to see the repo)."""


class NotFoundError(StoreError):
    """The repo, branch or file name is wrong, or the file does not exist yet."""


class ConflictError(StoreError):
    """The file changed between reading and writing. Read again and retry."""


class ProtectedError(StoreError):
    """A rule on the branch blocked the save (branch protection). Remove the rule."""


class GitHubStore:
    def __init__(self, token, repo, branch="main", path="data/tasks.json"):
        self.token = token
        self.repo = repo
        self.branch = branch
        self.path = path

    def _url(self):
        return f"{API}/repos/{self.repo}/contents/{self.path}"

    def _headers(self, accept="application/vnd.github+json"):
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": accept,
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def read(self):
        try:
            resp = requests.get(self._url(), headers=self._headers(), params={"ref": self.branch}, timeout=20)
        except requests.RequestException as e:
            raise StoreError(f"GitHub did not answer ({e.__class__.__name__}).")
        self._raise_for(resp)
        body = resp.json()
        version = body["sha"]
        if body.get("content"):
            text = base64.b64decode(body["content"]).decode("utf-8")
        else:
            # Files over 1 MB come back without content; ask for the plain text instead.
            raw = requests.get(self._url(), headers=self._headers("application/vnd.github.raw+json"),
                               params={"ref": self.branch}, timeout=30)
            self._raise_for(raw)
            text = raw.text
        return text, version

    def write(self, text, version, message):
        payload = {
            "message": message,
            "content": base64.b64encode(text.encode("utf-8")).decode("ascii"),
            "sha": version,
            "branch": self.branch,
        }
        try:
            resp = requests.put(self._url(), headers=self._headers(), json=payload, timeout=30)
        except requests.RequestException as e:
            raise StoreError(f"GitHub did not answer ({e.__class__.__name__}).")
        if resp.status_code in (200, 201):
            return resp.json()["content"]["sha"]
        if resp.status_code == 409:
            if "rule" in resp.text.lower():
                raise ProtectedError("A protection rule on the main branch blocked the save.")
            raise ConflictError("The file changed before the save.")
        self._raise_for(resp)
        raise StoreError(f"GitHub answered with code {resp.status_code}.")

    @staticmethod
    def _raise_for(resp):
        if resp.status_code in (401, 403):
            raise AuthError("GitHub refused the key.")
        if resp.status_code == 404:
            raise NotFoundError("GitHub could not find the repo, branch or file.")
        if resp.status_code >= 400:
            raise StoreError(f"GitHub answered with code {resp.status_code}.")


class LocalStore:
    """Same behaviour, but on a file on this computer. Used for testing only."""

    def __init__(self, path):
        self.path = path

    @staticmethod
    def _stamp(text):
        return hashlib.sha1(text.encode("utf-8")).hexdigest()

    def read(self):
        try:
            with open(self.path, encoding="utf-8") as f:
                text = f.read()
        except FileNotFoundError:
            raise NotFoundError(f"There is no file at {self.path}.")
        return text, self._stamp(text)

    def write(self, text, version, message):
        current_text, current_version = self.read()
        if current_version != version:
            raise ConflictError("The file changed before the save.")
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(text)
        return self._stamp(text)
