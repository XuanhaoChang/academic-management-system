from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QLabel,
    QListWidget,
    QMessageBox,
    QMainWindow,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QSizePolicy,
)

from core.constants import ActionType
from core.constants import RoleType
from core.logger import AuditLogger
from core.session import Session
from ui.admin.user_mgmt import UserMgmtWidget
from ui.admin.dept_mgmt import DeptMgmtWidget
from ui.admin.major_mgmt import MajorMgmtWidget
from ui.admin.course_mgmt import CourseMgmtWidget
from ui.admin.teaching_mgmt import TeachingMgmtWidget
from ui.admin.schedule_change_mgmt import ScheduleChangeMgmtWidget
from ui.admin.exam_defer_mgmt import ExamDeferMgmtWidget
from ui.teacher.course_panel import CoursePanel


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("教学管理系统")
        self.resize(1080, 720)

        self.nav = QListWidget()
        self.nav.addItem("Dashboard")
        self.nav.addItem("User Management")
        self.nav.addItem("Settings")
        self.pages = QStackedWidget()
        self.title_label = QLabel("教务管理系统")
        self.subtitle_label = QLabel("统一教学管理平台")
        self.logout_requested = False
        self._build_layout()

    def _build_layout(self) -> None:
        wrapper = QWidget()
        wrapper.setObjectName("mainWrapper")
        self.setCentralWidget(wrapper)

        self.title_label.setObjectName("pageTitle")
        self.subtitle_label.setObjectName("pageSubtitle")
        self.nav.setObjectName("sideNav")
        self.pages.setObjectName("pageStack")
        self.nav.setSpacing(8)

        title_font = QFont("WenQuanYi Micro Hei", 18, QFont.Weight.Bold)
        self.title_label.setFont(title_font)
        self.subtitle_label.setFont(QFont("WenQuanYi Micro Hei", 10))

        self.splitter = QSplitter()
        self.splitter.addWidget(self.nav)
        self.splitter.addWidget(self.pages)
        self.splitter.setSizes([220, 860])
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 3)
        self.splitter.setHandleWidth(10)
        self.splitter.setChildrenCollapsible(False)

        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0) # 移除外边距，改用内层布局控制
        layout.setSpacing(0)

        # 顶部导航栏
        header = QWidget()
        header.setObjectName("appHeader")
        header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 12, 24, 12)
        
        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(2)
        title_vbox.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.title_label.setObjectName("pageTitle")
        self.subtitle_label.setObjectName("pageSubtitle")
        title_vbox.addWidget(self.title_label)
        title_vbox.addWidget(self.subtitle_label)
        
        header_layout.addLayout(title_vbox)
        header_layout.addStretch()
        
        # 用户状态/退出占位
        self.user_info = QLabel("未登录")
        self.user_info.setObjectName("headerUser")
        header_layout.addWidget(self.user_info)

        self.btn_logout = QPushButton("注销")
        self.btn_logout.setObjectName("dangerButton")
        self.btn_logout.clicked.connect(self._logout)
        header_layout.addWidget(self.btn_logout)

        # 主体内容布局
        content_area = QWidget()
        content_layout = QHBoxLayout(content_area)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(12)
        content_layout.addWidget(self.splitter)

        layout.addWidget(header)
        layout.addWidget(content_area)

        self.nav.currentRowChanged.connect(self.switch_page)

    def init_navigation(self, role: int) -> None:
        if Session.current_user is not None:
            self.user_info.setText(f"{Session.current_user.real_name} ({Session.current_user.username})")

        self.nav.clear()
        while self.pages.count() > 0:
            page = self.pages.widget(0)
            if page is None:
                break
            self.pages.removeWidget(page)
            page.deleteLater()

        # 默认显示左侧导航；学生端单独隐藏
        self.nav.setVisible(True)
        self.splitter.setHandleWidth(10)
        self.splitter.setSizes([220, 860])

        if role == RoleType.ADMIN:
            self.nav.addItem("用户管理")
            self.pages.addWidget(UserMgmtWidget())
            self.nav.addItem("院系管理")
            self.pages.addWidget(DeptMgmtWidget())
            self.nav.addItem("专业管理")
            self.pages.addWidget(MajorMgmtWidget())
            self.nav.addItem("课程管理")
            self.pages.addWidget(CourseMgmtWidget())
            self.nav.addItem("授课安排")
            self.pages.addWidget(TeachingMgmtWidget())
            self.nav.addItem("调课审批")
            self.pages.addWidget(ScheduleChangeMgmtWidget())
            self.nav.addItem("缓考审批")
            self.pages.addWidget(ExamDeferMgmtWidget())
        elif role == RoleType.TEACHER:
            from ui.teacher.profile_panel  import ProfilePanel
            from ui.teacher.schedule_panel import SchedulePanel

            self.nav.addItem("个人信息")
            self.pages.addWidget(ProfilePanel())

            self.nav.addItem("我的课表")
            self.pages.addWidget(SchedulePanel())

            self.nav.addItem("教学工作台")
            self.pages.addWidget(CoursePanel())
        elif role == RoleType.STUDENT:
            self.nav.setVisible(False)
            self.splitter.setHandleWidth(0)
            self.splitter.setSizes([0, 1])
            try:
                from views.student.enrollment import EnrollmentWidget
                self.pages.addWidget(EnrollmentWidget())
            except Exception as exc:  # noqa: BLE001
                self.pages.addWidget(self._build_placeholder(f"学生中心加载失败：{exc}"))

        if self.pages.count() > 0:
            self.nav.setCurrentRow(0)

    def switch_page(self, page_idx: int) -> None:
        if 0 <= page_idx < self.pages.count():
            self.pages.setCurrentIndex(page_idx)

    def _build_placeholder(self, text: str) -> QWidget:
        holder = QWidget()
        holder_layout = QVBoxLayout(holder)
        holder_layout.setContentsMargins(24, 24, 24, 24)

        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setObjectName("emptyHint")
        holder_layout.addWidget(label)
        return holder

    def _logout(self) -> None:
        reply = QMessageBox.question(self, "注销确认", "确定要注销当前账号吗？")
        if reply != QMessageBox.StandardButton.Yes:
            return

        if Session.current_user is not None:
            AuditLogger.log_action(Session.current_user.id, ActionType.LOGOUT, "User logged out")

        Session.clear()
        self.logout_requested = True
        self.close()
