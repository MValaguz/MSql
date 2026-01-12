#  Creato da.....: Marco Valaguzza
#  Piattaforma...: Python 3.11
#  Data..........: 05/01/2026
#  Descrizione...: Gestore repository GitHub multi-token (OAuth Device Flow)
#  Note..........: Supporta account personale + più organizzazioni

import sys
import os
import time
import json
import webbrowser
import requests

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from github import Github, Auth
from git import Repo, InvalidGitRepositoryError

import utilita

# ============================================================
# Translation helper
# ============================================================
def tr(message: str) -> str:
    return QCoreApplication.translate("github_organizer", message)

# ============================================================
# Dialog lista file modificati
# ============================================================
class GitFileListDialog(QDialog):

    def __init__(self, files: list[str], parent=None):
        super().__init__(parent)

        self.setWindowTitle(tr("Modified files"))
        self.resize(450, 300)

        layout = QVBoxLayout(self)

        label = QLabel(tr("The following files will be included in the commit:"))
        layout.addWidget(label)

        self.list_widget = QListWidget()
        self.list_widget.addItems(files)
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_ok = QPushButton(tr("Confirm commit"))
        btn_cancel = QPushButton(tr("Cancel"))

        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)

        layout.addLayout(btn_layout)

        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

# ============================================================
# OAuth Device Flow Helper
# ============================================================
class GitHubOAuth:
    DEVICE_CODE_URL = "https://github.com/login/device/code"
    ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"

    def __init__(self, client_id: str, scope: str = "repo read:org"):
        self.client_id = client_id
        self.scope = scope
        self.device_code = None
        self.interval = 5
        self.access_token = None

    def start_device_flow(self):
        resp = requests.post(
            self.DEVICE_CODE_URL,
            data={"client_id": self.client_id, "scope": self.scope},
            headers={"Accept": "application/json"}
        )
        resp.raise_for_status()
        data = resp.json()

        self.device_code = data["device_code"]
        self.interval = data.get("interval", 5)

        return data["user_code"], data["verification_uri"]

    def poll_for_token(self):
        while True:
            time.sleep(self.interval)
            resp = requests.post(
                self.ACCESS_TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "device_code": self.device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
                },
                headers={"Accept": "application/json"}
            )
            resp.raise_for_status()
            data = resp.json()

            if "access_token" in data:
                self.access_token = data["access_token"]
                return self.access_token

            if data.get("error") == "slow_down":
                self.interval += 5
            elif data.get("error") not in ("authorization_pending", None):
                raise RuntimeError(data.get("error_description", "OAuth error"))

