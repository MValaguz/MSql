#  Creato da.....: Marco Valaguzza
#  Piattaforma...: Python 3.11
#  Data..........: 05/01/2026
#  Descrizione...: Gestore repository GitHub - download/upload
#  Note..........: Creato utilizzando ChatGPT

import sys
import os

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from github import Github
from git import Repo, InvalidGitRepositoryError

# serve per attivare la corretta ricera delle icone
import utilita

def tr(message: str) -> str:
    """Qt translation helper"""
    return QCoreApplication.translate("github_organizer", message)


# ============================================================
# Dialog modified files list
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

        self.btn_ok = QPushButton(tr("Confirm commit"))
        self.btn_cancel = QPushButton(tr("Cancel"))

        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)

        layout.addLayout(btn_layout)

        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)


# ============================================================
# GitHub Organizer Widget
# ============================================================
class GitHubWidget(QWidget):

    def __init__(self, github_token: str, parent=None):
        super().__init__(parent)

        if not github_token or not github_token.strip():
            raise ValueError(tr("Invalid GitHub token"))

        self.github = Github(github_token)
        self.settings = QSettings("Marco Valaguzza", "Msql_github_organizer")

        self.setWindowTitle(tr("GitHub Organizer"))
        self.resize(420, 420)

        icon = QIcon()
        icon.addPixmap(QPixmap("icons:MSql.gif"), QIcon.Mode.Normal, QIcon.State.Off)
        self.setWindowIcon(icon)

        self._build_ui()
        self.load_repositories()

    # ============================================================
    # UI
    # ============================================================
    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.lbl_info = QLabel(tr("GitHub repositories:"))
        layout.addWidget(self.lbl_info)

        self.repo_list = QListWidget()
        layout.addWidget(self.repo_list)

        btn_layout = QHBoxLayout()

        self.btn_refresh = QPushButton(QIcon("icons:refresh.png"), tr("Refresh list"))
        self.btn_download = QPushButton(QIcon("icons:download.png"), tr("Download"))
        self.btn_upload = QPushButton(QIcon("icons:upload.png"), tr("Upload"))

        self.btn_upload.setEnabled(False)

        btn_layout.addWidget(self.btn_refresh)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_download)
        btn_layout.addWidget(self.btn_upload)

        layout.addLayout(btn_layout)

        # signals
        self.btn_refresh.clicked.connect(self.load_repositories)
        self.btn_download.clicked.connect(self.download_repository)
        self.btn_upload.clicked.connect(self.upload_repository)

        self.repo_list.itemSelectionChanged.connect(
            lambda: self.btn_upload.setEnabled(self.repo_list.currentItem() is not None)
        )

    # ============================================================
    # GitHub
    # ============================================================
    def load_repositories(self):
        self.repo_list.clear()
        try:
            user = self.github.get_user()
            for repo in user.get_repos():
                item = QListWidgetItem(repo.full_name)
                item.setData(Qt.ItemDataRole.UserRole, repo.clone_url)
                self.repo_list.addItem(item)
        except Exception as e:
            QMessageBox.critical(self, tr("GitHub error"), str(e))

    # ============================================================
    # DOWNLOAD
    # ============================================================
    def download_repository(self):
        item = self.repo_list.currentItem()
        if not item:
            QMessageBox.warning(self, tr("Warning"), tr("Select a repository"))
            return

        repo_url = item.data(Qt.ItemDataRole.UserRole)
        repo_name = repo_url.split("/")[-1].replace(".git", "")

        last_dir = self.settings.value("last_download_dir", "")
        folder = QFileDialog.getExistingDirectory(
            self, tr("Select destination folder"), last_dir
        )
        if not folder:
            return

        self.settings.setValue("last_download_dir", folder)
        local_path = os.path.join(folder, repo_name)

        try:
            if not os.path.exists(local_path):
                Repo.clone_from(repo_url, local_path)
                QMessageBox.information(self, tr("OK"), tr("Repository cloned"))
            else:
                repo = Repo(local_path)
                repo.remote(name="origin").pull()
                QMessageBox.information(self, tr("OK"), tr("Repository updated (pull)"))

            self.settings.setValue(f"repo_path/{repo_url}", local_path)

        except Exception as e:
            QMessageBox.critical(self, tr("Git error"), str(e))

    # ============================================================
    # UPLOAD (safe + file list)
    # ============================================================
    def upload_repository(self):
        item = self.repo_list.currentItem()
        if not item:
            return

        expected_repo_url = item.data(Qt.ItemDataRole.UserRole)
        default_path = self.settings.value(f"repo_path/{expected_repo_url}", "")

        folder = QFileDialog.getExistingDirectory(
            self, tr("Select local repository"), default_path
        )
        if not folder:
            return

        try:
            repo = Repo(folder)
        except InvalidGitRepositoryError:
            QMessageBox.critical(self, tr("Error"), tr("The selected folder is not a Git repository"))
            return

        if "origin" not in [r.name for r in repo.remotes]:
            QMessageBox.critical(self, tr("Error"), tr("Remote 'origin' not found"))
            return

        if not self._same_repository(repo.remote("origin").url, expected_repo_url):
            QMessageBox.critical(
                self,
                tr("Upload blocked"),
                tr("The local repository does NOT match the selected one.")
            )
            return

        changed_files = self._get_changed_files(repo)
        if not changed_files:
            QMessageBox.information(self, tr("Info"), tr("No changes to upload"))
            return

        dlg = GitFileListDialog(changed_files, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        msg, ok = QInputDialog.getText(
            self, tr("Commit message"), tr("Commit message:")
        )
        if not ok or not msg.strip():
            return

        try:
            repo.git.add(all=True)
            repo.index.commit(msg)
            repo.remote("origin").push()
            QMessageBox.information(self, tr("OK"), tr("Upload completed"))
        except Exception as e:
            QMessageBox.critical(self, tr("Git error"), str(e))

    # ============================================================
    # Utils
    # ============================================================
    @staticmethod
    def _same_repository(local_url: str, expected_url: str) -> bool:
        def normalize(url: str) -> str:
            return (
                url.replace(".git", "")
                   .replace("git@", "")
                   .replace("https://", "")
                   .replace("github.com:", "github.com/")
                   .lower()
            )
        return normalize(local_url) == normalize(expected_url)

    @staticmethod
    def _get_changed_files(repo: Repo) -> list[str]:
        files = set()

        for diff in repo.index.diff(None):
            files.add(diff.a_path)

        for file in repo.untracked_files:
            files.add(file)

        return sorted(files)


# ============================================================
# TEST STANDALONE
# ============================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)

    #w = GitHubWidget("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")
    w = GitHubWidget("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")
    w.show()

    sys.exit(app.exec())
