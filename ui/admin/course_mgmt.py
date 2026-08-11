from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox, QFrame, QGridLayout, QHeaderView,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
    QSpinBox, QTextEdit, QTableWidget, QTableWidgetItem, 
    QVBoxLayout, QWidget
)
from core.exceptions import BusinessError, ValidationError
from services.admin_service import AdminService

class CourseMgmtWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.selected_course_id: int | None = None
        self._build_ui()
        self._load_departments()
        self.refresh_courses()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        # Title Area
        title = QLabel("课程管理")
        title.setObjectName("sectionTitle")
        subtitle = QLabel("管理系统中的课程基本信息")
        subtitle.setObjectName("sectionSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # New Course Form Card
        card = QFrame()
        card.setObjectName("actionCard")
        card_layout = QGridLayout(card)
        card_layout.setContentsMargins(10, 8, 10, 8)
        card_layout.setSpacing(10)

        self.input_new_code = QLineEdit()
        self.input_new_code.setPlaceholderText("课程代码")
        
        self.input_new_name = QLineEdit()
        self.input_new_name.setPlaceholderText("课程名称")
        
        self.spin_new_credits = QSpinBox()
        self.spin_new_credits.setRange(1, 10)
        self.spin_new_credits.setValue(3)
        
        self.spin_new_capacity = QSpinBox()
        self.spin_new_capacity.setRange(1, 500)
        self.spin_new_capacity.setValue(50)
        
        self.combo_new_dept = QComboBox()
        
        from PyQt6.QtWidgets import QSizePolicy
        self.text_new_desc = QTextEdit()
        self.text_new_desc.setPlaceholderText("课程简介")
        self.text_new_desc.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        btn_add = QPushButton("添加课程")
        btn_add.setObjectName("primaryButton")
        btn_add.clicked.connect(self.create_course)

        card_layout.addWidget(QLabel("课程代码:"), 0, 0)
        card_layout.addWidget(self.input_new_code, 0, 1)
        card_layout.addWidget(QLabel("课程名称:"), 0, 2)
        card_layout.addWidget(self.input_new_name, 0, 3)
        card_layout.addWidget(QLabel("学分:"), 1, 0)
        card_layout.addWidget(self.spin_new_credits, 1, 1)
        card_layout.addWidget(QLabel("容量:"), 1, 2)
        card_layout.addWidget(self.spin_new_capacity, 1, 3)
        card_layout.addWidget(QLabel("所属院系:"), 2, 0)
        card_layout.addWidget(self.combo_new_dept, 2, 1, 1, 3)
        card_layout.addWidget(QLabel("课程简介:"), 3, 0)
        card_layout.addWidget(self.text_new_desc, 3, 1, 1, 3)
        card_layout.addWidget(btn_add, 4, 3, Qt.AlignmentFlag.AlignRight)

        layout.addWidget(card)

        # Edit Course Form Card
        edit_card = QFrame()
        edit_card.setObjectName("actionCard")
        edit_layout = QGridLayout(edit_card)
        edit_layout.setContentsMargins(10, 8, 10, 8)
        edit_layout.setSpacing(10)

        self.input_edit_id = QLineEdit()
        self.input_edit_id.setReadOnly(True)
        self.input_edit_id.setPlaceholderText("选择课程以编辑")
        
        self.input_edit_code = QLineEdit()
        self.input_edit_name = QLineEdit()
        
        self.spin_edit_credits = QSpinBox()
        self.spin_edit_credits.setRange(1, 10)
        self.spin_edit_credits.setValue(3)
        
        self.spin_edit_capacity = QSpinBox()
        self.spin_edit_capacity.setRange(1, 500)
        self.spin_edit_capacity.setValue(50)
        
        self.combo_edit_dept = QComboBox()
        
        self.text_edit_desc = QTextEdit()
        self.text_edit_desc.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        edit_layout.addWidget(QLabel("课程ID:"), 0, 0)
        edit_layout.addWidget(self.input_edit_id, 0, 1)
        edit_layout.addWidget(QLabel("课程代码:"), 0, 2)
        edit_layout.addWidget(self.input_edit_code, 0, 3)
        edit_layout.addWidget(QLabel("课程名称:"), 1, 0)
        edit_layout.addWidget(self.input_edit_name, 1, 1)
        edit_layout.addWidget(QLabel("学分:"), 1, 2)
        edit_layout.addWidget(self.spin_edit_credits, 1, 3)
        edit_layout.addWidget(QLabel("容量:"), 2, 0)
        edit_layout.addWidget(self.spin_edit_capacity, 2, 1)
        edit_layout.addWidget(QLabel("所属院系:"), 2, 2)
        edit_layout.addWidget(self.combo_edit_dept, 2, 3)
        edit_layout.addWidget(QLabel("课程简介:"), 3, 0)
        edit_layout.addWidget(self.text_edit_desc, 3, 1, 1, 3)

        btn_row = QHBoxLayout()
        btn_refresh = QPushButton("刷新列表")
        btn_refresh.clicked.connect(self.refresh_courses)
        
        self.btn_save = QPushButton("保存修改")
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self.update_course)
        
        self.btn_delete = QPushButton("删除选中")
        self.btn_delete.setObjectName("dangerButton")
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self.delete_course)
        
        btn_row.addStretch()
        btn_row.addWidget(btn_refresh)
        btn_row.addWidget(self.btn_save)
        btn_row.addWidget(self.btn_delete)
        
        edit_layout.addLayout(btn_row, 4, 0, 1, 4)
        
        layout.addWidget(edit_card)

        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索课程...")
        self.search_input.textChanged.connect(self._filter_courses)
        layout.addWidget(self.search_input)

        # Data Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "课程代码", "课程名称", "学分", "容量", "院系", "创建时间"]
        )
        header = self.table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.table)

        # Status Label
        self.status_label = QLabel()
        self.status_label.setObjectName("statusLabel")
        layout.addWidget(self.status_label)

    def _load_departments(self) -> None:
        try:
            depts = AdminService.list_depts()
            self.combo_new_dept.clear()
            self.combo_edit_dept.clear()
            for d in depts:
                self.combo_new_dept.addItem(d["dept_name"], d["id"])
                self.combo_edit_dept.addItem(d["dept_name"], d["id"])
        except Exception as e:
            self.status_label.setText(f"加载院系失败: {e}")

    def refresh_courses(self) -> None:
        try:
            courses = AdminService.list_courses()
            self.table.setRowCount(0)
            for c in courses:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(c["id"])))
                self.table.setItem(row, 1, QTableWidgetItem(c["course_code"]))
                self.table.setItem(row, 2, QTableWidgetItem(c["course_name"]))
                self.table.setItem(row, 3, QTableWidgetItem(str(c["credits"])))
                self.table.setItem(row, 4, QTableWidgetItem(str(c.get("capacity") or "-")))
                self.table.setItem(row, 5, QTableWidgetItem(c.get("dept_name", "")))
                
                created_at = c.get("created_at")
                if created_at is not None and hasattr(created_at, "strftime"):
                    dt_str = getattr(created_at, "strftime")("%Y-%m-%d %H:%M")
                else:
                    dt_str = str(created_at) if created_at else ""
                self.table.setItem(row, 6, QTableWidgetItem(dt_str))
                
                # Store full data for edit selection
                item = self.table.item(row, 0)
                if item is not None:
                    item.setData(Qt.ItemDataRole.UserRole, c)
            self.status_label.setText("列表已刷新")
            self._clear_edit_form()
        except BusinessError as e:
            self.status_label.setText(f"刷新失败: {e}")

    def _on_selection_changed(self) -> None:
        items = self.table.selectedItems()
        if not items:
            self._clear_edit_form()
            return
        
        item = self.table.item(items[0].row(), 0)
        if item is None:
            return
        data = item.data(Qt.ItemDataRole.UserRole)
        self.selected_course_id = data["id"]
        
        self.input_edit_id.setText(str(data["id"]))
        self.input_edit_code.setText(data["course_code"])
        self.input_edit_name.setText(data["course_name"])
        self.spin_edit_credits.setValue(int(data["credits"]))
        self.spin_edit_capacity.setValue(int(data.get("capacity") or 50))
        
        idx = self.combo_edit_dept.findData(data["dept_id"])
        if idx >= 0:
            self.combo_edit_dept.setCurrentIndex(idx)
            
        self.text_edit_desc.setPlainText(data.get("description", "") or "")
        
        self.btn_save.setEnabled(True)
        self.btn_delete.setEnabled(True)

    def create_course(self) -> None:
        try:
            code = self.input_new_code.text().strip()
            name = self.input_new_name.text().strip()
            credits = self.spin_new_credits.value()
            capacity = self.spin_new_capacity.value()
            dept_id = self.combo_new_dept.currentData()
            desc = self.text_new_desc.toPlainText().strip()
            
            if not code or not name:
                raise ValidationError("课程代码和名称不能为空")
            if dept_id is None:
                raise ValidationError("请选择所属院系")
                
            AdminService.create_course(code, name, credits, capacity, dept_id, desc)
            self.status_label.setText(f"课程 {name} 创建成功")
            QMessageBox.information(self, "成功", "课程创建成功")
            self._clear_new_form()
            self.refresh_courses()
        except BusinessError as exc:
            self.status_label.setText(f"创建失败: {exc}")
            QMessageBox.warning(self, "创建失败", str(exc))

    def update_course(self) -> None:
        if not self.selected_course_id:
            return
        try:
            code = self.input_edit_code.text().strip()
            name = self.input_edit_name.text().strip()
            credits = self.spin_edit_credits.value()
            capacity = self.spin_edit_capacity.value()
            dept_id = self.combo_edit_dept.currentData()
            desc = self.text_edit_desc.toPlainText().strip()
            
            if not code or not name:
                raise ValidationError("课程代码和名称不能为空")
            if dept_id is None:
                raise ValidationError("请选择所属院系")
                
            AdminService.update_course(
                self.selected_course_id, code, name, credits, capacity, dept_id, desc
            )
            self.status_label.setText(f"课程 {name} 修改成功")
            QMessageBox.information(self, "成功", "课程修改成功")
            self.refresh_courses()
        except BusinessError as exc:
            self.status_label.setText(f"修改失败: {exc}")
            QMessageBox.warning(self, "修改失败", str(exc))

    def delete_course(self) -> None:
        if not self.selected_course_id:
            return
        
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除该课程吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                AdminService.soft_delete_course(self.selected_course_id)
                self.status_label.setText("课程已删除")
                self.refresh_courses()
            except BusinessError as e:
                self.status_label.setText(f"删除失败: {e}")
                QMessageBox.warning(self, "删除失败", str(e))

    def _clear_new_form(self) -> None:
        self.input_new_code.clear()
        self.input_new_name.clear()
        self.spin_new_credits.setValue(3)
        self.spin_new_capacity.setValue(50)
        if self.combo_new_dept.count() > 0:
            self.combo_new_dept.setCurrentIndex(0)
        self.text_new_desc.clear()

    def _clear_edit_form(self) -> None:
        self.selected_course_id = None
        self.input_edit_id.clear()
        self.input_edit_code.clear()
        self.input_edit_name.clear()
        self.spin_edit_credits.setValue(3)
        self.spin_edit_capacity.setValue(50)
        self.text_edit_desc.clear()
        self.btn_save.setEnabled(False)
        self.btn_delete.setEnabled(False)

    def _filter_courses(self, text: str) -> None:
        search_text = text.strip().lower()
        for row in range(self.table.rowCount()):
            if not search_text:
                self.table.setRowHidden(row, False)
            else:
                match_found = False
                for col in range(self.table.columnCount()):
                    # skip system columns: ID (col 0) and creation time (last column)
                    if col == 0 or col == self.table.columnCount() - 1:
                        continue
                    item = self.table.item(row, col)
                    if item and search_text in item.text().lower():
                        match_found = True
                        break
                self.table.setRowHidden(row, not match_found)
