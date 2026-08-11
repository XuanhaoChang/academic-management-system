from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.constants import RoleType
from core.exceptions import BusinessError
from services.auth_service import AuthService


class LoginDialog(QDialog):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("登录")
        self.setModal(True)
        self.resize(520, 380)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        card = QFrame()
        card.setObjectName("loginCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(12)

        title = QLabel("教学管理系统")
        title.setObjectName("loginTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle = QLabel("请先登录")
        subtitle.setObjectName("loginSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_login_tab(), "登录")

        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addWidget(self.tabs)
        root.addStretch(1)
        root.addWidget(card)
        root.addStretch(1)

    def _build_login_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        form.setContentsMargins(12, 12, 12, 12)
        form.setSpacing(12)

        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("请输入用户名")
        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText("请输入密码")
        self.login_password.setEchoMode(QLineEdit.EchoMode.Password)

        form.addRow("用户名", self.login_username)
        form.addRow("密码", self.login_password)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_login = QPushButton("登录")
        btn_login.setObjectName("primaryButton")
        btn_login.clicked.connect(self._handle_login)
        btn_row.addWidget(btn_login)

        form.addRow(btn_row)
        return page

    def _handle_login(self) -> None:
        username = self.login_username.text().strip()
        password = self.login_password.text()
        if not username:
            QMessageBox.warning(self, "登录失败", "请输入用户名")
            return
        if not password:
            QMessageBox.warning(self, "登录失败", "请输入密码")
            return

        try:
            AuthService.login_with_password(username, password)
            self.accept()
        except BusinessError as exc:
            QMessageBox.warning(self, "登录失败", str(exc))
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "系统错误", f"登录发生未预期异常：{exc}")
