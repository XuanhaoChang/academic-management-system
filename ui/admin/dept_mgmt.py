from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox, QFileDialog, QFrame, QGridLayout, QHeaderView,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
)

from core.exceptions import BusinessError, ValidationError
from services.admin_service import AdminService


class DeptMgmtWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.selected_dept_id: int | None = None
        self._build_ui()
        self.refresh_depts()

    def _clear_selected_dept(self) -> None:
        self.selected_dept_id = None
        self.input_dept_id.clear()
        self.input_dept_code.clear()
        self.input_dept_name.clear()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        # 1. 标题区
        title = QLabel("院系管理")
        title.setObjectName("sectionTitle")
        subtitle = QLabel("管理系统的基础组织单元")
        subtitle.setObjectName("sectionSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # 卡片容器
        card = QFrame()
        card.setObjectName("actionCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 8, 10, 8)
        card_layout.setSpacing(10)

        # 2. 新增表单卡片 (区)
        create_title = QLabel("新增院系")
        create_title.setObjectName("helperText")
        card_layout.addWidget(create_title)

        create_grid = QGridLayout()
        create_grid.setHorizontalSpacing(10)
        create_grid.setVerticalSpacing(8)

        self.input_new_code = QLineEdit()
        self.input_new_code.setPlaceholderText("如 CS")
        self.input_new_name = QLineEdit()
        self.input_new_name.setPlaceholderText("如 计算机学院")

        create_grid.addWidget(QLabel("院系代码"), 0, 0)
        create_grid.addWidget(self.input_new_code, 0, 1)
        create_grid.addWidget(QLabel("院系名称"), 0, 2)
        create_grid.addWidget(self.input_new_name, 0, 3)
        card_layout.addLayout(create_grid)

        create_row = QHBoxLayout()
        self.btn_create_dept = QPushButton("添加院系")
        self.btn_create_dept.setObjectName("primaryButton")
        self.btn_create_dept.clicked.connect(self.create_dept)
        create_row.addStretch(1)
        create_row.addWidget(self.btn_create_dept)
        card_layout.addLayout(create_row)

        # 3. 编辑表单卡片 (区)
        edit_title = QLabel("编辑院系")
        edit_title.setObjectName("helperText")
        card_layout.addWidget(edit_title)

        form_grid = QGridLayout()
        form_grid.setHorizontalSpacing(10)
        form_grid.setVerticalSpacing(8)

        self.input_dept_id = QLineEdit()
        self.input_dept_id.setReadOnly(True)
        self.input_dept_code = QLineEdit()
        self.input_dept_name = QLineEdit()

        form_grid.addWidget(QLabel("院系ID"), 0, 0)
        form_grid.addWidget(self.input_dept_id, 0, 1)
        form_grid.addWidget(QLabel("院系代码"), 0, 2)
        form_grid.addWidget(self.input_dept_code, 0, 3)
        form_grid.addWidget(QLabel("院系名称"), 1, 0)
        form_grid.addWidget(self.input_dept_name, 1, 1)

        card_layout.addLayout(form_grid)

        edit_row = QHBoxLayout()
        self.btn_refresh = QPushButton("刷新列表")
        self.btn_refresh.setObjectName("secondaryButton")
        self.btn_refresh.clicked.connect(self._on_refresh_clicked)
        self.btn_update = QPushButton("保存修改")
        self.btn_update.setObjectName("primaryButton")
        self.btn_update.clicked.connect(self.update_dept)
        self.btn_delete_selected = QPushButton("删除选中")
        self.btn_delete_selected.setObjectName("dangerButton")
        self.btn_delete_selected.clicked.connect(self.delete_dept)
        edit_row.addWidget(self.btn_refresh)
        edit_row.addWidget(self.btn_update)
        edit_row.addWidget(self.btn_delete_selected)
        card_layout.addLayout(edit_row)

        # 4. 搜索栏
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索院系...")
        self.search_input.textChanged.connect(self._filter_depts)
        card_layout.addWidget(self.search_input)

        # 5. 数据表格
        self.dept_table = QTableWidget(0, 4)
        self.dept_table.setObjectName("dataTable")
        self.dept_table.setHorizontalHeaderLabels(["ID", "院系代码", "院系名称", "创建时间"])
        header = self.dept_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.dept_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.dept_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.dept_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.dept_table.setSortingEnabled(True)
        self.dept_table.itemSelectionChanged.connect(self._on_dept_selected)
        card_layout.addWidget(self.dept_table)

        # 5. 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.status_label.setObjectName("statusLabel")
        card_layout.addWidget(self.status_label)

        layout.addWidget(card)
        layout.addStretch(1)

    def refresh_depts(self) -> None:
        depts = AdminService.list_depts(include_deleted=False)
        header = self.dept_table.horizontalHeader()
        sort_column = 0
        sort_order = Qt.SortOrder.AscendingOrder
        if header is not None:
            sort_column = header.sortIndicatorSection()
            sort_order = header.sortIndicatorOrder()

        self.dept_table.setSortingEnabled(False)
        self.dept_table.clearContents()
        self.dept_table.setRowCount(len(depts))
        for i, d in enumerate(depts):
            self.dept_table.setItem(i, 0, QTableWidgetItem(str(d["id"])))
            self.dept_table.setItem(i, 1, QTableWidgetItem(d["dept_code"]))
            self.dept_table.setItem(i, 2, QTableWidgetItem(d["dept_name"]))
            self.dept_table.setItem(i, 3, QTableWidgetItem(str(d["created_at"])))

        self.dept_table.setSortingEnabled(True)
        if 0 <= sort_column < self.dept_table.columnCount():
            self.dept_table.sortItems(sort_column, sort_order)

        self.dept_table.clearSelection()
        self._clear_selected_dept()
        self._filter_depts(self.search_input.text())

    def _on_refresh_clicked(self) -> None:
        # Refresh button should always perform a full reload rather than keeping an old search filter.
        self.search_input.blockSignals(True)
        self.search_input.clear()
        self.search_input.blockSignals(False)
        self.refresh_depts()
        self.status_label.setText("院系列表已刷新")

    def create_dept(self) -> None:
        try:
            code = self.input_new_code.text().strip()
            name = self.input_new_name.text().strip()
            if not code or not name:
                raise ValidationError("代码和名称不能为空")
            AdminService.create_dept(code, name)
            self.status_label.setText(f"院系 {name} 创建成功")
            QMessageBox.information(self, "成功", "院系创建成功")
            self.input_new_code.clear()
            self.input_new_name.clear()
            self.refresh_depts()
        except BusinessError as exc:
            self.status_label.setText(f"创建失败: {exc}")
            QMessageBox.warning(self, "创建失败", str(exc))

    def update_dept(self) -> None:
        if self.selected_dept_id is None:
            QMessageBox.warning(self, "修改失败", "请先在下方表格中选择一个院系")
            return

        try:
            AdminService.update_dept(
                self.selected_dept_id,
                self.input_dept_code.text(),
                self.input_dept_name.text()
            )
            self.status_label.setText(f"院系 {self.selected_dept_id} 修改成功")
            QMessageBox.information(self, "成功", "院系信息已更新")
            self.refresh_depts()
        except BusinessError as exc:
            self.status_label.setText(f"修改失败: {exc}")
            QMessageBox.warning(self, "修改失败", str(exc))

    def delete_dept(self) -> None:
        if self.selected_dept_id is None:
            QMessageBox.warning(self, "删除失败", "请先在下方表格中选择一个院系")
            return

        try:
            AdminService.soft_delete_dept(self.selected_dept_id)
            self.status_label.setText(f"院系 {self.selected_dept_id} 已被逻辑删除")
            QMessageBox.information(self, "成功", f"已逻辑删除院系 {self.selected_dept_id}")
            self.refresh_depts()
        except BusinessError as exc:
            self.status_label.setText(f"删除失败: {exc}")
            QMessageBox.warning(self, "删除失败", str(exc))

    def _on_dept_selected(self) -> None:
        selected_items = self.dept_table.selectedItems()
        if not selected_items:
            self._clear_selected_dept()
            return

        row = selected_items[0].row()
        if row < 0:
            self._clear_selected_dept()
            return

        dept_id_item = self.dept_table.item(row, 0)
        dept_code_item = self.dept_table.item(row, 1)
        dept_name_item = self.dept_table.item(row, 2)

        if not dept_id_item or not dept_code_item or not dept_name_item:
            return

        self.selected_dept_id = int(dept_id_item.text())
        self.input_dept_id.setText(dept_id_item.text())
        self.input_dept_code.setText(dept_code_item.text())
        self.input_dept_name.setText(dept_name_item.text())

    def _filter_depts(self, text: str) -> None:
        search_text = text.strip().lower()
        visible_count = 0
        for row in range(self.dept_table.rowCount()):
            if not search_text:
                self.dept_table.setRowHidden(row, False)
                visible_count += 1
            else:
                match_found = False
                for col in range(self.dept_table.columnCount()):
                    if col == self.dept_table.columnCount() - 1:
                        continue
                    item = self.dept_table.item(row, col)
                    if item and search_text in item.text().lower():
                        match_found = True
                        break
                self.dept_table.setRowHidden(row, not match_found)
                if match_found:
                    visible_count += 1

        current_row = self.dept_table.currentRow()
        if current_row < 0 or self.dept_table.isRowHidden(current_row):
            self.dept_table.clearSelection()
            self._clear_selected_dept()

        total_count = self.dept_table.rowCount()
        if search_text:
            self.status_label.setText(f"共 {total_count} 条院系记录，匹配 {visible_count} 条")
        else:
            self.status_label.setText(f"已加载 {visible_count} 条院系记录")
