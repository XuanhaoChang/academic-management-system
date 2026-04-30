from __future__ import annotations

from typing import Any

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtWidgets import (
    QGraphicsOpacityEffect,
    QFormLayout,
    QHeaderView,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QFileDialog,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.exceptions import AuthError, BusinessError, ValidationError
from core.session import Session
from services.auth_service import AuthService
from services.selection_service import SelectionService
from services.student_selection_patch import apply_selection_patch
from services.student_service import StudentService
from services.validator import CourseValidator


class EnrollmentWidget(QWidget):
    _PERIOD_CLOCK: dict[int, tuple[str, str]] = {
        1: ("08:00", "08:45"),
        2: ("08:55", "09:40"),
        3: ("10:00", "10:45"),
        4: ("10:55", "11:40"),
        5: ("14:00", "14:45"),
        6: ("14:55", "15:40"),
        7: ("16:00", "16:45"),
        8: ("16:55", "17:40"),
        9: ("19:00", "19:45"),
        10: ("19:55", "20:40"),
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        apply_selection_patch()

        self._student_id = Session.current_user.id if Session.current_user else 0
        self._svc = StudentService()
        self._selection = SelectionService()
        self._validator = CourseValidator()
        self._semester = ""

        self._available: list[dict[str, Any]] = []
        self._selected: list[dict[str, Any]] = []
        self._waiting: list[dict[str, Any]] = []
        self._profile: dict[str, Any] = {}
        self._grades_current_raw: list[dict[str, Any]] = []
        self._exam_rows_raw: list[dict[str, Any]] = []
        self._eval_map: dict[int, dict[str, Any]] = {}
        self._page_opacity_effect: QGraphicsOpacityEffect | None = None
        self._page_fade_anim: QPropertyAnimation | None = None

        self._build_ui()
        self._apply_student_theme()
        self.refresh_all()

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        # 左侧：内容区（顶部信息 + 页面堆叠）
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        self.lbl_profile = QLabel("加载中...")
        self.lbl_profile.setObjectName("helperText")
        self.lbl_profile.setVisible(False)

        row = QHBoxLayout()
        self.lbl_semester = QLabel("学期：-")
        self.lbl_semester.setObjectName("helperText")
        row.addWidget(self.lbl_semester)
        row.addStretch(1)
        self.btn_refresh = QPushButton("刷新")
        self.btn_refresh.setObjectName("secondaryButton")
        self.btn_refresh.clicked.connect(self._on_refresh_clicked)
        row.addWidget(self.btn_refresh)
        left_layout.addLayout(row)

        self.pages = QStackedWidget()
        self.pages.setObjectName("pageStack")
        self.pages.addWidget(self._build_profile_tab())
        self.pages.addWidget(self._build_select_tab())
        self.pages.addWidget(self._build_timetable_tab())
        self.pages.addWidget(self._build_grade_tab())
        self.pages.addWidget(self._build_exam_tab())
        self.pages.addWidget(self._build_eval_tab())
        self._page_opacity_effect = QGraphicsOpacityEffect(self.pages)
        self._page_opacity_effect.setOpacity(1.0)
        self.pages.setGraphicsEffect(self._page_opacity_effect)
        self._page_fade_anim = QPropertyAnimation(self._page_opacity_effect, b"opacity", self)
        self._page_fade_anim.setDuration(170)
        self._page_fade_anim.setStartValue(0.82)
        self._page_fade_anim.setEndValue(1.0)
        self._page_fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        left_layout.addWidget(self.pages, 1)

        # 右侧：竖直导航栏
        self.nav = QListWidget()
        self.nav.setObjectName("sideNav")
        self.nav.setSpacing(8)
        self.nav.addItem("个人信息")
        self.nav.addItem("选课系统")
        self.nav.addItem("课表查询")
        self.nav.addItem("成绩查询")
        self.nav.addItem("考试查询")
        self.nav.addItem("课程评教")
        self.nav.setFixedWidth(160)
        self.nav.currentRowChanged.connect(self._on_nav_changed)
        self.nav.setCurrentRow(0)

        root.addWidget(left, 1)
        root.addWidget(self.nav)

    def _apply_student_theme(self) -> None:
        """Local theme polish for student pages without changing global qss."""
        self.setStyleSheet(
            """
            QWidget#pageStack {
                background: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
            }
            QListWidget#sideNav {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                padding: 8px;
                outline: none;
            }
            QListWidget#sideNav::item {
                border-radius: 8px;
                padding: 10px 12px;
                margin: 2px 0px;
                color: #1F2937;
            }
            QListWidget#sideNav::item:hover {
                background: #EFF6FF;
            }
            QListWidget#sideNav::item:selected {
                background: #DBEAFE;
                color: #1D4ED8;
                font-weight: 600;
            }
            QGroupBox {
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                margin-top: 12px;
                padding-top: 10px;
                background: #FFFFFF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #0F172A;
                font-weight: 600;
            }
            QLineEdit, QTextEdit, QSpinBox {
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                padding: 6px 8px;
                background: #FFFFFF;
            }
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus {
                border: 1px solid #60A5FA;
                background: #F8FBFF;
            }
            QPushButton {
                border-radius: 8px;
                padding: 7px 12px;
            }
            QPushButton:hover {
                background: #EFF6FF;
            }
            QHeaderView::section {
                background: #F1F5F9;
                color: #334155;
                border: none;
                border-bottom: 1px solid #E2E8F0;
                padding: 7px;
                font-weight: 600;
            }
            QTableWidget {
                gridline-color: #E5E7EB;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                background: #FFFFFF;
                alternate-background-color: #F8FAFC;
            }
            """
        )

    def _on_nav_changed(self, idx: int) -> None:
        self.pages.setCurrentIndex(idx)
        self._animate_page_switch()

    def _animate_page_switch(self) -> None:
        if self._page_opacity_effect is None or self._page_fade_anim is None:
            return
        self._page_fade_anim.stop()
        self._page_opacity_effect.setOpacity(0.82)
        self._page_fade_anim.start()

    def _build_profile_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        box = QGroupBox("个人信息")
        box_layout = QGridLayout(box)
        box_layout.setHorizontalSpacing(18)
        box_layout.setVerticalSpacing(12)

        labels = [
            ("姓名", "lbl_pi_name"),
            ("学号", "lbl_pi_student_no"),
            ("年级", "lbl_pi_grade"),
            ("学院", "lbl_pi_dept"),
            ("专业", "lbl_pi_major"),
            ("班级", "lbl_pi_class"),
            ("专业排名", "lbl_pi_major_rank"),
            ("GPA", "lbl_pi_gpa"),
        ]
        for i, (title, obj_name) in enumerate(labels):
            k = QLabel(f"{title}：")
            k.setStyleSheet("font-size:15px; font-weight:600;")
            v = QLabel("—")
            v.setObjectName(obj_name)
            v.setStyleSheet("font-size:15px;")
            box_layout.addWidget(k, i, 0)
            box_layout.addWidget(v, i, 1)
            setattr(self, obj_name, v)

        pwd_box = QGroupBox("修改密码")
        pwd_layout = QFormLayout(pwd_box)
        pwd_layout.setHorizontalSpacing(16)
        pwd_layout.setVerticalSpacing(10)
        self._edit_old_pwd = QLineEdit()
        self._edit_new_pwd = QLineEdit()
        self._edit_cfm_pwd = QLineEdit()
        for edit in (self._edit_old_pwd, self._edit_new_pwd, self._edit_cfm_pwd):
            edit.setEchoMode(QLineEdit.EchoMode.Password)
            edit.setMinimumWidth(280)
        self._edit_old_pwd.setPlaceholderText("请输入旧密码")
        self._edit_new_pwd.setPlaceholderText("至少 6 位")
        self._edit_cfm_pwd.setPlaceholderText("再次输入新密码")
        pwd_layout.addRow("旧密码：", self._edit_old_pwd)
        pwd_layout.addRow("新密码：", self._edit_new_pwd)
        pwd_layout.addRow("确认新密码：", self._edit_cfm_pwd)
        self.btn_change_pwd = QPushButton("修改密码")
        self.btn_change_pwd.setObjectName("primaryButton")
        self.btn_change_pwd.clicked.connect(self._on_change_password)
        pwd_layout.addRow("", self.btn_change_pwd)

        layout.addWidget(box)
        layout.addWidget(pwd_box)
        layout.addStretch(1)
        return w

    def _build_select_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        action_row = QHBoxLayout()
        self.edt_course_search = QLineEdit()
        self.edt_course_search.setPlaceholderText("数据库检索：课程/教师/教室关键词")
        self.btn_course_search = QPushButton("搜索")
        self.btn_course_search.setObjectName("secondaryButton")
        self.btn_course_search.clicked.connect(self._on_course_search)
        self.edt_course_search.returnPressed.connect(self._on_course_search)
        self.btn_enroll = QPushButton("选中课程 -> 选课")
        self.btn_enroll.setText("选课")
        self.btn_enroll.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))
        self.btn_enroll.clicked.connect(self._on_enroll)
        self.btn_drop = QPushButton("退课")
        self.btn_drop.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        self.btn_drop.clicked.connect(self._on_drop)
        self.btn_cancel_waiting = QPushButton("取消候补")
        self.btn_cancel_waiting.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserStop))
        self.btn_cancel_waiting.clicked.connect(self._on_cancel_waiting)
        action_row.addWidget(self.edt_course_search, 1)
        action_row.addWidget(self.btn_course_search)
        action_row.addWidget(self.btn_enroll)
        action_row.addWidget(self.btn_drop)
        action_row.addWidget(self.btn_cancel_waiting)
        action_row.addStretch(1)
        layout.addLayout(action_row)

        panes = QVBoxLayout()
        panes.setSpacing(10)

        g1 = QGroupBox("可选课程")
        l1 = QVBoxLayout(g1)
        self.tbl_available = QTableWidget(0, 10)
        self.tbl_available.setHorizontalHeaderLabels(
            ["teaching_id", "课程编号", "课程名", "学分", "上课时间", "教室", "任课教师", "学期", "状态", "容量/已选"]
        )
        self._setup_table_ui(self.tbl_available)
        self.tbl_available.setColumnHidden(0, True)
        self.tbl_available.setColumnWidth(1, 90)
        self.tbl_available.setColumnWidth(2, 210)
        self.tbl_available.setColumnWidth(3, 56)
        self.tbl_available.setColumnWidth(4, 260)
        self.tbl_available.setColumnWidth(5, 96)
        self.tbl_available.setColumnWidth(6, 100)
        self.tbl_available.setColumnWidth(7, 78)
        self.tbl_available.setColumnWidth(9, 90)
        l1.addWidget(self.tbl_available)

        g2 = QGroupBox("已选课程")
        l2 = QVBoxLayout(g2)
        self.tbl_selected = QTableWidget(0, 10)
        self.tbl_selected.setHorizontalHeaderLabels(
            ["teaching_id", "课程编号", "课程名", "学分", "上课时间", "教室", "任课教师", "学期", "状态", "容量/已选"]
        )
        self._setup_table_ui(self.tbl_selected)
        self.tbl_selected.setColumnHidden(0, True)
        self.tbl_selected.setColumnWidth(1, 90)
        self.tbl_selected.setColumnWidth(2, 210)
        self.tbl_selected.setColumnWidth(3, 56)
        self.tbl_selected.setColumnWidth(4, 260)
        self.tbl_selected.setColumnWidth(5, 96)
        self.tbl_selected.setColumnWidth(6, 100)
        self.tbl_selected.setColumnWidth(7, 78)
        self.tbl_selected.setColumnWidth(9, 90)
        l2.addWidget(self.tbl_selected)

        g3 = QGroupBox("候补课程")
        l3 = QVBoxLayout(g3)
        self.tbl_waiting = QTableWidget(0, 8)
        self.tbl_waiting.setHorizontalHeaderLabels(
            ["teaching_id", "排队号", "课程编号", "课程名", "上课时间", "教室", "任课教师", "学期"]
        )
        self._setup_table_ui(self.tbl_waiting)
        self.tbl_waiting.setColumnHidden(0, True)
        self.tbl_waiting.setColumnWidth(1, 72)
        self.tbl_waiting.setColumnWidth(2, 90)
        self.tbl_waiting.setColumnWidth(3, 210)
        self.tbl_waiting.setColumnWidth(4, 260)
        self.tbl_waiting.setColumnWidth(5, 96)
        self.tbl_waiting.setColumnWidth(6, 100)
        self.tbl_waiting.setColumnWidth(7, 78)
        l3.addWidget(self.tbl_waiting)

        g1.setMinimumHeight(220)
        g2.setMinimumHeight(220)
        g3.setMinimumHeight(190)

        panes.addWidget(g1, 3)
        panes.addWidget(g2, 3)
        panes.addWidget(g3, 2)
        layout.addLayout(panes)

        return w

    @staticmethod
    def _setup_table_ui(table: QTableWidget) -> None:
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setWordWrap(False)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setDefaultSectionSize(32)
        table.setStyleSheet(
            "QTableWidget::item:selected {"
            "background:#DBEAFE;"
            "color:#111827;"
            "}"
        )
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        if table.columnCount() > 4:
            table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        if table.columnCount() > 5:
            table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

    @classmethod
    def _slot_clock_range(cls, start_period: int, end_period: int) -> str:
        start_clock = cls._PERIOD_CLOCK.get(start_period, (f"第{start_period}节", ""))[0]
        end_clock = cls._PERIOD_CLOCK.get(end_period, ("", f"第{end_period}节"))[1]
        if start_clock and end_clock:
            return f"{start_clock}-{end_clock}"
        if start_clock:
            return start_clock
        if end_clock:
            return end_clock
        return f"第{start_period}-{end_period}节"

    @staticmethod
    def _clock_to_cn(hhmm: str) -> str:
        if ":" not in hhmm:
            return hhmm
        hh, mm = hhmm.split(":", 1)
        return f"{int(hh):02d}:{int(mm):02d}"

    @classmethod
    def _slot_clock_range_cn(cls, start_period: int, end_period: int) -> str:
        raw = cls._slot_clock_range(start_period, end_period)
        if "-" not in raw:
            return raw
        start_clock, end_clock = raw.split("-", 1)
        return f"{cls._clock_to_cn(start_clock)}-{cls._clock_to_cn(end_clock)}"

    def _timeslot_detail_text(self, timeslot: str) -> str:
        import re

        text = (timeslot or "").strip()
        if not text:
            return "—"
        chunks = re.split(r"[，,]", text)
        range_pat = re.compile(r"周([一二三四五六日天])\s*(\d+)\s*-\s*(\d+)\s*节")
        one_pat = re.compile(r"周([一二三四五六日天])\s*(\d+)\s*节")
        parts: list[str] = []
        for raw in chunks:
            s = raw.strip().replace(" ", "")
            if not s:
                continue
            m = range_pat.search(s)
            if m:
                wk = m.group(1)
                a = int(m.group(2))
                b = int(m.group(3))
                if b < a:
                    a, b = b, a
                parts.append(f"周{wk} {a}~{b}节 {self._slot_clock_range_cn(a, b)}")
                continue
            m2 = one_pat.search(s)
            if m2:
                wk = m2.group(1)
                a = int(m2.group(2))
                parts.append(f"周{wk} {a}~{a}节 {self._slot_clock_range_cn(a, a)}")
                continue
            parts.append(s)
        return " / ".join(parts) if parts else text

    def _timeslot_clock_text(self, timeslot: str) -> str:
        slots = self._validator.parse_timeslot(timeslot)
        if not slots:
            return "—"
        parts: list[str] = []
        for s in slots:
            text = self._slot_clock_range(s.start, s.end)
            if text not in parts:
                parts.append(text)
        return " / ".join(parts)

    # 与教师端课表保持一致：每行代表两节课为一个时间块
    _SLOT_LABELS: list[tuple[str, int, int]] = [
        ("1-2节", 1, 2),
        ("3-4节", 3, 4),
        ("5-6节", 5, 6),
        ("7-8节", 7, 8),
        ("9-10节", 9, 10),
    ]

    def _build_timetable_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        self.tbl_schedule = QTableWidget(5, 7)
        self.tbl_schedule.setHorizontalHeaderLabels(["周一", "周二", "周三", "周四", "周五", "周六", "周日"])
        slot_row_labels = [
            f"{label}\n{self._slot_clock_range_cn(s, e)}"
            for label, s, e in self._SLOT_LABELS
        ]
        self.tbl_schedule.setVerticalHeaderLabels(slot_row_labels)
        self.tbl_schedule.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_schedule.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.tbl_schedule.verticalHeader().setDefaultSectionSize(70)
        self.tbl_schedule.verticalHeader().setMinimumWidth(110)
        self.tbl_schedule.setMinimumHeight(420)
        self.tbl_schedule.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tbl_schedule)
        return w

    def _build_grade_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        self.lbl_gpa = QLabel("GPA：-")
        layout.addWidget(self.lbl_gpa)

        search_row = QHBoxLayout()
        self.edt_grade_search = QLineEdit()
        self.edt_grade_search.setPlaceholderText("输入课程名进行检索，如：数据库")
        self.btn_grade_search = QPushButton("搜索")
        self.btn_grade_search.setObjectName("secondaryButton")
        self.btn_grade_search.clicked.connect(self._apply_grade_filter)
        self.btn_grade_clear = QPushButton("清空")
        self.btn_grade_clear.setObjectName("secondaryButton")
        self.btn_grade_clear.clicked.connect(self._clear_grade_filter)
        self.edt_grade_search.returnPressed.connect(self._apply_grade_filter)
        search_row.addWidget(self.edt_grade_search, 1)
        search_row.addWidget(self.btn_grade_search)
        search_row.addWidget(self.btn_grade_clear)
        layout.addLayout(search_row)

        self.tbl_grades_current = QTableWidget(0, 8)
        self.tbl_grades_current.setHorizontalHeaderLabels(
            ["课程编号", "课程名", "学分", "平时分", "卷面分", "最终分", "绩点", "等级"]
        )
        self._setup_table_ui(self.tbl_grades_current)
        self.tbl_grades_current.setWordWrap(False)
        self.tbl_grades_current.setColumnWidth(0, 92)
        self.tbl_grades_current.setColumnWidth(1, 320)
        self.tbl_grades_current.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        layout.addWidget(self.tbl_grades_current)
        self.btn_export_grades = QPushButton("打印成绩单(导出Excel)")
        self.btn_export_grades.setObjectName("primaryButton")
        self.btn_export_grades.clicked.connect(self._on_export_grades)
        layout.addWidget(self.btn_export_grades)
        return w

    def _build_exam_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        self.tbl_exams = QTableWidget(0, 7)
        self.tbl_exams.setHorizontalHeaderLabels(
            ["course_id", "课程编号", "课程名", "考试日期", "考试时间", "考场", "考试状态"]
        )
        self._setup_table_ui(self.tbl_exams)
        self.tbl_exams.setColumnHidden(0, True)
        self.tbl_exams.setColumnWidth(1, 92)
        self.tbl_exams.setColumnWidth(2, 260)
        self.tbl_exams.setColumnWidth(6, 90)
        layout.addWidget(self.tbl_exams)

        search_row = QHBoxLayout()
        self.edt_exam_search = QLineEdit()
        self.edt_exam_search.setPlaceholderText("输入课程名检索考试记录")
        self.btn_exam_search = QPushButton("搜索")
        self.btn_exam_search.setObjectName("secondaryButton")
        self.btn_exam_search.clicked.connect(self._apply_exam_filter)
        self.btn_exam_clear = QPushButton("清空")
        self.btn_exam_clear.setObjectName("secondaryButton")
        self.btn_exam_clear.clicked.connect(self._clear_exam_filter)
        self.edt_exam_search.returnPressed.connect(self._apply_exam_filter)
        search_row.addWidget(self.edt_exam_search, 1)
        search_row.addWidget(self.btn_exam_search)
        search_row.addWidget(self.btn_exam_clear)
        layout.addLayout(search_row)

        req_row = QHBoxLayout()
        self.btn_apply_defer = QPushButton("申请缓考")
        self.btn_apply_defer.setObjectName("secondaryButton")
        self.btn_apply_defer.clicked.connect(self._on_apply_defer)
        self.btn_cancel_defer = QPushButton("取消申请")
        self.btn_cancel_defer.setObjectName("secondaryButton")
        self.btn_cancel_defer.clicked.connect(self._on_cancel_defer)
        req_row.addStretch(1)
        req_row.addWidget(self.btn_apply_defer)
        req_row.addWidget(self.btn_cancel_defer)
        layout.addLayout(req_row)
        return w

    def _build_eval_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        self.tbl_eval = QTableWidget(0, 6)
        self.tbl_eval.setHorizontalHeaderLabels(["course_id", "课程编号", "课程名", "学期", "任课教师", "打分状态"])
        self._setup_table_ui(self.tbl_eval)
        self.tbl_eval.setColumnHidden(0, True)
        self.tbl_eval.setColumnWidth(1, 92)
        self.tbl_eval.setColumnWidth(2, 260)
        self.tbl_eval.setColumnWidth(3, 80)
        self.tbl_eval.setColumnWidth(4, 120)
        self.tbl_eval.setColumnWidth(5, 120)
        self.tbl_eval.currentCellChanged.connect(self._on_eval_selection_changed)
        layout.addWidget(self.tbl_eval)

        eval_row = QHBoxLayout()
        self.spn_eval_score = QSpinBox()
        self.spn_eval_score.setRange(0, 100)
        self.spn_eval_score.setValue(0)
        self.lbl_eval_pending = QLabel("当前状态：待打分")
        self.edt_eval_comment = QTextEdit()
        self.edt_eval_comment.setPlaceholderText("请输入评语（可选）")
        self.edt_eval_comment.setFixedHeight(70)
        eval_row.addWidget(QLabel("评分(0-100)："))
        eval_row.addWidget(self.spn_eval_score)
        eval_row.addWidget(self.lbl_eval_pending)
        eval_row.addStretch(1)
        layout.addLayout(eval_row)
        layout.addWidget(self.edt_eval_comment)

        self.btn_eval = QPushButton("提交评教")
        self.btn_eval.setObjectName("primaryButton")
        self.btn_eval.clicked.connect(self._on_eval)
        layout.addWidget(self.btn_eval)
        return w

    def refresh_all(self) -> None:
        if not self._student_id:
            return

        self._semester = self._svc.current_semester()
        self.lbl_semester.setText(f"学期：{self._semester}")
        p = self._svc.get_student_profile(self._student_id)
        self._profile = p
        self.lbl_profile.setText("")

        self._available = self._svc.list_available_courses(self._student_id, self._semester)
        self._selected = self._svc.list_selected_courses(self._student_id, self._semester)
        self._waiting = self._svc.list_waiting(self._student_id, self._semester)
        self._eval_map = self._svc.list_evaluations(self._student_id, self._semester)

        self._render_profile()
        self._render_select_tables()
        self._render_schedule()
        self._render_grades()
        self._render_exams()
        self._render_eval()

    def _render_profile(self) -> None:
        p = self._profile
        gpa = self._svc.gpa_current(self._student_id)
        rk = self._svc.major_rank_by_gpa(self._student_id)
        rank_text = "—"
        if rk.get("rank_no") is not None and rk.get("total_in_major"):
            rank_text = f"第{rk.get('rank_no')}名 / 共{rk.get('total_in_major')}人"

        self.lbl_pi_name.setText(str(p.get("real_name") or "—"))
        self.lbl_pi_student_no.setText(str(p.get("username") or "—"))
        self.lbl_pi_grade.setText(str(p.get("grade_year") or "—"))
        self.lbl_pi_dept.setText(str(p.get("dept_name") or "—"))
        self.lbl_pi_major.setText(str(p.get("major_name") or "—"))
        self.lbl_pi_class.setText(str(p.get("class_name") or "—"))
        self.lbl_pi_major_rank.setText(rank_text)
        self.lbl_pi_gpa.setText(str(gpa.get("weighted_gpa") or 0))

    def _render_select_tables(self) -> None:
        self.tbl_available.setRowCount(0)
        for r in self._available:
            if int(r.get("already_selected") or 0) == 1:
                continue
            row = self.tbl_available.rowCount()
            self.tbl_available.insertRow(row)
            vals = [
                str(r.get("teaching_id")),
                str(r.get("course_code") or ""),
                str(r.get("course_name") or ""),
                str(r.get("credits")),
                self._timeslot_detail_text(str(r.get("timeslot") or "")),
                str(r.get("classroom") or "未排教室"),
                str(r.get("teacher_name") or ""),
                str(r.get("semester") or self._semester),
                str(r.get("status") or ""),
                f"{r.get('max_count')}/{r.get('enrolled_count')}",
            ]
            for c, v in enumerate(vals):
                self.tbl_available.setItem(row, c, QTableWidgetItem(v))

        self.tbl_selected.setRowCount(0)
        for r in self._selected:
            row = self.tbl_selected.rowCount()
            self.tbl_selected.insertRow(row)
            vals = [
                str(r.get("teaching_id")),
                str(r.get("course_code") or ""),
                str(r.get("course_name") or ""),
                str(r.get("credits")),
                self._timeslot_detail_text(str(r.get("timeslot") or "")),
                str(r.get("classroom") or "未排教室"),
                str(r.get("teacher_name") or ""),
                str(r.get("semester") or self._semester),
                str(r.get("status") or ""),
                f"{r.get('max_count')}/{r.get('enrolled_count')}",
            ]
            for c, v in enumerate(vals):
                self.tbl_selected.setItem(row, c, QTableWidgetItem(v))

        self.tbl_waiting.setRowCount(0)
        for r in self._waiting:
            row = self.tbl_waiting.rowCount()
            self.tbl_waiting.insertRow(row)
            vals = [
                str(r.get("teaching_id")),
                str(r.get("queue_no")),
                str(r.get("course_code") or ""),
                str(r.get("course_name") or ""),
                self._timeslot_detail_text(str(r.get("timeslot") or "")),
                str(r.get("classroom") or "未排教室"),
                str(r.get("teacher_name") or ""),
                str(r.get("semester") or self._semester),
            ]
            for c, v in enumerate(vals):
                self.tbl_waiting.setItem(row, c, QTableWidgetItem(v))

    def _render_schedule(self) -> None:
        for r in range(self.tbl_schedule.rowCount()):
            for c in range(self.tbl_schedule.columnCount()):
                self.tbl_schedule.setSpan(r, c, 1, 1)
                self.tbl_schedule.setItem(r, c, QTableWidgetItem(""))

        # 与教师端统一：用 (start-1)//2 映射节次到行（5行格式）
        colors = [QColor("#D6EAF8"), QColor("#D5F5E3"), QColor("#EBDEF0"), QColor("#FDEBD0")]
        for i, c in enumerate(self._selected):
            slots = self._validator.parse_timeslot(str(c.get("timeslot") or ""))
            for s in slots:
                row = (s.start - 1) // 2
                if row < 0 or row > 4:
                    continue
                col = s.weekday
                if col < 0 or col > 6:
                    continue
                prev = self.tbl_schedule.item(row, col)
                prev_text = prev.text().strip() if prev else ""
                content = (
                    f"{str(c.get('course_name') or c.get('course_code') or '').strip()}"
                    f"\n{str(c.get('classroom') or '未排教室').strip()}"
                )
                merged = content if not prev_text else f"{prev_text}\n{content}"
                item = QTableWidgetItem(merged)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setBackground(QBrush(colors[i % len(colors)]))
                item.setForeground(QBrush(QColor("#1F2937")))
                self.tbl_schedule.setItem(row, col, item)

    def _render_grades(self) -> None:
        gpa = self._svc.gpa_current(self._student_id)
        self.lbl_gpa.setText(
            f"GPA：{gpa.get('weighted_gpa', 0)}  学分：{gpa.get('total_credits', 0)}  已计课程：{gpa.get('course_count', 0)}"
        )
        self._grades_current_raw = self._svc.list_grades_current(self._student_id, self._semester)
        self._apply_grade_filter()

    def _apply_grade_filter(self) -> None:
        keyword = (self.edt_grade_search.text() or "").strip().lower()
        curr = self._grades_current_raw
        if keyword:
            curr = [r for r in curr if keyword in str(r.get("course_name") or "").lower()]

        self.tbl_grades_current.setRowCount(0)
        for r in curr:
            row = self.tbl_grades_current.rowCount()
            self.tbl_grades_current.insertRow(row)
            vals = [
                str(r.get("course_code") or ""),
                str(r.get("course_name") or ""),
                str(r.get("credits") or ""),
                str(r.get("daily_score") if r.get("daily_score") is not None else "—"),
                str(r.get("exam_score") if r.get("exam_score") is not None else "—"),
                str(r.get("final_score") if r.get("final_score") is not None else "—"),
                str(r.get("gpa_point") if r.get("gpa_point") is not None else "—"),
                str(r.get("grade_letter") or "—"),
            ]
            final_score = r.get("final_score")
            is_fail = False
            try:
                is_fail = final_score is not None and float(final_score) < 60
            except (TypeError, ValueError):
                is_fail = False
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if is_fail:
                    item.setForeground(QBrush(QColor("#E74C3C")))
                self.tbl_grades_current.setItem(row, c, item)


    def _clear_grade_filter(self) -> None:
        self.edt_grade_search.clear()
        self._apply_grade_filter()

    def _render_exams(self) -> None:
        self._exam_rows_raw = self._svc.list_upcoming_exams(self._student_id, self._semester)
        self._apply_exam_filter()

    def _apply_exam_filter(self) -> None:
        keyword = (self.edt_exam_search.text() or "").strip().lower()
        rows = self._exam_rows_raw
        if keyword:
            rows = [r for r in rows if keyword in str(r.get("course_name") or "").lower()]
        self.tbl_exams.setRowCount(0)
        for r in rows:
            row = self.tbl_exams.rowCount()
            self.tbl_exams.insertRow(row)
            # 已有成绩 → 考试已完成；否则显示缓考申请状态
            if int(r.get("has_grade") or 0):
                status_text = "考试已完成"
            else:
                defer_status = str(r.get("defer_status") or "NONE")
                status_text = {
                    "PENDING": "缓考待审批",
                    "APPROVED": "缓考已批准",
                    "REJECTED": "缓考已驳回",
                    "NONE": "未申请缓考",
                }.get(defer_status, defer_status)
            start_text = str(r.get("start_time") or "")
            end_text = str(r.get("end_time") or "")
            start_hm = ":".join(start_text.split(":")[:2]) if ":" in start_text else start_text
            end_hm = ":".join(end_text.split(":")[:2]) if ":" in end_text else end_text
            exam_time = f"{start_hm}-{end_hm}" if start_hm and end_hm else "—"

            vals = [
                str(r.get("course_id")),
                str(r.get("course_code") or ""),
                str(r.get("course_name") or ""),
                str(r.get("exam_date") or ""),
                exam_time,
                str(r.get("exam_room") or ""),
                status_text,
            ]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if status_text == "考试已完成":
                    item.setForeground(QBrush(QColor("#16A34A")))
                self.tbl_exams.setItem(row, c, item)

    def _clear_exam_filter(self) -> None:
        self.edt_exam_search.clear()
        self._apply_exam_filter()

    def _render_eval(self) -> None:
        self.tbl_eval.setRowCount(0)
        for r in self._selected:
            row = self.tbl_eval.rowCount()
            self.tbl_eval.insertRow(row)
            cid = int(r.get("course_id") or 0)
            score_status = "未打分"
            if cid in self._eval_map and self._eval_map[cid].get("eval_score") is not None:
                score_status = str(self._eval_map[cid].get("eval_score"))
            self.tbl_eval.setItem(row, 0, QTableWidgetItem(str(cid)))
            self.tbl_eval.setItem(row, 1, QTableWidgetItem(str(r.get("course_code") or "")))
            self.tbl_eval.setItem(row, 2, QTableWidgetItem(str(r.get("course_name") or "")))
            self.tbl_eval.setItem(row, 3, QTableWidgetItem(str(r.get("semester") or self._semester)))
            self.tbl_eval.setItem(row, 4, QTableWidgetItem(str(r.get("teacher_name") or "")))
            self.tbl_eval.setItem(row, 5, QTableWidgetItem(score_status))

    def _selected_course_id(self, table: QTableWidget, col: int = 0) -> int | None:
        row = table.currentRow()
        if row < 0:
            return None
        item = table.item(row, col)
        if item is None:
            return None
        try:
            return int(item.text())
        except ValueError:
            return None

    def _on_refresh_clicked(self) -> None:
        if not self._student_id:
            return
        try:
            page_idx = self.nav.currentRow()
            self._semester = self._svc.current_semester()
            self.lbl_semester.setText(f"学期：{self._semester}")

            if page_idx == 0:  # 个人信息
                self._profile = self._svc.get_student_profile(self._student_id)
                self._edit_old_pwd.clear()
                self._edit_new_pwd.clear()
                self._edit_cfm_pwd.clear()
                self._render_profile()
            elif page_idx == 1:  # 选课系统
                self.edt_course_search.clear()
                self._available = self._svc.list_available_courses(self._student_id, self._semester)
                self._selected = self._svc.list_selected_courses(self._student_id, self._semester)
                self._waiting = self._svc.list_waiting(self._student_id, self._semester)
                self._render_select_tables()
            elif page_idx == 2:  # 课表查询
                self._selected = self._svc.list_selected_courses(self._student_id, self._semester)
                self._render_schedule()
            elif page_idx == 3:  # 成绩查询
                self.edt_grade_search.clear()
                self._render_grades()
            elif page_idx == 4:  # 考试查询
                self.edt_exam_search.clear()
                self._render_exams()
            elif page_idx == 5:  # 课程评教
                self.spn_eval_score.setValue(0)
                self.edt_eval_comment.clear()
                self.lbl_eval_pending.setText("当前状态：待打分")
                self._selected = self._svc.list_selected_courses(self._student_id, self._semester)
                self._eval_map = self._svc.list_evaluations(self._student_id, self._semester)
                self._render_eval()

            QMessageBox.information(self, "刷新完成", "已刷新当前页面。")
        except (ValidationError, BusinessError) as exc:
            QMessageBox.warning(self, "刷新失败", str(exc))
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "系统错误", f"刷新发生未预期异常：{exc}")

    def _on_enroll(self) -> None:
        cid = self._selected_course_id(self.tbl_available)
        if cid is None:
            QMessageBox.information(self, "提示", "请先在可选课程里选择一条记录")
            return
        try:
            result = self._selection.attempt_enroll(self._student_id, cid)
            QMessageBox.information(self, "选课结果", str(result.get("msg") if isinstance(result, dict) else result))
            self.refresh_all()
        except (ValidationError, BusinessError) as exc:
            QMessageBox.warning(self, "选课失败", str(exc))
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "系统错误", f"选课发生未预期异常：{exc}")

    def _on_drop(self) -> None:
        cid = self._selected_course_id(self.tbl_selected)
        if cid is None:
            QMessageBox.information(self, "提示", "请先在已选课程里选择一条记录")
            return
        try:
            result = self._selection.drop_course(self._student_id, cid)
            QMessageBox.information(self, "退课结果", str(result.get("msg") if isinstance(result, dict) else result))
            self.refresh_all()
        except (ValidationError, BusinessError) as exc:
            QMessageBox.warning(self, "退课失败", str(exc))
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "系统错误", f"退课发生未预期异常：{exc}")

    def _on_cancel_waiting(self) -> None:
        cid = self._selected_course_id(self.tbl_waiting)
        if cid is None:
            QMessageBox.information(self, "提示", "请先在候补队列里选择一条记录")
            return
        try:
            result = self._selection.cancel_waiting(self._student_id, cid)
            QMessageBox.information(self, "取消候补结果", str(result.get("msg") if isinstance(result, dict) else result))
            self.refresh_all()
        except (ValidationError, BusinessError) as exc:
            QMessageBox.warning(self, "取消候补失败", str(exc))
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "系统错误", f"取消候补发生未预期异常：{exc}")

    def _on_apply_defer(self) -> None:
        cid = self._selected_course_id(self.tbl_exams)
        if cid is None:
            QMessageBox.information(self, "提示", "请先在考试列表中选中一门课程")
            return
        status_item = self.tbl_exams.item(self.tbl_exams.currentRow(), 6)
        if status_item and status_item.text() != "未申请":
            QMessageBox.information(self, "提示", "已申请过，无需重复申请")
            return
        try:
            ok = self._svc.submit_exam_defer_request(self._student_id, cid, self._semester)
            if ok:
                QMessageBox.information(self, "成功", "申请成功")
            else:
                QMessageBox.information(self, "提示", "已申请过，无需重复申请")
            self._render_exams()
        except (ValidationError, BusinessError) as exc:
            QMessageBox.warning(self, "申请失败", str(exc))
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "系统错误", f"提交缓考申请异常：{exc}")

    def _on_cancel_defer(self) -> None:
        cid = self._selected_course_id(self.tbl_exams)
        if cid is None:
            QMessageBox.information(self, "提示", "请先在考试列表中选中一门课程")
            return
        try:
            ok = self._svc.cancel_exam_defer_request(self._student_id, cid, self._semester)
            if ok:
                QMessageBox.information(self, "成功", "已取消申请")
            else:
                QMessageBox.information(self, "提示", "当前没有可取消的缓考申请")
            self._render_exams()
        except (ValidationError, BusinessError) as exc:
            QMessageBox.warning(self, "取消失败", str(exc))
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "系统错误", f"取消缓考申请异常：{exc}")

    def _on_eval(self) -> None:
        cid = self._selected_course_id(self.tbl_eval)
        if cid is None:
            QMessageBox.information(self, "提示", "请先选择课程")
            return
        try:
            old_score = self._eval_map.get(cid, {}).get("eval_score")
            if old_score is not None:
                reply = QMessageBox.question(
                    self,
                    "确认修改",
                    f"该课程已打分（当前：{old_score}），是否更改打分？",
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            self._svc.submit_evaluation(
                self._student_id,
                cid,
                self._semester,
                int(self.spn_eval_score.value()),
                self.edt_eval_comment.toPlainText().strip(),
            )
            QMessageBox.information(self, "成功", "评教提交成功")
            self.edt_eval_comment.clear()
            self.spn_eval_score.setValue(0)
            self.lbl_eval_pending.setText("当前状态：待打分")
            self.refresh_all()
        except (ValidationError, BusinessError) as exc:
            QMessageBox.warning(self, "提交失败", str(exc))
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "系统错误", f"评教提交异常：{exc}")

    def _on_eval_selection_changed(self) -> None:
        if self.tbl_eval.currentRow() < 0:
            return
        self.spn_eval_score.setValue(0)
        self.edt_eval_comment.clear()
        self.lbl_eval_pending.setText("当前状态：待打分")

    def _on_export_grades(self) -> None:
        try:
            from openpyxl import Workbook

            path, _ = QFileDialog.getSaveFileName(self, "导出成绩单", "成绩单.xlsx", "Excel 文件 (*.xlsx)")
            if not path:
                return
            wb = Workbook()
            ws = wb.active
            ws.title = "成绩单"
            ws.append(["课程编号", "课程名", "学分", "平时分", "卷面分", "最终分", "绩点", "等级"])
            for r in self._grades_current_raw:
                ws.append(
                    [
                        r.get("course_code"),
                        r.get("course_name"),
                        r.get("credits"),
                        r.get("daily_score"),
                        r.get("exam_score"),
                        r.get("final_score"),
                        r.get("gpa_point"),
                        r.get("grade_letter"),
                    ]
                )
            wb.save(path)
            QMessageBox.information(self, "成功", f"成绩单已导出：{path}")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "导出失败", f"导出成绩单失败：{exc}")

    def _on_course_search(self) -> None:
        keyword = (self.edt_course_search.text() or "").strip()
        key = keyword.lower()
        shown_rows = [r for r in self._available if int(r.get("already_selected") or 0) != 1]
        for row, rec in enumerate(shown_rows):
            hay = (
                f"{rec.get('course_code') or ''} "
                f"{rec.get('course_name') or ''} "
                f"{rec.get('teacher_name') or ''} "
                f"{rec.get('classroom') or ''}"
            ).lower()
            match = (not key) or (key in hay)
            self.tbl_available.setRowHidden(row, not match)

    def _on_change_password(self) -> None:
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
            AuthService.update_password(self._student_id, old_pwd, new_pwd)
            QMessageBox.information(self, "修改成功", "密码已成功修改。")
            self._edit_old_pwd.clear()
            self._edit_new_pwd.clear()
            self._edit_cfm_pwd.clear()
        except AuthError as exc:
            QMessageBox.warning(self, "修改失败", str(exc))
        except (ValidationError, BusinessError) as exc:
            QMessageBox.warning(self, "修改失败", str(exc))

    def _simulate_competition(self) -> None:
        """
        并发演示亮点（简化版）：
        用“当前学生 + 另一个学生ID”连续调用同一课程存储过程，
        展示名额竞争结果（成功/候补）。
        """
        cid = self._selected_course_id(self.tbl_available)
        if cid is None:
            QMessageBox.information(self, "提示", "请先在可选课程中选中一个目标课程")
            return
        if not self._student_id:
            return

        # 找一个不同学生做对手（优先 stu002 / id=2 可能不稳定，按数据库查）
        other_rows = StudentService.list_available_courses(self._student_id, self._semester)
        _ = other_rows

        # 直接取一个固定偏移ID演示，失败不影响主流程
        rival_id = self._student_id + 1
        out = []
        try:
            r1 = self._selection.attempt_enroll(self._student_id, cid)
            out.append(f"当前账号: {r1}")
        except Exception as e:  # noqa: BLE001
            out.append(f"当前账号: {e}")
        try:
            r2 = self._selection.attempt_enroll(rival_id, cid)
            out.append(f"模拟对手(student_id={rival_id}): {r2}")
        except Exception as e:  # noqa: BLE001
            out.append(f"模拟对手(student_id={rival_id}): {e}")

        QMessageBox.information(self, "并发抢课演示结果", "\n".join(out))
        self.refresh_all()

