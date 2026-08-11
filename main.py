import sys
import os
from views.login_dialog import LoginDialog
from views.main_window import MainWindow
from PyQt6.QtWidgets import QApplication, QStyleFactory
from core.session import Session
from pathlib import Path


os.environ["QT_OPENGL"] = "software"
os.environ["QT_QUICK_BACKEND"] = "software"


def main() -> int:
    app = QApplication(sys.argv)

    # 统一基础风格，避免不同平台控件观感差异过大
    fusion = QStyleFactory.create("Fusion")
    if fusion is not None:
        app.setStyle(fusion)

    qss_path = Path(__file__).resolve().parent / "ui" / "assets" / "theme.qss"
    try:
        with qss_path.open("r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except OSError:
        pass
    
    while True:
        login = LoginDialog()
        
        if login.exec() != LoginDialog.DialogCode.Accepted:
            return 0

        current_user = Session.current_user
        if current_user is None:
            return 0

        window = MainWindow()
        window.init_navigation(current_user.role_id)
        window.show()
        app.exec()

        if not window.logout_requested:
            return 0


if __name__ == "__main__":
    raise SystemExit(main())