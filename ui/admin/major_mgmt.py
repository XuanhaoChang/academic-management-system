from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox, QFrame, QGridLayout, QHeaderView,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
)

from core.exceptions import BusinessError
from services.admin_service import AdminService


class MajorMgmtWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.selected_major_id: int | None = None
        self._majors_by_id: dict[int, dict] = {}
        self._build_ui()
        self._load_departments()
        self.refresh_majors()

    def _clear_selected_major(self) -> None:
        self.selected_major_id = None
        self.input_major_id.clear()
        self.input_major_code.clear()
        self.input_major_name.clear()
        if self.combo_edit_dept.count() > 0:
            self.combo_edit_dept.setCurrentIndex(0)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        title = QLabel("专业管理")
        title.setObjectName("sectionTitle")
        subtitle = QLabel("管理系统中的学科专业分类")
        subtitle.setObjectName("sectionSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        card = QFrame()
        card.setObjectName("actionCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 8, 10, 8)
        card_layout.setSpacing(10)

        create_title = QLabel("新增专业")
        create_title.setObjectName("helperText")
        card_layout.addWidget(create_title)

        create_grid = QGridLayout()
        create_grid.setHorizontalSpacing(10)
        create_grid.setVerticalSpacing(8)

        self.input_new_major_code = QLineEdit()
        self.input_new_major_code.setPlaceholderText("专业代码")
        self.input_new_major_name = QLineEdit()
        self.input_new_major_name.setPlaceholderText("专业名称")
        self.combo_new_dept = QComboBox()

        create_grid.addWidget(QLabel("专业代码"), 0, 0)
        create_grid.addWidget(self.input_new_major_code, 0, 1)
        create_grid.addWidget(QLabel("专业名称"), 0, 2)
        create_grid.addWidget(self.input_new_major_name, 0, 3)
        create_grid.addWidget(QLabel("所属院系"), 1, 0)
        create_grid.addWidget(self.combo_new_dept, 1, 1)
        card_layout.addLayout(create_grid)

        create_row = QHBoxLayout()
        self.btn_create_major = QPushButton("添加专业")
        self.btn_create_major.setObjectName("primaryButton")
        self.btn_create_major.clicked.connect(self.create_major)
        create_row.addStretch(1)
        create_row.addWidget(self.btn_create_major)
        card_layout.addLayout(create_row)

        form_grid = QGridLayout()
        form_grid.setHorizontalSpacing(10)
        form_grid.setVerticalSpacing(8)

        self.input_major_id = QLineEdit()
        self.input_major_id.setReadOnly(True)
        self.input_major_code = QLineEdit()
        self.input_major_name = QLineEdit()
        self.combo_edit_dept = QComboBox()

        form_grid.addWidget(QLabel("专业ID"), 0, 0)
        form_grid.addWidget(self.input_major_id, 0, 1)
        form_grid.addWidget(QLabel("专业代码"), 0, 2)
        form_grid.addWidget(self.input_major_code, 0, 3)
        form_grid.addWidget(QLabel("专业名称"), 1, 0)
        form_grid.addWidget(self.input_major_name, 1, 1)
        form_grid.addWidget(QLabel("所属院系"), 1, 2)
        form_grid.addWidget(self.combo_edit_dept, 1, 3)

        card_layout.addLayout(form_grid)

        edit_row = QHBoxLayout()
        self.btn_refresh = QPushButton("刷新列表")
        self.btn_refresh.setObjectName("secondaryButton")
        self.btn_refresh.clicked.connect(self.refresh_majors)
        self.btn_update = QPushButton("保存修改")
        self.btn_update.setObjectName("primaryButton")
        self.btn_update.clicked.connect(self.update_major)
        self.btn_delete_selected = QPushButton("删除选中")
        self.btn_delete_selected.setObjectName("dangerButton")
        self.btn_delete_selected.clicked.connect(self.delete_major)
        edit_row.addWidget(self.btn_refresh)
        edit_row.addWidget(self.btn_update)
        edit_row.addWidget(self.btn_delete_selected)
        card_layout.addLayout(edit_row)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索专业...")
        self.search_input.textChanged.connect(self._filter_majors)
        card_layout.addWidget(self.search_input)

        self.major_table = QTableWidget(0, 5)
        self.major_table.setObjectName("dataTable")
        self.major_table.setHorizontalHeaderLabels(["ID", "专业代码", "专业名称", "所属院系", "创建时间"])
        header = self.major_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.major_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.major_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.major_table.setSortingEnabled(True)
        self.major_table.itemSelectionChanged.connect(self._on_major_selected)
        card_layout.addWidget(self.major_table)

        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.status_label.setObjectName("statusLabel")
        card_layout.addWidget(self.status_label)

        layout.addWidget(card)
        layout.addStretch(1)

    def _load_departments(self) -> None:
        try:
            depts = AdminService.list_depts(include_deleted=False)
            self.combo_new_dept.clear()
            self.combo_edit_dept.clear()
            for d in depts:
                self.combo_new_dept.addItem(d["dept_name"], d["id"])
                self.combo_edit_dept.addItem(d["dept_name"], d["id"])
        except Exception as e:
            self.status_label.setText(f"加载院系失败: {e}")

    def refresh_majors(self) -> None:
        try:
            majors = AdminService.list_majors(include_deleted=False)
            self._majors_by_id = {int(m["id"]): m for m in majors}

            header = self.major_table.horizontalHeader()
            sort_column = 0
            sort_order = Qt.SortOrder.AscendingOrder
            if header is not None:
                sort_column = header.sortIndicatorSection()
                sort_order = header.sortIndicatorOrder()

            self.major_table.setSortingEnabled(False)
            self.major_table.clearContents()
            self.major_table.setRowCount(len(majors))

            for i, m in enumerate(majors):
                self.major_table.setItem(i, 0, QTableWidgetItem(str(m.get("id", ""))))
                self.major_table.setItem(i, 1, QTableWidgetItem(str(m.get("major_code", ""))))
                self.major_table.setItem(i, 2, QTableWidgetItem(str(m.get("major_name", ""))))
                self.major_table.setItem(i, 3, QTableWidgetItem(str(m.get("dept_name", ""))))
                self.major_table.setItem(i, 4, QTableWidgetItem(str(m.get("created_at", ""))))

            self.major_table.setSortingEnabled(True)
            if 0 <= sort_column < self.major_table.columnCount():
                self.major_table.sortItems(sort_column, sort_order)

            self.major_table.clearSelection()
            self._clear_selected_major()
            self._filter_majors(self.search_input.text())

            self.status_label.setText(f"已加载 {len(majors)} 条专业记录")
        except Exception as e:
            self.status_label.setText(f"刷新失败: {e}")

    def create_major(self) -> None:
        try:
            dept_id = self.combo_new_dept.currentData()
            if dept_id is None:
                raise BusinessError("请先选择所属院系")
                
            AdminService.create_major(
                self.input_new_major_code.text(),
                self.input_new_major_name.text(),
                int(dept_id),
            )
            self.status_label.setText(f"专业 {self.input_new_major_name.text().strip()} 创建成功")
            QMessageBox.information(self, "成功", "专业创建成功")
            self.input_new_major_code.clear()
            self.input_new_major_name.clear()
            self.refresh_majors()
        except BusinessError as exc:
            self.status_label.setText(f"创建失败: {exc}")
            QMessageBox.warning(self, "创建失败", str(exc))
        except Exception as exc:
            self.status_label.setText(f"创建失败: {exc}")
            QMessageBox.critical(self, "错误", str(exc))

    def _on_major_selected(self) -> None:
        selected_items = self.major_table.selectedItems()
        if not selected_items:
            self._clear_selected_major()
            return

        row = selected_items[0].row()
        if row < 0:
            self._clear_selected_major()
            return

        id_item = self.major_table.item(row, 0)
        code_item = self.major_table.item(row, 1)
        name_item = self.major_table.item(row, 2)
        dept_item = self.major_table.item(row, 3)

        if not id_item or not code_item or not name_item or not dept_item:
            return

        self.selected_major_id = int(id_item.text())
        self.input_major_id.setText(id_item.text())
        self.input_major_code.setText(code_item.text())
        self.input_major_name.setText(name_item.text())

        major = self._majors_by_id.get(self.selected_major_id)
        if not major:
            return
        idx = self.combo_edit_dept.findData(major.get("dept_id"))
        if idx >= 0:
            self.combo_edit_dept.setCurrentIndex(idx)

    def update_major(self) -> None:
        if self.selected_major_id is None:
            QMessageBox.warning(self, "修改失败", "请先在下方表格中选择一个专业")
            return

        try:
            dept_id = self.combo_edit_dept.currentData()
            if dept_id is None:
                raise BusinessError("请选择所属院系")

            AdminService.update_major(
                self.selected_major_id,
                self.input_major_code.text(),
                self.input_major_name.text(),
                int(dept_id),
            )
            self.status_label.setText(f"专业 {self.selected_major_id} 修改成功")
            QMessageBox.information(self, "成功", "专业信息已更新")
            self.refresh_majors()
        except BusinessError as exc:
            self.status_label.setText(f"修改失败: {exc}")
            QMessageBox.warning(self, "修改失败", str(exc))
        except Exception as exc:
            self.status_label.setText(f"修改失败: {exc}")
            QMessageBox.critical(self, "错误", str(exc))

    def delete_major(self) -> None:
        if self.selected_major_id is None:
            QMessageBox.warning(self, "删除失败", "请先在下方表格中选择一个专业")
            return

        try:
            AdminService.soft_delete_major(self.selected_major_id)
            self.status_label.setText(f"专业 {self.selected_major_id} 已被删除")
            QMessageBox.information(self, "成功", f"已删除专业 {self.selected_major_id}")
            self.refresh_majors()
        except BusinessError as exc:
            self.status_label.setText(f"删除失败: {exc}")
            QMessageBox.warning(self, "删除失败", str(exc))
        except Exception as exc:
            self.status_label.setText(f"删除失败: {exc}")
            QMessageBox.critical(self, "错误", str(exc))

    def _filter_majors(self, text: str) -> None:
        search_text = text.strip().lower()
        visible_count = 0
        for row in range(self.major_table.rowCount()):
            if not search_text:
                self.major_table.setRowHidden(row, False)
                visible_count += 1
            else:
                match_found = False
                for col in range(self.major_table.columnCount()):
                    if col == self.major_table.columnCount() - 1:
                        continue
                    item = self.major_table.item(row, col)
                    if item and search_text in item.text().lower():
                        match_found = True
                        break
                self.major_table.setRowHidden(row, not match_found)
                if match_found:
                    visible_count += 1

        current_row = self.major_table.currentRow()
        if current_row < 0 or self.major_table.isRowHidden(current_row):
            self.major_table.clearSelection()
            self._clear_selected_major()

        total_count = self.major_table.rowCount()
        if search_text:
            self.status_label.setText(f"共 {total_count} 条专业记录，匹配 {visible_count} 条")
