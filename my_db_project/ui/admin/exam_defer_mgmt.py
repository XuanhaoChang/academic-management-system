from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from core.exceptions import BusinessError, ValidationError
from services.admin_service import AdminService


class ExamDeferMgmtWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._build_ui()
        self.refresh_requests()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        title = QLabel("缓考审批")
        title.setObjectName("sectionTitle")
        subtitle = QLabel("管理员审批学生缓考申请")
        subtitle.setObjectName("sectionSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        card = QFrame()
        card.setObjectName("actionCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 8, 10, 8)
        card_layout.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("状态筛选"))
        self.cmb_status = QComboBox()
        self.cmb_status.addItem("全部", "")
        self.cmb_status.addItem("待审批", "PENDING")
        self.cmb_status.addItem("已批准", "APPROVED")
        self.cmb_status.addItem("已拒绝", "REJECTED")
        self.cmb_status.currentIndexChanged.connect(self.refresh_requests)
        top_row.addWidget(self.cmb_status)

        btn_refresh = QPushButton("刷新")
        btn_refresh.setObjectName("secondaryButton")
        btn_refresh.clicked.connect(self.refresh_requests)
        top_row.addWidget(btn_refresh)
        top_row.addStretch(1)
        card_layout.addLayout(top_row)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["申请ID", "学号", "学生", "课程", "学期", "原因", "状态", "提交时间"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            header.setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        card_layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        self.btn_approve = QPushButton("批准")
        self.btn_approve.setObjectName("primaryButton")
        self.btn_approve.setEnabled(False)
        self.btn_approve.clicked.connect(self._approve)

        self.btn_reject = QPushButton("拒绝")
        self.btn_reject.setObjectName("dangerButton")
        self.btn_reject.setEnabled(False)
        self.btn_reject.clicked.connect(self._reject)

        btn_row.addWidget(self.btn_approve)
        btn_row.addWidget(self.btn_reject)
        btn_row.addStretch(1)
        card_layout.addLayout(btn_row)

        self.status_label = QLabel("就绪")
        self.status_label.setObjectName("statusLabel")
        card_layout.addWidget(self.status_label)

        layout.addWidget(card)
        layout.addStretch(1)

    def _selected_req_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if item is None:
            return None
        try:
            return int(item.text())
        except ValueError:
            return None

    def _on_selection_changed(self) -> None:
        req_id = self._selected_req_id()
        if req_id is None:
            self.btn_approve.setEnabled(False)
            self.btn_reject.setEnabled(False)
            return

        row = self.table.currentRow()
        status_item = self.table.item(row, 6)
        status_text = status_item.text() if status_item else ""
        pending = (status_text == "待审批")
        self.btn_approve.setEnabled(pending)
        self.btn_reject.setEnabled(pending)

    def refresh_requests(self) -> None:
        status = self.cmb_status.currentData()
        try:
            rows = AdminService.list_exam_defer_requests(status if status else None)
        except BusinessError as exc:
            self.status_label.setText(f"加载失败：{exc}")
            return

        self.table.setRowCount(0)
        status_map = {
            "PENDING": "待审批",
            "APPROVED": "已批准",
            "REJECTED": "已拒绝",
        }
        for r in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            vals = [
                str(r.get("req_id", "")),
                str(r.get("student_no") or ""),
                str(r.get("student_name") or ""),
                f"{r.get('course_code', '')} {r.get('course_name', '')}".strip(),
                str(r.get("semester") or ""),
                str(r.get("reason") or ""),
                status_map.get(str(r.get("status") or ""), str(r.get("status") or "")),
                str(r.get("created_at") or "")[:16],
            ]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if c == 6:
                    if vals[6] == "待审批":
                        item.setForeground(Qt.GlobalColor.darkYellow)
                    elif vals[6] == "已批准":
                        item.setForeground(Qt.GlobalColor.darkGreen)
                    elif vals[6] == "已拒绝":
                        item.setForeground(Qt.GlobalColor.darkRed)
                self.table.setItem(row, c, item)

        self.btn_approve.setEnabled(False)
        self.btn_reject.setEnabled(False)
        self.status_label.setText(f"已加载 {len(rows)} 条缓考申请")

    def _approve(self) -> None:
        req_id = self._selected_req_id()
        if req_id is None:
            QMessageBox.information(self, "提示", "请先选择一条申请")
            return
        try:
            AdminService.process_exam_defer_request(req_id, "APPROVED")
            QMessageBox.information(self, "成功", "已批准缓考申请")
            self.refresh_requests()
        except (ValidationError, BusinessError) as exc:
            QMessageBox.warning(self, "审批失败", str(exc))

    def _reject(self) -> None:
        req_id = self._selected_req_id()
        if req_id is None:
            QMessageBox.information(self, "提示", "请先选择一条申请")
            return
        try:
            AdminService.process_exam_defer_request(req_id, "REJECTED")
            QMessageBox.information(self, "成功", "已拒绝缓考申请")
            self.refresh_requests()
        except (ValidationError, BusinessError) as exc:
            QMessageBox.warning(self, "审批失败", str(exc))
