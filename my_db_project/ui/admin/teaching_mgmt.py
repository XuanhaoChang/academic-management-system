from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox, QCompleter, QFrame, QGridLayout, QHeaderView,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
    QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
)
from core.constants import CourseStatus
from core.exceptions import BusinessError, ValidationError
from services.admin_service import AdminService


class TeachingMgmtWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.selected_teaching_id: int | None = None
        self._build_ui()
        self._load_initial_data()
        self.refresh_teachings()

    def _setup_completer(self, combo: QComboBox) -> None:
        combo.setEditable(True)
        completer = QCompleter(combo.model(), combo)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        combo.setCompleter(completer)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        title = QLabel("授课安排管理")
        title.setObjectName("sectionTitle")
        subtitle = QLabel("管理课程的授课信息：指定教师、时间、地点和学期")
        subtitle.setObjectName("sectionSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        card = QFrame()
        card.setObjectName("actionCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 8, 10, 8)
        card_layout.setSpacing(10)

        create_title = QLabel("新增授课安排")
        create_title.setObjectName("helperText")
        card_layout.addWidget(create_title)

        create_grid = QGridLayout()
        create_grid.setHorizontalSpacing(10)
        create_grid.setVerticalSpacing(8)

        self.combo_new_course = QComboBox()
        self._setup_completer(self.combo_new_course)
        self.combo_new_course.currentIndexChanged.connect(self._on_new_course_changed)
        self.combo_new_teacher = QComboBox()
        self._setup_completer(self.combo_new_teacher)
        self.input_new_classroom = QLineEdit()
        self.input_new_classroom.setPlaceholderText("如 A101")
        self.input_new_timeslot = QLineEdit()
        self.input_new_timeslot.setPlaceholderText("如 周一3-4节")
        self.txt_new_semester = QLineEdit()
        self.txt_new_semester.setReadOnly(True)
        self.txt_new_semester.setStyleSheet("background-color: #f5f5f5; color: #666;")
        self.spin_new_max_count = QSpinBox()
        self.spin_new_max_count.setRange(1, 500)
        self.spin_new_max_count.setValue(50)

        create_grid.addWidget(QLabel("课程 *"), 0, 0)
        create_grid.addWidget(self.combo_new_course, 0, 1)
        create_grid.addWidget(QLabel("授课教师 *"), 0, 2)
        create_grid.addWidget(self.combo_new_teacher, 0, 3)
        create_grid.addWidget(QLabel("学期 *"), 1, 0)
        create_grid.addWidget(self.txt_new_semester, 1, 1)
        create_grid.addWidget(QLabel("上课地点"), 1, 2)
        create_grid.addWidget(self.input_new_classroom, 1, 3)
        create_grid.addWidget(QLabel("上课时间"), 2, 0)
        create_grid.addWidget(self.input_new_timeslot, 2, 1)
        create_grid.addWidget(QLabel("容量"), 2, 2)
        create_grid.addWidget(self.spin_new_max_count, 2, 3)
        card_layout.addLayout(create_grid)

        create_row = QHBoxLayout()
        btn_refresh_courses = QPushButton("刷新课程列表")
        btn_refresh_courses.setObjectName("secondaryButton")
        btn_refresh_courses.clicked.connect(self._refresh_course_dropdowns)
        btn_create = QPushButton("创建授课安排")
        btn_create.setObjectName("primaryButton")
        btn_create.clicked.connect(self.create_teaching)
        create_row.addWidget(btn_refresh_courses)
        create_row.addStretch()
        create_row.addWidget(btn_create)
        card_layout.addLayout(create_row)

        card_layout.addWidget(QLabel())

        form_grid = QGridLayout()
        form_grid.setHorizontalSpacing(10)
        form_grid.setVerticalSpacing(8)

        self.input_edit_id = QLineEdit()
        self.input_edit_id.setReadOnly(True)
        self.combo_edit_course = QComboBox()
        self._setup_completer(self.combo_edit_course)
        self.combo_edit_teacher = QComboBox()
        self._setup_completer(self.combo_edit_teacher)
        self.input_edit_classroom = QLineEdit()
        self.input_edit_timeslot = QLineEdit()
        self.input_edit_semester = QLineEdit()
        self.input_edit_semester.setReadOnly(True)
        self.input_edit_semester.setStyleSheet("background-color: #f0f0f0; color: #666;")
        self.spin_edit_max_count = QSpinBox()
        self.spin_edit_max_count.setRange(1, 500)
        self.combo_edit_status = QComboBox()
        self.combo_edit_status.addItem("选课中", "OPEN")
        self.combo_edit_status.addItem("已截止", "CLOSED")
        self.combo_edit_status.addItem("已满员", "FULL")

        form_grid.addWidget(QLabel("安排ID"), 0, 0)
        form_grid.addWidget(self.input_edit_id, 0, 1)
        form_grid.addWidget(QLabel("课程"), 0, 2)
        form_grid.addWidget(self.combo_edit_course, 0, 3)
        form_grid.addWidget(QLabel("授课教师"), 1, 0)
        form_grid.addWidget(self.combo_edit_teacher, 1, 1)
        form_grid.addWidget(QLabel("学期(不可改)"), 1, 2)
        form_grid.addWidget(self.input_edit_semester, 1, 3)
        form_grid.addWidget(QLabel("上课地点"), 2, 0)
        form_grid.addWidget(self.input_edit_classroom, 2, 1)
        form_grid.addWidget(QLabel("上课时间"), 2, 2)
        form_grid.addWidget(self.input_edit_timeslot, 2, 3)
        form_grid.addWidget(QLabel("容量/已选"), 3, 0)
        form_grid.addWidget(self.spin_edit_max_count, 3, 1)
        form_grid.addWidget(QLabel("状态"), 3, 2)
        form_grid.addWidget(self.combo_edit_status, 3, 3)
        card_layout.addLayout(form_grid)

        edit_row = QHBoxLayout()
        btn_refresh = QPushButton("刷新列表")
        btn_refresh.setObjectName("secondaryButton")
        btn_refresh.clicked.connect(self.refresh_teachings)
        self.btn_save = QPushButton("保存修改")
        self.btn_save.setObjectName("primaryButton")
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self.update_teaching)
        self.btn_delete = QPushButton("删除选中")
        self.btn_delete.setObjectName("dangerButton")
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self.delete_teaching)
        edit_row.addWidget(btn_refresh)
        edit_row.addWidget(self.btn_save)
        edit_row.addWidget(self.btn_delete)
        card_layout.addLayout(edit_row)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索授课安排...")
        self.search_input.textChanged.connect(self._filter_teachings)
        card_layout.addWidget(self.search_input)

        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID", "课程", "教师", "学期", "地点", "时间", "容量", "已选", "状态", "创建时间"
        ])
        header = self.table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        card_layout.addWidget(self.table)

        self.status_label = QLabel("就绪")
        self.status_label.setObjectName("statusLabel")
        card_layout.addWidget(self.status_label)

        layout.addWidget(card)
        layout.addStretch(1)

    def _load_initial_data(self) -> None:
        try:
            courses = AdminService.list_courses()
            self.combo_new_course.clear()
            self.combo_edit_course.clear()
            for c in courses:
                text = f"{c['course_code']} - {c['course_name']}"
                self.combo_new_course.addItem(text, c["id"])
                self.combo_edit_course.addItem(text, c["id"])

            teachers = AdminService.list_teachers()
            self.combo_new_teacher.clear()
            self.combo_edit_teacher.clear()
            for t in teachers:
                self.combo_new_teacher.addItem(t["real_name"], t["id"])
                self.combo_edit_teacher.addItem(t["real_name"], t["id"])

            current_semester = AdminService.get_current_semester()
            self.txt_new_semester.setText(current_semester)
        except Exception as e:
            self.status_label.setText(f"加载数据失败: {e}")

    def _refresh_course_dropdowns(self) -> None:
        try:
            courses = AdminService.list_courses()
            self.combo_new_course.clear()
            self.combo_edit_course.clear()
            for c in courses:
                text = f"{c['course_code']} - {c['course_name']}"
                self.combo_new_course.addItem(text, c["id"])
                self.combo_edit_course.addItem(text, c["id"])
            self.status_label.setText(f"已刷新课程列表，当前 {len(courses)} 门课程")
        except Exception as e:
            self.status_label.setText(f"刷新失败: {e}")

    def _on_new_course_changed(self, index: int) -> None:
        if index < 0:
            return
        course_id = self.combo_new_course.currentData()
        if course_id is None:
            return
        courses = AdminService.list_courses()
        for c in courses:
            if c["id"] == course_id:
                self.spin_new_max_count.setValue(int(c.get("capacity") or 50))
                break


    def refresh_teachings(self) -> None:
        try:
            teachings = AdminService.list_teachings()
            self.table.setRowCount(0)
            for t in teachings:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(t["id"])))
                self.table.setItem(row, 1, QTableWidgetItem(t.get("course_name", "")))
                self.table.setItem(row, 2, QTableWidgetItem(t.get("teacher_name", "")))
                self.table.setItem(row, 3, QTableWidgetItem(t.get("semester", "")))
                self.table.setItem(row, 4, QTableWidgetItem(t.get("classroom") or "—"))
                self.table.setItem(row, 5, QTableWidgetItem(t.get("timeslot") or "—"))
                self.table.setItem(row, 6, QTableWidgetItem(str(t.get("max_count", ""))))
                self.table.setItem(row, 7, QTableWidgetItem(str(t.get("enrolled_count", ""))))
                status_map = {"OPEN": "选课中", "CLOSED": "已截止", "FULL": "已满员"}
                self.table.setItem(row, 8, QTableWidgetItem(status_map.get(t.get("status", ""), t.get("status", ""))))
                created = t.get("created_at")
                self.table.setItem(row, 9, QTableWidgetItem(str(created) if created else ""))

                item = self.table.item(row, 0)
                if item:
                    item.setData(Qt.ItemDataRole.UserRole, t)
            self.status_label.setText(f"已加载 {len(teachings)} 条授课安排")
        except BusinessError as e:
            self.status_label.setText(f"刷新失败: {e}")

    def _on_selection_changed(self) -> None:
        items = self.table.selectedItems()
        if not items:
            self._clear_edit_form()
            return
        item = self.table.item(items[0].row(), 0)
        if not item:
            return
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return

        self.selected_teaching_id = data["id"]
        self.input_edit_id.setText(str(data["id"]))

        course_idx = self.combo_edit_course.findData(data["course_id"])
        if course_idx >= 0:
            self.combo_edit_course.setCurrentIndex(course_idx)

        teacher_idx = self.combo_edit_teacher.findData(data["teacher_id"])
        if teacher_idx >= 0:
            self.combo_edit_teacher.setCurrentIndex(teacher_idx)

        self.input_edit_semester.setText(data.get("semester", ""))
        self.input_edit_classroom.setText(data.get("classroom") or "")
        self.input_edit_timeslot.setText(data.get("timeslot") or "")
        self.spin_edit_max_count.setValue(int(data.get("max_count") or 50))

        status = data.get("status", "OPEN")
        status_idx = self.combo_edit_status.findData(status)
        if status_idx >= 0:
            self.combo_edit_status.setCurrentIndex(status_idx)

        self.btn_save.setEnabled(True)
        self.btn_delete.setEnabled(True)

    def _clear_edit_form(self) -> None:
        self.selected_teaching_id = None
        self.input_edit_id.clear()
        self.input_edit_semester.clear()
        self.input_edit_classroom.clear()
        self.input_edit_timeslot.clear()
        self.spin_edit_max_count.setValue(50)
        self.btn_save.setEnabled(False)
        self.btn_delete.setEnabled(False)

    def create_teaching(self) -> None:
        try:
            course_id = self.combo_new_course.currentData()
            teacher_id = self.combo_new_teacher.currentData()
            semester = self.txt_new_semester.text().strip()
            classroom = self.input_new_classroom.text().strip() or None
            timeslot = self.input_new_timeslot.text().strip() or None
            max_count = self.spin_new_max_count.value()

            if course_id is None:
                raise ValidationError("请选择课程")
            if teacher_id is None:
                raise ValidationError("请选择授课教师")
            if not semester:
                raise ValidationError("请选择学期")

            AdminService.create_teaching(
                course_id, teacher_id, classroom, timeslot, semester, max_count
            )
            self.status_label.setText("授课安排创建成功")
            QMessageBox.information(self, "成功", "授课安排创建成功")
            self._clear_new_form()
            self._load_initial_data()
            self.refresh_teachings()
        except BusinessError as exc:
            self.status_label.setText(f"创建失败: {exc}")
            QMessageBox.warning(self, "创建失败", str(exc))

    def update_teaching(self) -> None:
        if not self.selected_teaching_id:
            return
        try:
            course_id = self.combo_edit_course.currentData()
            teacher_id = self.combo_edit_teacher.currentData()
            semester = self.input_edit_semester.text().strip()
            classroom = self.input_edit_classroom.text().strip() or None
            timeslot = self.input_edit_timeslot.text().strip() or None
            max_count = self.spin_edit_max_count.value()
            status = self.combo_edit_status.currentData()

            AdminService.update_teaching(
                self.selected_teaching_id, course_id, teacher_id,
                classroom, timeslot, semester, max_count, status
            )
            self.status_label.setText("授课安排更新成功")
            QMessageBox.information(self, "成功", "授课安排已更新")
            self.refresh_teachings()
        except BusinessError as exc:
            self.status_label.setText(f"更新失败: {exc}")
            QMessageBox.warning(self, "更新失败", str(exc))

    def delete_teaching(self) -> None:
        if not self.selected_teaching_id:
            return
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除该授课安排吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            AdminService.soft_delete_teaching(self.selected_teaching_id)
            self.status_label.setText("授课安排已删除")
            QMessageBox.information(self, "成功", "授课安排已删除")
            self.refresh_teachings()
        except BusinessError as exc:
            self.status_label.setText(f"删除失败: {exc}")
            QMessageBox.warning(self, "删除失败", str(exc))

    def _clear_new_form(self) -> None:
        if self.combo_new_course.count() > 0:
            self.combo_new_course.setCurrentIndex(0)
        if self.combo_new_teacher.count() > 0:
            self.combo_new_teacher.setCurrentIndex(0)
        current_semester = AdminService.get_current_semester()
        self.txt_new_semester.setText(current_semester)
        self.input_new_classroom.clear()
        self.input_new_timeslot.clear()
        self.spin_new_max_count.setValue(50)

    def _filter_teachings(self, text: str) -> None:
        search_text = text.strip().lower()
        for row in range(self.table.rowCount()):
            if not search_text:
                self.table.setRowHidden(row, False)
            else:
                match_found = False
                for col in range(self.table.columnCount()):
                    # Skip non-data columns: ID (0) and Created Time (last column)
                    if col == 0 or col == self.table.columnCount() - 1:
                        continue
                    item = self.table.item(row, col)
                    if item and search_text in item.text().lower():
                        match_found = True
                        break
                self.table.setRowHidden(row, not match_found)
