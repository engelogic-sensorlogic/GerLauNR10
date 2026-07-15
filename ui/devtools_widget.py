"""
GerLauNR10 - Dev Tools: sincronização GitHub e Obsidian
"""
import os
import subprocess
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QLineEdit, QGroupBox, QFormLayout, QFileDialog,
    QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent


class GitThread(QThread):
    log = pyqtSignal(str)
    done = pyqtSignal(bool, str)

    def __init__(self, commands: list, cwd: str):
        super().__init__()
        self.commands = commands
        self.cwd = cwd

    def run(self):
        try:
            for cmd in self.commands:
                self.log.emit(f"$ {' '.join(cmd)}")
                result = subprocess.run(
                    cmd, cwd=self.cwd,
                    capture_output=True, text=True, encoding="utf-8"
                )
                if result.stdout:
                    self.log.emit(result.stdout.strip())
                if result.stderr:
                    self.log.emit(f"[stderr] {result.stderr.strip()}")
                if result.returncode != 0:
                    self.done.emit(False, f"Erro no comando: {' '.join(cmd)}")
                    return
            self.done.emit(True, "Operação concluída com sucesso!")
        except Exception as e:
            self.done.emit(False, str(e))


class DevToolsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QLabel(" Dev Tools – Sincronização e Manutenção")
        header.setObjectName("page_title")
        layout.addWidget(header)

        desc = QLabel(
            "Ferramentas para desenvolvedores: sincronização com GitHub e backup para Obsidian."
        )
        desc.setStyleSheet("color: #586069; font-size: 12px;")
        layout.addWidget(desc)

        # ---- GitHub ----
        grp_git = QGroupBox("🐙  GitHub – Sincronização do Projeto")
        git_layout = QVBoxLayout(grp_git)

        form_git = QFormLayout()
        self.e_repo_url = QLineEdit("https://github.com/engelogic-sensorlogic/GerLauNR10.git")
        self.e_branch = QLineEdit("main")
        self.e_commit_msg = QLineEdit()
        self.e_commit_msg.setPlaceholderText("Ex: feat: adiciona geração de PDF")
        form_git.addRow("URL do Repositório:", self.e_repo_url)
        form_git.addRow("Branch:", self.e_branch)
        form_git.addRow("Mensagem do commit:", self.e_commit_msg)
        git_layout.addLayout(form_git)

        git_btns = QHBoxLayout()
        btn_init = QPushButton("⚡ Inicializar Repositório")
        btn_init.setObjectName("btn_secondary")
        btn_init.clicked.connect(self._git_init)
        btn_commit = QPushButton("Commit")
        btn_commit.setObjectName("btn_primary")
        btn_commit.clicked.connect(self._git_commit)
        btn_push = QPushButton("🚀 Push para GitHub")
        btn_push.setObjectName("btn_accent")
        btn_push.clicked.connect(self._git_push)
        btn_pull = QPushButton("Pull do GitHub")
        btn_pull.setObjectName("btn_secondary")
        btn_pull.clicked.connect(self._git_pull)
        btn_status = QPushButton("📊 Git Status")
        btn_status.setObjectName("btn_secondary")
        btn_status.clicked.connect(self._git_status)
        for btn in [btn_init, btn_status, btn_commit, btn_push, btn_pull]:
            git_btns.addWidget(btn)
        git_layout.addLayout(git_btns)
        layout.addWidget(grp_git)

        # ---- Obsidian ----
        grp_obs = QGroupBox("📓  Obsidian – Backup de Dados")
        obs_layout = QVBoxLayout(grp_obs)

        form_obs = QFormLayout()
        self.e_obs_path = QLineEdit()
        self.e_obs_path.setPlaceholderText("Caminho do vault Obsidian...")

        obs_path_row = QHBoxLayout()
        obs_path_row.addWidget(self.e_obs_path)
        btn_browse_obs = QPushButton("📁 Selecionar")
        btn_browse_obs.setObjectName("btn_secondary")
        btn_browse_obs.setFixedWidth(100)
        btn_browse_obs.clicked.connect(self._browse_obs)
        obs_path_row.addWidget(btn_browse_obs)
        form_obs.addRow("Vault Obsidian:", obs_path_row)
        obs_layout.addLayout(form_obs)

        obs_btns = QHBoxLayout()
        btn_backup = QPushButton("Exportar Dados para Obsidian")
        btn_backup.setObjectName("btn_success")
        btn_backup.clicked.connect(self._export_obsidian)
        obs_btns.addWidget(btn_backup)
        obs_btns.addStretch()
        obs_layout.addLayout(obs_btns)
        layout.addWidget(grp_obs)

        # ---- Log ----
        log_lbl = QLabel("Log de operações:")
        log_lbl.setStyleSheet("color: #586069; font-size: 11px;")
        layout.addWidget(log_lbl)

        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setFont(QFont("Courier New", 10))
        self.log_edit.setStyleSheet(
            "background: #1a2332; color: #a0c0e0; border-radius: 6px; padding: 8px;"
        )
        layout.addWidget(self.log_edit)

        # Limpar log
        btn_clear = QPushButton("Limpar Log")
        btn_clear.setObjectName("btn_secondary")
        btn_clear.clicked.connect(self.log_edit.clear)
        layout.addWidget(btn_clear, alignment=Qt.AlignmentFlag.AlignRight)

    def _log(self, msg: str):
        self.log_edit.append(msg)
        self.log_edit.verticalScrollBar().setValue(self.log_edit.verticalScrollBar().maximum())

    def _run_git(self, commands: list):
        cwd = str(BASE_DIR)
        self._git_thread = GitThread(commands, cwd)
        self._git_thread.log.connect(self._log)
        self._git_thread.done.connect(lambda ok, msg: self._log(
            f"\n{'✅' if ok else '❌'}  {msg}\n{'─'*40}"
        ))
        self._git_thread.start()

    def _git_init(self):
        self._log("─" * 40)
        self._log("Inicializando repositório Git...")
        repo_url = self.e_repo_url.text().strip()
        commands = [
            ["git", "init"],
            ["git", "remote", "add", "origin", repo_url],
        ]
        # Cria .gitignore se não existir
        gi_path = BASE_DIR / ".gitignore"
        if not gi_path.exists():
            gi_path.write_text(
                "# GerLauNR10 .gitignore\n"
                "data/\n__pycache__/\n*.pyc\n*.pyo\n*.db\n"
                "dist/\nbuild/\n*.spec\n.env\nClientes/\n"
            )
            self._log("📄 .gitignore criado")
        self._run_git(commands)

    def _git_status(self):
        self._log("─" * 40)
        self._run_git([["git", "status"]])

    def _git_commit(self):
        msg = self.e_commit_msg.text().strip()
        if not msg:
            msg = "feat: atualização do projeto GerLauNR10"
        self._log("─" * 40)
        self._run_git([
            ["git", "add", "."],
            ["git", "commit", "-m", msg],
        ])

    def _git_push(self):
        branch = self.e_branch.text().strip() or "main"
        self._log("─" * 40)
        self._log(f"Enviando para GitHub (branch: {branch})...")
        self._run_git([
            ["git", "push", "-u", "origin", branch],
        ])

    def _git_pull(self):
        branch = self.e_branch.text().strip() or "main"
        self._log("─" * 40)
        self._log(f"Sincronizando do GitHub (branch: {branch})...")
        self._run_git([["git", "pull", "origin", branch]])

    def _browse_obs(self):
        path = QFileDialog.getExistingDirectory(self, "Selecionar Vault Obsidian")
        if path:
            self.e_obs_path.setText(path)

    def _export_obsidian(self):
        obs_path = self.e_obs_path.text().strip()
        if not obs_path:
            QMessageBox.warning(self, "Aviso", "Selecione o caminho do Vault Obsidian.")
            return
        obs_dir = Path(obs_path) / "GerLauNR10"
        obs_dir.mkdir(parents=True, exist_ok=True)

        import database as db
        clientes = db.listar_clientes()
        md_content = "# GerLauNR10 – Dados Exportados\n\n"
        md_content += f"Exportado em: {__import__('datetime').datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
        md_content += f"## Clientes ({len(clientes)})\n\n"

        for c in clientes:
            laudos = db.listar_laudos(c["id"])
            md_content += f"### {c['razao_social']}"
            if c.get("filial"):
                md_content += f" – {c['filial']}"
            md_content += f"\n- CNPJ: {c.get('cnpj', '—')}\n"
            md_content += f"- Laudos: {len(laudos)}\n\n"
            for l in laudos:
                paineis = db.listar_paineis(l["id"])
                media = sum(p.get("nivel_aderencia", 0) for p in paineis) / len(paineis) if paineis else 0
                md_content += f"  #### {l.get('titulo', '—')} (Nº {l.get('numero', '—')})\n"
                md_content += f"  - Status: {l.get('status', '—')}\n"
                md_content += f"  - Painéis: {len(paineis)} | Aderência média: {media*100:.1f}%\n\n"

        out_file = obs_dir / "resumo.md"
        out_file.write_text(md_content, encoding="utf-8")
        self._log(f"✅  Exportado para: {out_file}")
        QMessageBox.information(self, "Exportado", f"Dados exportados para:\n{out_file}")
