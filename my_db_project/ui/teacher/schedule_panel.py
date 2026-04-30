"""SchedulePanel — [组员A] 教师课表 + 调课申请面板

子Tab 0：我的课表
  - 学期下拉切换
  - QTableWidget 周历网格（行=时间段，列=周一~周日）
  - 单元格按课程着色，点击显示详情
  - 课表数据来自 view_teacher_schedule（timeslot 字段为组长录入的文本）

子Tab 1：申请调课
  - 选择课程 → 自动填写原时间
  - 填写申请时间 + 原因 → 提交
  - 显示历史申请列表（含状态 badge）
"""
from __future__ import annotations

import re
from typing import Optional

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QBrush, QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.exceptions import BusinessError, ValidationError
from core.session import Session
from services.teacher_service import TeacherService


# ------------------------------------------------------------------
# 时间段解析工具函数
# ------------------------------------------------------------------
WEEKDAY_MAP: dict[str, int] = {
    "周一": 0, "周二": 1, "周三": 2, "周四": 3,
    "周五": 4, "周六": 5, "周日": 6,
}

# 节次 → 行索引（每行代表一个时间段）
SLOT_ROWS: list[str] = ["1-2节", "3-4节", "5-6节", "7-8节", "9-10节"]
SLOT_MAP: dict[str, int] = {s: i for i, s in enumerate(SLOT_ROWS)}

# 课程颜色循环（背景色）
COURSE_COLORS: list[str] = [
    "#D6EAF8", "#D5F5E3", "#FDEBD0", "#F9EBEA",
    "#E8DAEF", "#D7DBDD", "#FDFEFE", "#EBF5FB",
]


def parse_timeslot(timeslot_str: str) -> list[tuple[int, int]]:
    """解析 timeslot 文本，返回 [(col, row), ...] 列表。

    输入示例: "周一3-4节,周三3-4节" 或 "周二1-2节,周四1-2节"
    未识别的片段静默跳过（不崩溃）。
    """
    if not timeslot_str:
        return []

    result: list[tuple[int, int]] = []
    parts = [p.strip() for p in timeslot_str.split(",")]
    for part in parts:
        # 匹配 "周X数字-数字节" 格式
        m = re.match(r"(周[一二三四五六日])(\d+-\d+节?)", part)
        if not m:
            continue
        weekday_str = m.group(1)
        slot_raw    = m.group(2)
        # 规范化节次：确保末尾有"节"
        if not slot_raw.endswith("节"):
            slot_raw += "节"

        col = WEEKDAY_MAP.get(weekday_str)
        row = SLOT_MAP.get(slot_raw)
        if col is not None and row is not None:
            result.append((col, row))
    return result