# ============================================================
# GitHub Organizer Widget
# ============================================================
class GitHubWidget(QWidget):

    def __init__(self, client_id: str, parent=None):
        super().__init__(parent)

        self.client_id = client_id
        self.settings = QSettings("Marco Valaguzza", "MSql")
        self.github_instances: list[Github] = []

        self.setWindowTitle(tr("GitHub Organizer"))
        self.resize(520, 480)

        icon = QIcon()
        icon.addPixmap(QPixmap("icons:MSql.gif"))
        self.setWindowIcon(icon)

        self._build_ui()
        self.login_all_tokens()
        self.load_repositories()

    # ============================================================
    # UI
    # ============================================================
    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText(tr("Search repository..."))
        layout.addWidget(self.txt_search)

        self.repo_list = QListWidget()
        layout.addWidget(self.repo_list)

        btn_layout = QHBoxLayout()

        self.btn_refresh = QPushButton(QIcon("icons:refresh.png"), tr("Refresh"))
        self.btn_download = QPushButton(QIcon("icons:download.png"), tr("Download"))
        self.btn_upload = QPushButton(QIcon("icons:upload.png"), tr("Upload"))
        self.btn_upload.setEnabled(False)

        btn_layout.addWidget(self.btn_refresh)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_download)
        btn_layout.addWidget(self.btn_upload)

        layout.addLayout(btn_layout)

        self.btn_refresh.clicked.connect(self.load_repositories)
        self.btn_download.clicked.connect(self.download_repository)
        self.btn_upload.clicked.connect(self.upload_repository)

        self.repo_list.itemSelectionChanged.connect(
            lambda: self.btn_upload.setEnabled(self.repo_list.currentItem() is not None)
        )

        self.txt_search.textChanged.connect(self.filter_repositories)

    # ============================================================
    # Token handling (JSON SAFE)
    # ============================================================
    def _load_tokens(self) -> dict:
        raw = self.settings.value("github_tokens", "{}")
        try:
            return json.loads(raw)
        except Exception:
            return {}

    def _save_tokens(self, tokens: dict):
        self.settings.setValue("github_tokens", json.dumps(tokens))
        self.settings.sync()

    # ============================================================
    # Login
    # ============================================================
    def login_all_tokens(self):
        tokens = self._load_tokens()

        for token in tokens.values():
            try:                
                gh = Github(auth=Auth.Token(token),user_agent="MSql-GitHub-Organizer")
                _ = gh.get_user().login
                self.github_instances.append(gh)
            except Exception:
                pass

        if not self.github_instances:
            self.login_new_token("personal")

    def login_new_token(self, key: str):
        oauth = GitHubOAuth(self.client_id)
        user_code, url = oauth.start_device_flow()

        QMessageBox.information(
            self,
            tr("GitHub Login"),
            tr(f"Open URL and enter code:\n\n{url}\n\nCode: {user_code}")
        )

        webbrowser.open(url)
        token = oauth.poll_for_token()

        tokens = self._load_tokens()
        tokens[key] = token
        self._save_tokens(tokens)

        self.github_instances.append(
            Github(auth=Auth.Token(token),user_agent="MSql-GitHub-Organizer")
        )

    # ============================================================
    # Load repositories
    # ============================================================
    def load_repositories(self):
        self.repo_list.clear()
        self._items = {}

        try:
            for gh in self.github_instances:
                user = gh.get_user()

                for repo in user.get_repos(affiliation="owner,collaborator,organization_member"):
                    self._add_repo(repo.full_name, repo.clone_url)

                for org in user.get_orgs():
                    try:
                        for repo in org.get_repos():
                            self._add_repo(repo.full_name, repo.clone_url)
                    except Exception:
                        pass

            for name in sorted(self._items):
                self.repo_list.addItem(self._items[name])

            self.filter_repositories(self.txt_search.text())

        except Exception as e:
            QMessageBox.critical(self, tr("GitHub error"), str(e))

    def _add_repo(self, name, url):
        if name not in self._items:
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, url)
            self._items[name] = item

    # ============================================================
    # Search
    # ============================================================
    def filter_repositories(self, text: str):
        text = text.lower()
        for i in range(self.repo_list.count()):
            item = self.repo_list.item(i)
            item.setHidden(text not in item.text().lower())

    # ============================================================
    # Download
    # ============================================================
    def download_repository(self):
        item = self.repo_list.currentItem()
        if not item:
            return

        repo_url = item.data(Qt.ItemDataRole.UserRole)
        repo_name = repo_url.split("/")[-1].replace(".git", "")

        folder = QFileDialog.getExistingDirectory(self, tr("Select folder"))
        if not folder:
            return

        path = os.path.join(folder, repo_name)

        try:
            if not os.path.exists(path):
                Repo.clone_from(repo_url, path)
            else:
                Repo(path).remote().pull()

            self.settings.setValue(f"repo_path/{repo_url}", path)

        except Exception as e:
            QMessageBox.critical(self, tr("Git error"), str(e))

    # ============================================================
    # Upload
    # ============================================================
    def upload_repository(self):
        item = self.repo_list.currentItem()
        if not item:
            return

        repo_url = item.data(Qt.ItemDataRole.UserRole)
        default = self.settings.value(f"repo_path/{repo_url}", "")

        folder = QFileDialog.getExistingDirectory(self, tr("Select repository"), default)
        if not folder:
            return

        try:
            repo = Repo(folder)
        except InvalidGitRepositoryError:
            QMessageBox.critical(self, tr("Error"), tr("Not a Git repository"))
            return

        changed = self._get_changed_files(repo)
        if not changed:
            QMessageBox.information(self, tr("Info"), tr("No changes"))
            return

        if GitFileListDialog(changed, self).exec() != QDialog.DialogCode.Accepted:
            return

        msg, ok = QInputDialog.getText(self, tr("Commit"), tr("Commit message:"))
        if not ok or not msg.strip():
            return

        try:
            repo.git.add(all=True)
            repo.index.commit(msg)
            repo.remote("origin").push()
        except Exception as e:
            QMessageBox.critical(self, tr("Git error"), str(e))

    # ============================================================
    # Utils
    # ============================================================
    @staticmethod
    def _get_changed_files(repo: Repo) -> list[str]:
        files = {d.a_path for d in repo.index.diff(None)}
        files.update(repo.untracked_files)
        return sorted(files)

# ============================================================
# TEST
# ============================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    # va passato id del client GitHub OAuth che però è nelle preferenza di MSql!!!!
    w = GitHubWidget("")
    w.show()
    sys.exit(app.exec())