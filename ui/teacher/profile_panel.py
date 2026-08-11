"""ProfilePanel — 教师个人信息面板

功能：
  - 展示当前登录教师的基本信息（教工号/姓名/院系/注册时间）
  - 修改密码（旧密码验证 + 新密码确认）
"""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.exceptions import AuthError, BusinessError, ValidationError
from core.session import Session
from services.auth_service import AuthService
from services.teacher_service import TeacherService


class ProfilePanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._svc = TeacherService()
        self._auth = AuthService()
        self._setup_ui()

    # ------------------------------------------------------------------
    # UI 构建
    # ------------------------------------------------------------------
    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(20)

        # 顶部标题
        title = QLabel("个人信息")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        root.addWidget(title)

        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        root.addWidget(line)

        # 基本信息区
        info_box = QGroupBox("基本信息")
        info_box.setStyleSheet("QGroupBox { font-size: 14px; font-weight: bold; }")
        info_layout = QFormLayout(info_box)
        info_layout.setSpacing(12)
        info_layout.setContentsMargins(16, 20, 16, 16)

        self._lbl_username  = QLabel("—")
        self._lbl_real_name = QLabel("—")
        self._lbl_dept      = QLabel("—")
        self._lbl_created   = QLabel("—")

        for lbl in (self._lbl_username, self._lbl_real_name,
                    self._lbl_dept, self._lbl_created):
            lbl.setStyleSheet("font-size: 13px; color: #34495e;")

        info_layout.addRow("教工号：", self._lbl_username)
        info_layout.addRow("姓　名：", self._lbl_real_name)
        info_layout.addRow("所属院系：", self._lbl_dept)
        info_layout.addRow("注册时间：", self._lbl_created)

        root.addWidget(info_box)

        # 修改密码区
        pwd_box = QGroupBox("修改密码")
        pwd_box.setStyleSheet("QGroupBox { font-size: 14px; font-weight: bold; }")
        pwd_layout = QFormLayout(pwd_box)
        pwd_layout.setSpacing(12)
        pwd_layout.setContentsMargins(16, 20, 16, 16)

        self._edit_old_pwd  = QLineEdit()
        self._edit_new_pwd  = QLineEdit()
        self._edit_cfm_pwd  = QLineEdit()
        for edit in (self._edit_old_pwd, self._edit_new_pwd, self._edit_cfm_pwd):
            edit.setEchoMode(QLineEdit.EchoMode.Password)
            edit.setFixedWidth(260)

        self._edit_old_pwd.setPlaceholderText("请输入旧密码")
        self._edit_new_pwd.setPlaceholderText("至少 6 位")
        self._edit_cfm_pwd.setPlaceholderText("再次输入新密码")

        pwd_layout.addRow("旧密码：", self._edit_old_pwd)
        pwd_layout.addRow("新密码：", self._edit_new_pwd)
        pwd_layout.addRow("确认新密码：", self._edit_cfm_pwd)

        btn_row = QHBoxLayout()
        self._btn_change_pwd = QPushButton("修改密码")
        self._btn_change_pwd.setFixedWidth(120)
        self._btn_change_pwd.setStyleSheet(
            "QPushButton { background-color: #2980b9; color: white; "
            "border-radius: 4px; padding: 6px 16px; } "
            "QPushButton:hover { background-color: #3498db; }"
        )
        self._btn_change_pwd.clicked.connect(self._on_change_password)
        btn_row.addWidget(self._btn_change_pwd)
        btn_row.addStretch()

        pwd_layout.addRow("", btn_row)
        root.addWidget(pwd_box)

        root.addStretch()

    # ------------------------------------------------------------------
    # 数据加载
    # ------------------------------------------------------------------
    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._load_profile()

    def _load_profile(self) -> None:
        if Session.current_user is None:
            return
        try:
            info = self._svc.get_profile(Session.current_user.id)
            self._lbl_username.setText(info.get("username", "—"))
            self._lbl_real_name.setText(info.get("real_name", "—"))
            self._lbl_dept.setText(info.get("dept_name", "—"))
            created = info.get("created_at")
            self._lbl_created.setText(str(created)[:19] if created else "—")
        except (BusinessError, ValidationError) as exc:
            QMessageBox.warning(self, "加载失败", str(exc))

    # ------------------------------------------------------------------
    # 修改密码
    # ------------------------------------------------------------------
    def _on_change_password(self) -> None:
        if Session.current_user is None:
            return

        old_pwd = self._edit_old_pwd.text()
        new_pwd = self._edit_new_pwd.text()
        cfm_pwd = self._edit_cfm_pwd.text()

        if not old_pwd:
            QMessageBox.warning(self, "输入错误", "请输入旧密码。")
            return
        if len(new_pwd) < 6:
            QMessageBox.warning(self, "输入错误", "新密码至少需要 6 位。")
            return
        if new_pwd != cfm_pwd:
            QMessageBox.warning(self, "输入错误", "两次输入的新密码不一致。")
            return

        try:
            AuthService.update_password(Session.current_user.id, old_pwd, new_pwd)
            QMessageBox.information(self, "修改成功", "密码已成功修改。")
            # 清空输入框
            self._edit_old_pwd.clear()
            self._edit_new_pwd.clear()
            self._edit_cfm_pwd.clear()
        except AuthError as exc:
            QMessageBox.warning(self, "修改失败", str(exc))
        except (BusinessError, ValidationError) as exc:
            QMessageBox.warning(self, "修改失败", str(exc))