# ------------------------------------------------------------------
# SchedulePanel
# ------------------------------------------------------------------
class SchedulePanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._svc = TeacherService()
        # {(semester, course_name): color_hex}
        self._color_map: dict[tuple[str, str], str] = {}
        self._color_idx = 0
        # 当前加载的授课行 [{teaching_id, course_name, ...}]
        self._schedule_rows: list[dict] = []
        self._setup_ui()

    # ------------------------------------------------------------------
    # UI 构建
    # ------------------------------------------------------------------
    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self._tabs = QTabWidget()
        root.addWidget(self._tabs)

        self._tabs.addTab(self._build_schedule_tab(), "我的课表")
        self._tabs.addTab(self._build_reschedule_tab(), "申请调课")

    # ——— 子Tab 0：我的课表 ———————————————————————————————————————————
    def _build_schedule_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # 顶部控制行
        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("学期："))
        self._cmb_semester = QComboBox()
        self._cmb_semester.setFixedWidth(160)
        self._cmb_semester.currentTextChanged.connect(self._load_schedule)
        ctrl.addWidget(self._cmb_semester)

        btn_refresh = QPushButton("刷新")
        btn_refresh.setFixedWidth(72)
        btn_refresh.clicked.connect(self._refresh_semesters)
        ctrl.addWidget(btn_refresh)
        ctrl.addStretch()
        layout.addLayout(ctrl)

        # 周历表格
        self._tbl_schedule = QTableWidget(len(SLOT_ROWS), 7)
        self._tbl_schedule.setHorizontalHeaderLabels(
            ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        )
        self._tbl_schedule.setVerticalHeaderLabels(SLOT_ROWS)
        self._tbl_schedule.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._tbl_schedule.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._tbl_schedule.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._tbl_schedule.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._tbl_schedule.cellClicked.connect(self._on_cell_clicked)
        self._tbl_schedule.setMinimumHeight(280)
        layout.addWidget(self._tbl_schedule, stretch=1)

        # 详情区
        detail_box = QGroupBox("课程详情")
        detail_layout = QFormLayout(detail_box)
        detail_layout.setSpacing(6)
        detail_layout.setContentsMargins(12, 12, 12, 12)

        self._detail_labels: dict[str, QLabel] = {}
        for key in ("课程名称", "课程编号", "学　分", "教　室",
                    "上课时间", "选课人数", "课程状态", "成绩状态"):
            lbl = QLabel("—")
            lbl.setStyleSheet("color: #34495e;")
            self._detail_labels[key] = lbl
            detail_layout.addRow(f"{key}：", lbl)

        layout.addWidget(detail_box)
        return w

    # ——— 子Tab 1：申请调课 ————————————————————————————————————————
    def _build_reschedule_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # 申请表单
        form_box = QGroupBox("提交调课申请")
        form_box.setStyleSheet("QGroupBox { font-size: 13px; font-weight: bold; }")
        form_layout = QFormLayout(form_box)
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(14, 16, 14, 14)

        self._cmb_req_course = QComboBox()
        self._cmb_req_course.setMinimumWidth(240)
        self._cmb_req_course.currentIndexChanged.connect(self._on_req_course_changed)

        self._edit_orig_time = QLineEdit()
        self._edit_orig_time.setReadOnly(True)
        self._edit_orig_time.setStyleSheet("background-color: #ecf0f1;")
        self._edit_orig_time.setPlaceholderText("选择课程后自动填写")

        # 申请调整到：用下拉选择器代替自由文本
        req_time_widget = QWidget()
        req_time_layout = QHBoxLayout(req_time_widget)
        req_time_layout.setContentsMargins(0, 0, 0, 0)
        req_time_layout.setSpacing(6)

        self._cmb_req_week = QComboBox()
        self._cmb_req_week.addItems([f"第{w}教学周" for w in range(1, 21)])
        self._cmb_req_week.setFixedWidth(120)

        self._cmb_req_weekday = QComboBox()
        self._cmb_req_weekday.addItems(["周一", "周二", "周三", "周四", "周五", "周六", "周日"])
        self._cmb_req_weekday.setFixedWidth(90)

        self._cmb_req_slot = QComboBox()
        self._cmb_req_slot.addItems(["1-2节", "3-4节", "5-6节", "7-8节", "9-10节"])
        self._cmb_req_slot.setFixedWidth(100)

        req_time_layout.addWidget(self._cmb_req_week)
        req_time_layout.addWidget(self._cmb_req_weekday)
        req_time_layout.addWidget(self._cmb_req_slot)
        req_time_layout.addStretch()

        # 申请原因：快捷标签 + 自由文本
        reason_widget = QWidget()
        reason_vbox = QVBoxLayout(reason_widget)
        reason_vbox.setContentsMargins(0, 0, 0, 0)
        reason_vbox.setSpacing(4)

        # 快捷标签行
        _REASON_TAGS = [
            "时间冲突", "教室占用", "教师出差", "学生活动冲突",
            "节假日补课", "考试周调整", "其他原因",
        ]
        tag_row = QHBoxLayout()
        tag_row.setSpacing(6)
        tag_hint = QLabel("快捷原因：")
        tag_hint.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        tag_row.addWidget(tag_hint)
        for tag_text in _REASON_TAGS:
            btn_tag = QPushButton(tag_text)
            btn_tag.setCheckable(True)
            btn_tag.setStyleSheet(
                "QPushButton { background-color: #ECF0F1; color: #555; border: 1px solid #BDC3C7; "
                "border-radius: 10px; padding: 2px 10px; font-size: 11px; } "
                "QPushButton:checked { background-color: #3498DB; color: white; border-color: #2980B9; } "
                "QPushButton:hover { background-color: #D6EAF8; }"
            )
            btn_tag.clicked.connect(lambda checked, t=tag_text: self._toggle_reason_tag(t))
            tag_row.addWidget(btn_tag)
        tag_row.addStretch()
        reason_vbox.addLayout(tag_row)

        self._edit_reason = QTextEdit()
        self._edit_reason.setFixedHeight(60)
        self._edit_reason.setPlaceholderText("点击上方标签快速填写，或直接输入详细原因（必填）")
        reason_vbox.addWidget(self._edit_reason)

        form_layout.addRow("选择课程：",  self._cmb_req_course)
        form_layout.addRow("原上课时间：", self._edit_orig_time)
        form_layout.addRow("申请调整到：", req_time_widget)
        form_layout.addRow("申请原因：",  reason_widget)

        btn_submit = QPushButton("提交申请")
        btn_submit.setFixedWidth(110)
        btn_submit.setStyleSheet(
            "QPushButton { background-color: #27ae60; color: white; "
            "border-radius: 4px; padding: 6px 14px; } "
            "QPushButton:hover { background-color: #2ecc71; }"
        )
        btn_submit.clicked.connect(self._on_submit_request)
        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_submit)
        btn_row.addStretch()
        form_layout.addRow("", btn_row)

        layout.addWidget(form_box)

        # 历史申请列表
        hist_box = QGroupBox("我的申请记录")
        hist_box.setStyleSheet("QGroupBox { font-size: 13px; font-weight: bold; }")
        hist_layout = QVBoxLayout(hist_box)
        hist_layout.setContentsMargins(10, 14, 10, 10)

        btn_refresh_req = QPushButton("刷新")
        btn_refresh_req.setFixedWidth(72)
        btn_refresh_req.clicked.connect(self._load_request_list)
        refresh_row = QHBoxLayout()
        refresh_row.addStretch()
        refresh_row.addWidget(btn_refresh_req)
        hist_layout.addLayout(refresh_row)

        self._tbl_requests = QTableWidget(0, 7)
        self._tbl_requests.setHorizontalHeaderLabels(
            ["课程", "学期", "原时间", "申请时间", "状态", "管理员意见", "提交时间"]
        )
        self._tbl_requests.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self._tbl_requests.horizontalHeader().setStretchLastSection(True)
        self._tbl_requests.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._tbl_requests.setAlternatingRowColors(True)
        hist_layout.addWidget(self._tbl_requests)

        layout.addWidget(hist_box)
        return w

    # ------------------------------------------------------------------
    # 数据加载
    # ------------------------------------------------------------------
    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._refresh_semesters()
        self._load_req_course_combo()
        self._load_request_list()

    def _refresh_semesters(self) -> None:
        if Session.current_user is None:
            return
        try:
            semesters = self._svc.get_available_semesters_for_teacher(Session.current_user.id)
            self._cmb_semester.blockSignals(True)
            self._cmb_semester.clear()
            self._cmb_semester.addItems(semesters)
            self._cmb_semester.blockSignals(False)
            if semesters:
                self._load_schedule(semesters[0])
        except Exception as exc:
            QMessageBox.warning(self, "加载失败", str(exc))

    def _load_schedule(self, semester: str = "") -> None:
        if not semester:
            semester = self._cmb_semester.currentText()
        if not semester or Session.current_user is None:
            return

        try:
            all_rows = self._svc.get_my_schedule(Session.current_user.id)
        except Exception as exc:
            QMessageBox.warning(self, "加载失败", str(exc))
            return

        self._schedule_rows = [r for r in all_rows if r["semester"] == semester]
        self._render_schedule_grid()

    def _render_schedule_grid(self) -> None:
        # 清空表格
        for r in range(len(SLOT_ROWS)):
            for c in range(7):
                self._tbl_schedule.setItem(r, c, QTableWidgetItem(""))
                self._tbl_schedule.item(r, c).setBackground(QBrush(QColor("#f5f5f5")))

        for row in self._schedule_rows:
            timeslot = row.get("timeslot") or ""
            course_name = row.get("course_name", "")
            classroom   = row.get("classroom") or ""
            key = (row.get("semester", ""), course_name)

            # 分配颜色
            if key not in self._color_map:
                color = COURSE_COLORS[self._color_idx % len(COURSE_COLORS)]
                self._color_map[key] = color
                self._color_idx += 1
            color = self._color_map[key]

            cells = parse_timeslot(timeslot)
            for col, r in cells:
                text = f"{course_name}\n{classroom}"
                item = QTableWidgetItem(text)
                item.setBackground(QBrush(QColor(color)))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                font = QFont()
                font.setPointSize(9)
                item.setFont(font)
                # 存 teaching_id 以便点击查看详情
                item.setData(Qt.ItemDataRole.UserRole, row.get("teaching_id"))
                self._tbl_schedule.setItem(r, col, item)

    def _on_cell_clicked(self, row: int, col: int) -> None:
        item = self._tbl_schedule.item(row, col)
        if item is None:
            return
        teaching_id = item.data(Qt.ItemDataRole.UserRole)
        if teaching_id is None:
            self._clear_detail()
            return

        # 从缓存中找匹配的行
        info = next((r for r in self._schedule_rows if r.get("teaching_id") == teaching_id), None)
        if info is None:
            return

        self._detail_labels["课程名称"].setText(info.get("course_name", "—"))
        self._detail_labels["课程编号"].setText(info.get("course_code", "—"))
        self._detail_labels["学　分"].setText(str(info.get("credits", "—")))
        self._detail_labels["教　室"].setText(info.get("classroom") or "—")
        self._detail_labels["上课时间"].setText(info.get("timeslot") or "—")
        enrolled = info.get("enrolled_count", 0)
        max_c    = info.get("max_count", 0)
        self._detail_labels["选课人数"].setText(f"{enrolled} / {max_c}")
        status_map = {"OPEN": "开放", "CLOSED": "已关闭", "FULL": "已满"}
        self._detail_labels["课程状态"].setText(status_map.get(info.get("status", ""), "—"))
        submitted = info.get("is_submitted", 0)
        self._detail_labels["成绩状态"].setText(
            "✅ 已提交锁定" if submitted else "📝 未提交"
        )

    def _clear_detail(self) -> None:
        for lbl in self._detail_labels.values():
            lbl.setText("—")

    # ——— 调课申请 ——————————————————————————————————————————————————
    def _load_req_course_combo(self) -> None:
        if Session.current_user is None:
            return
        try:
            rows = self._svc.get_my_schedule(Session.current_user.id)
            self._cmb_req_course.blockSignals(True)
            self._cmb_req_course.clear()
            for r in rows:
                display = f"{r['course_name']} ({r['semester']})"
                self._cmb_req_course.addItem(display, userData=r)
            self._cmb_req_course.blockSignals(False)
            self._on_req_course_changed(0)
        except Exception:
            pass

    def _on_req_course_changed(self, _index: int) -> None:
        row = self._cmb_req_course.currentData()
        if row:
            self._edit_orig_time.setText(row.get("timeslot") or "")
        else:
            self._edit_orig_time.clear()

    def _on_submit_request(self) -> None:
        if Session.current_user is None:
            return

        row = self._cmb_req_course.currentData()
        if row is None:
            QMessageBox.warning(self, "提示", "请先选择课程。")
            return

        teaching_id   = row["teaching_id"]
        original_time = self._edit_orig_time.text().strip() or None
        # 从下拉框拼接申请时间，格式如 "第3教学周 周四5-6节"
        requested_time = (
            self._cmb_req_week.currentText() + " "
            + self._cmb_req_weekday.currentText()
            + self._cmb_req_slot.currentText()
        )
        reason = self._edit_reason.toPlainText().strip()

        try:
            self._svc.submit_reschedule_request(
                teaching_id=teaching_id,
                teacher_id=Session.current_user.id,
                reason=reason,
                original_time=original_time,
                requested_time=requested_time,
            )
            QMessageBox.information(self, "提交成功", "调课申请已提交，等待管理员审批。")
            self._edit_reason.clear()
            self._load_request_list()
        except ValidationError as exc:
            QMessageBox.warning(self, "提交失败", str(exc))
        except BusinessError as exc:
            QMessageBox.warning(self, "提交失败", str(exc))

    def _load_request_list(self) -> None:
        if Session.current_user is None:
            return
        try:
            rows = self._svc.list_my_reschedule_requests(Session.current_user.id)
        except Exception as exc:
            QMessageBox.warning(self, "加载失败", str(exc))
            return

        # 若数据库暂无记录，展示一条 mock 示例让界面看起来完整
        _mock_injected = False
        if not rows:
            rows = [{
                "course_name":    "（示例）数据库原理",
                "semester":       "2024-2",
                "original_time":  "周二3-4节",
                "requested_time": "周四5-6节",
                "status":         "PENDING",
                "admin_comment":  None,
                "created_at":     "2026-03-24 10:00",
            }]
            _mock_injected = True

        self._tbl_requests.setRowCount(len(rows))
        STATUS_COLOR = {
            "PENDING":  "#F39C12",
            "APPROVED": "#27AE60",
            "REJECTED": "#E74C3C",
        }
        STATUS_TEXT = {
            "PENDING":  "⏳ 待审批",
            "APPROVED": "✅ 已批准",
            "REJECTED": "❌ 已拒绝",
        }
        for i, r in enumerate(rows):
            vals = [
                r.get("course_name", ""),
                r.get("semester", ""),
                r.get("original_time") or "—",
                r.get("requested_time") or "—",
                STATUS_TEXT.get(r.get("status", ""), r.get("status", "")),
                r.get("admin_comment") or "—",
                str(r.get("created_at", ""))[:16],
            ]
            for j, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if j == 4:  # 状态列着色
                    color = STATUS_COLOR.get(r.get("status", ""), "#7F8C8D")
                    item.setForeground(QBrush(QColor(color)))
                    font = QFont()
                    font.setBold(True)
                    item.setFont(font)
                self._tbl_requests.setItem(i, j, item)

            # mock 行整体灰色斜体，提示这是示例数据
            if _mock_injected:
                mock_font = QFont()
                mock_font.setItalic(True)
                for j in range(7):
                    cell = self._tbl_requests.item(i, j)
                    if cell:
                        cell.setForeground(QBrush(QColor("#999999")))
                        if j != 4:  # 状态列保留彩色，只改字体
                            cell.setFont(mock_font)

    def _toggle_reason_tag(self, tag: str) -> None:
        """点击快捷标签：已有该标签则移除，否则追加。"""
        current = self._edit_reason.toPlainText().strip()
        if tag in current:
            # 移除该标签（含可能的逗号和空格）
            new_text = current.replace(f"、{tag}", "").replace(f"{tag}、", "").replace(tag, "")
            self._edit_reason.setPlainText(new_text.strip("、 "))
        else:
            sep = "、" if current else ""
            self._edit_reason.setPlainText(f"{current}{sep}{tag}")
