from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.exceptions import BusinessError
from services.admin_service import AdminService


class UserMgmtWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.selected_user_id: int | None = None
        self._all_users: list[dict] = []
        self._users_by_id: dict[int, dict] = {}
        self._depts: list[dict] = []
        self._majors_by_dept: dict[int, list[dict]] = {}
        self._build_ui()
        self.refresh_users()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        title = QLabel("用户管理")
        title.setObjectName("sectionTitle")
        subtitle = QLabel("支持CSV批量导入与逻辑删除，所有操作将写入审计日志")
        subtitle.setObjectName("sectionSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        card = QFrame()
        card.setObjectName("actionCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 8, 10, 8)
        card_layout.setSpacing(10)

        # helper = QLabel("建议先导入测试用户，再执行删除操作验证软删除流程")
        # helper.setObjectName("helperText")
        # helper.setWordWrap(True)
        # card_layout.addWidget(helper)

        create_title = QLabel("新增账户")
        create_title.setObjectName("helperText")
        card_layout.addWidget(create_title)

        create_grid = QGridLayout()
        create_grid.setHorizontalSpacing(10)
        create_grid.setVerticalSpacing(8)

        self.input_new_username = QLineEdit()
        self.input_new_username.setPlaceholderText("用户名，如 new_admin")
        self.input_new_real_name = QLineEdit()
        self.input_new_real_name.setPlaceholderText("姓名")
        self.input_new_password = QLineEdit()
        self.input_new_password.setPlaceholderText("初始密码（至少6位）")
        self.input_new_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_new_role = QComboBox()
        self.input_new_role.addItem("管理员", 1)
        self.input_new_role.addItem("教师", 2)
        self.input_new_role.addItem("学生", 3)
        self.label_new_dept = QLabel("院系")
        self.input_new_dept = QComboBox()
        self.label_new_major = QLabel("专业")
        self.input_new_major = QComboBox()

        create_grid.addWidget(QLabel("用户名"), 0, 0)
        create_grid.addWidget(self.input_new_username, 0, 1)
        create_grid.addWidget(QLabel("姓名"), 0, 2)
        create_grid.addWidget(self.input_new_real_name, 0, 3)
        create_grid.addWidget(QLabel("密码"), 1, 0)
        create_grid.addWidget(self.input_new_password, 1, 1)
        create_grid.addWidget(QLabel("角色"), 1, 2)
        create_grid.addWidget(self.input_new_role, 1, 3)
        create_grid.addWidget(self.label_new_dept, 2, 0)
        create_grid.addWidget(self.input_new_dept, 2, 1)
        create_grid.addWidget(self.label_new_major, 2, 2)
        create_grid.addWidget(self.input_new_major, 2, 3)
        card_layout.addLayout(create_grid)

        form_grid = QGridLayout()
        form_grid.setHorizontalSpacing(10)
        form_grid.setVerticalSpacing(8)

        self.input_user_id = QLineEdit()
        self.input_user_id.setReadOnly(True)
        self.input_username = QLineEdit()
        self.input_username.setReadOnly(True)
        self.input_real_name = QLineEdit()
        self.input_role = QComboBox()
        self.input_role.addItem("管理员", 1)
        self.input_role.addItem("教师", 2)
        self.input_role.addItem("学生", 3)
        self.label_dept = QLabel("院系")
        self.input_dept = QComboBox()
        self.label_major = QLabel("专业")
        self.input_major = QComboBox()

        form_grid.addWidget(QLabel("用户ID"), 0, 0)
        form_grid.addWidget(self.input_user_id, 0, 1)
        form_grid.addWidget(QLabel("用户名"), 0, 2)
        form_grid.addWidget(self.input_username, 0, 3)
        form_grid.addWidget(QLabel("姓名"), 1, 0)
        form_grid.addWidget(self.input_real_name, 1, 1)
        form_grid.addWidget(QLabel("角色"), 1, 2)
        form_grid.addWidget(self.input_role, 1, 3)
        form_grid.addWidget(self.label_dept, 2, 0)
        form_grid.addWidget(self.input_dept, 2, 1)
        form_grid.addWidget(self.label_major, 2, 2)
        form_grid.addWidget(self.input_major, 2, 3)

        card_layout.addLayout(form_grid)

        # === 组1：创建/导入 ===
        lbl_group1 = QLabel("新增账户 / 导入")
        lbl_group1.setObjectName("helperText")
        card_layout.addWidget(lbl_group1)
        group1_layout = QHBoxLayout()
        group1_layout.setSpacing(10)
        self.btn_create_user = QPushButton("添加账户")
        self.btn_create_user.setObjectName("primaryButton")
        self.btn_create_user.clicked.connect(self.create_user)
        self.btn_import = QPushButton("批量导入用户")
        self.btn_import.setObjectName("primaryButton")
        self.btn_import.clicked.connect(self._choose_csv)
        group1_layout.addWidget(self.btn_create_user)
        group1_layout.addWidget(self.btn_import)
        group1_layout.addStretch(1)
        card_layout.addLayout(group1_layout)

        # === 组2：编辑/删除 ===
        lbl_group2 = QLabel("编辑操作")
        lbl_group2.setObjectName("helperText")
        card_layout.addWidget(lbl_group2)
        group2_layout = QHBoxLayout()
        group2_layout.setSpacing(10)
        self.btn_update = QPushButton("保存修改")
        self.btn_update.setObjectName("primaryButton")
        self.btn_update.clicked.connect(self.update_selected_user)
        self.btn_soft_delete_selected = QPushButton("软删除选中用户")
        self.btn_soft_delete_selected.setObjectName("dangerButton")
        self.btn_soft_delete_selected.clicked.connect(self.soft_delete_selected_user)
        group2_layout.addWidget(self.btn_update)
        group2_layout.addWidget(self.btn_soft_delete_selected)
        group2_layout.addStretch(1)
        card_layout.addLayout(group2_layout)

        # === 组3：系统/工具 ===
        lbl_group3 = QLabel("系统工具")
        lbl_group3.setObjectName("helperText")
        card_layout.addWidget(lbl_group3)
        group3_layout = QHBoxLayout()
        group3_layout.setSpacing(10)
        self.btn_refresh = QPushButton("刷新用户列表")
        self.btn_refresh.setObjectName("secondaryButton")
        self.btn_refresh.clicked.connect(self.refresh_users)
        self.btn_verify_audit = QPushButton("查看最新审计日志")
        self.btn_verify_audit.setObjectName("secondaryButton")
        self.btn_verify_audit.clicked.connect(self._show_last_audit)
        group3_layout.addWidget(self.btn_refresh)
        group3_layout.addWidget(self.btn_verify_audit)
        group3_layout.addStretch(1)
        card_layout.addLayout(group3_layout)

        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)
        search_layout.addWidget(QLabel("搜索"))
        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("按ID/用户名/姓名/角色搜索")
        self.input_search.textChanged.connect(self._apply_user_filter)
        self.btn_clear_search = QPushButton("清空搜索")
        self.btn_clear_search.setObjectName("secondaryButton")
        self.btn_clear_search.clicked.connect(self.input_search.clear)
        search_layout.addWidget(self.input_search)
        search_layout.addWidget(self.btn_clear_search)
        card_layout.addLayout(search_layout)

        self.user_table = QTableWidget(0, 6)
        self.user_table.setObjectName("dataTable")
        self.user_table.setHorizontalHeaderLabels(["ID", "用户名", "姓名", "角色", "是否删除", "创建时间"])
        header = self.user_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.user_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.user_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.user_table.itemSelectionChanged.connect(self._on_user_selected)
        card_layout.addWidget(self.user_table)

        self.input_new_role.currentIndexChanged.connect(self._on_new_role_changed)
        self.input_new_dept.currentIndexChanged.connect(self._on_new_dept_changed)
        self.input_role.currentIndexChanged.connect(self._on_role_changed)
        self.input_dept.currentIndexChanged.connect(self._on_dept_changed)

        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.status_label.setObjectName("statusLabel")
        card_layout.addWidget(self.status_label)

        layout.addWidget(card)
        layout.addStretch(1)

        self._on_new_role_changed()
        self._on_role_changed()

    @staticmethod
    def _optional_combo_int(combo: QComboBox) -> int | None:
        value = combo.currentData()
        if value in (None, ""):
            return None
        return int(value)

    @staticmethod
    def _set_combo_data(combo: QComboBox, value: int | None) -> None:
        idx = combo.findData(value)
        combo.setCurrentIndex(idx if idx >= 0 else 0)

    def _populate_dept_combo(self, combo: QComboBox, selected_dept_id: int | None) -> None:
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("请选择院系", None)
        for dept in self._depts:
            combo.addItem(str(dept["dept_name"]), int(dept["id"]))
        self._set_combo_data(combo, selected_dept_id)
        combo.blockSignals(False)

    def _populate_major_combo(self, combo: QComboBox, dept_id: int | None, selected_major_id: int | None) -> None:
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("请选择专业", None)
        majors = self._majors_by_dept.get(dept_id, []) if dept_id is not None else []
        for major in majors:
            combo.addItem(str(major["major_name"]), int(major["id"]))
        self._set_combo_data(combo, selected_major_id)
        combo.blockSignals(False)

    def _refresh_new_major_options(self, selected_major_id: int | None = None) -> None:
        dept_id = self._optional_combo_int(self.input_new_dept)
        target_major_id = selected_major_id
        if target_major_id is None:
            target_major_id = self._optional_combo_int(self.input_new_major)
        self._populate_major_combo(self.input_new_major, dept_id, target_major_id)

    def _refresh_edit_major_options(self, selected_major_id: int | None = None) -> None:
        dept_id = self._optional_combo_int(self.input_dept)
        target_major_id = selected_major_id
        if target_major_id is None:
            target_major_id = self._optional_combo_int(self.input_major)
        self._populate_major_combo(self.input_major, dept_id, target_major_id)

    def _on_new_role_changed(self) -> None:
        role_id = int(self.input_new_role.currentData())
        show_dept = role_id in (2, 3)
        show_major = role_id == 3
        self.label_new_dept.setVisible(show_dept)
        self.input_new_dept.setVisible(show_dept)
        self.label_new_major.setVisible(show_major)
        self.input_new_major.setVisible(show_major)
        if not show_dept:
            self._set_combo_data(self.input_new_dept, None)
            self._populate_major_combo(self.input_new_major, None, None)
            return
        if show_major:
            self._refresh_new_major_options()
        else:
            self._populate_major_combo(self.input_new_major, None, None)

    def _on_new_dept_changed(self) -> None:
        if int(self.input_new_role.currentData()) == 3:
            self._refresh_new_major_options(None)

    def _on_role_changed(self) -> None:
        role_id = int(self.input_role.currentData())
        show_dept = role_id in (2, 3)
        show_major = role_id == 3
        self.label_dept.setVisible(show_dept)
        self.input_dept.setVisible(show_dept)
        self.label_major.setVisible(show_major)
        self.input_major.setVisible(show_major)
        if not show_dept:
            self._set_combo_data(self.input_dept, None)
            self._populate_major_combo(self.input_major, None, None)
            return
        if show_major:
            self._refresh_edit_major_options()
        else:
            self._populate_major_combo(self.input_major, None, None)

    def _on_dept_changed(self) -> None:
        if int(self.input_role.currentData()) == 3:
            self._refresh_edit_major_options(None)

    def _load_org_options(self) -> None:
        new_dept_id = self._optional_combo_int(self.input_new_dept)
        new_major_id = self._optional_combo_int(self.input_new_major)
        edit_dept_id = self._optional_combo_int(self.input_dept)
        edit_major_id = self._optional_combo_int(self.input_major)

        self._depts = AdminService.list_depts(include_deleted=False)
        majors = AdminService.list_majors(include_deleted=False)
        self._majors_by_dept = {}
        for major in majors:
            dept_id = int(major["dept_id"])
            self._majors_by_dept.setdefault(dept_id, []).append(major)

        self._populate_dept_combo(self.input_new_dept, new_dept_id)
        self._populate_dept_combo(self.input_dept, edit_dept_id)
        self._refresh_new_major_options(new_major_id)
        self._refresh_edit_major_options(edit_major_id)
        self._on_new_role_changed()
        self._on_role_changed()

    def create_user(self) -> None:
        try:
            role_id = int(self.input_new_role.currentData())
            AdminService.create_user(
                self.input_new_username.text(),
                self.input_new_real_name.text(),
                role_id,
                self.input_new_password.text(),
                self._optional_combo_int(self.input_new_dept),
                self._optional_combo_int(self.input_new_major),
            )
            self.status_label.setText(f"用户 {self.input_new_username.text().strip()} 创建成功")
            QMessageBox.information(self, "成功", "账户创建成功")
            self.input_new_username.clear()
            self.input_new_real_name.clear()
            self.input_new_password.clear()
            self.input_new_role.setCurrentIndex(0)
            self.refresh_users()
        except BusinessError as exc:
            self.status_label.setText(f"创建失败: {exc}")
            QMessageBox.warning(self, "创建失败", str(exc))

    def _choose_csv(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "选择CSV", str(Path.cwd()), "CSV Files (*.csv)")
        if not file_path:
            return
        self.import_users_from_csv(file_path)

    def import_users_from_csv(self, file_path: str) -> None:
        try:
            total = AdminService.import_users_from_csv(file_path)
            self.status_label.setText(f"成功导入 {total} 条用户记录")
            QMessageBox.information(self, "成功", f"导入完成，共{total}条")
            self.refresh_users()
        except BusinessError as exc:
            self.status_label.setText(f"导入失败: {exc}")
            QMessageBox.warning(self, "导入失败", str(exc))
        except Exception as exc:
            self.status_label.setText(f"导入失败: {exc}")
            QMessageBox.critical(self, "导入失败", str(exc))

    def soft_delete_selected_user(self) -> None:
        if self.selected_user_id is None:
            QMessageBox.warning(self, "删除失败", "请先在下方表格中选择一个用户")
            return
        try:
            AdminService.soft_delete_user(self.selected_user_id)
            self.status_label.setText(f"用户 {self.selected_user_id} 已被逻辑删除")
            QMessageBox.information(self, "成功", f"已逻辑删除用户 {self.selected_user_id}")
            self.refresh_users()
        except BusinessError as exc:
            self.status_label.setText(f"删除失败: {exc}")
            QMessageBox.warning(self, "删除失败", str(exc))

    def _clear_selected_user(self) -> None:
        self.selected_user_id = None
        self.input_user_id.clear()
        self.input_username.clear()
        self.input_real_name.clear()
        self.input_role.setCurrentIndex(0)
        self._set_combo_data(self.input_dept, None)
        self._populate_major_combo(self.input_major, None, None)
        self._on_role_changed()

    def _render_users(self, users: list[dict]) -> None:
        self._users_by_id = {int(user["id"]): user for user in users}
        self.user_table.setRowCount(len(users))

        role_map = {1: "管理员", 2: "教师", 3: "学生"}
        for i, u in enumerate(users):
            self.user_table.setItem(i, 0, QTableWidgetItem(str(u["id"])))
            self.user_table.setItem(i, 1, QTableWidgetItem(str(u["username"])))
            self.user_table.setItem(i, 2, QTableWidgetItem(str(u["real_name"])))
            self.user_table.setItem(i, 3, QTableWidgetItem(role_map.get(u["role_id"], str(u["role_id"]))))
            self.user_table.setItem(i, 4, QTableWidgetItem("是" if u["is_deleted"] else "否"))
            self.user_table.setItem(i, 5, QTableWidgetItem(str(u["created_at"])))

    def _apply_user_filter(self) -> None:
        keyword = self.input_search.text().strip().lower()
        role_map = {1: "管理员", 2: "教师", 3: "学生"}

        if not keyword:
            filtered_users = self._all_users
        else:
            filtered_users = [
                u
                for u in self._all_users
                if (
                    keyword in str(u["id"]).lower()
                    or keyword in str(u["username"]).lower()
                    or keyword in str(u["real_name"]).lower()
                    or keyword in role_map.get(u["role_id"], str(u["role_id"])).lower()
                )
            ]

        self._render_users(filtered_users)
        if self.selected_user_id is not None and self.selected_user_id not in self._users_by_id:
            self._clear_selected_user()

        if keyword:
            self.status_label.setText(f"已加载 {len(self._all_users)} 条用户记录，匹配 {len(filtered_users)} 条")
        else:
            self.status_label.setText(f"已加载 {len(filtered_users)} 条用户记录")

    def refresh_users(self) -> None:
        self._load_org_options()
        self._all_users = AdminService.list_users(include_deleted=False)
        self._apply_user_filter()

    def _on_user_selected(self) -> None:
        row = self.user_table.currentRow()
        if row < 0:
            self._clear_selected_user()
            return

        user_id_item = self.user_table.item(row, 0)
        username_item = self.user_table.item(row, 1)
        real_name_item = self.user_table.item(row, 2)
        role_item = self.user_table.item(row, 3)

        if not user_id_item or not username_item or not real_name_item or not role_item:
            return

        self.selected_user_id = int(user_id_item.text())
        self.input_user_id.setText(user_id_item.text())
        self.input_username.setText(username_item.text())
        self.input_real_name.setText(real_name_item.text())

        user_data = self._users_by_id.get(self.selected_user_id)
        if not user_data:
            return

        role_value = int(user_data["role_id"])
        idx = self.input_role.findData(role_value)
        if idx >= 0:
            self.input_role.blockSignals(True)
            self.input_role.setCurrentIndex(idx)
            self.input_role.blockSignals(False)

        self._on_role_changed()

        dept_id = user_data.get("dept_id")
        major_id = user_data.get("major_id")
        normalized_dept_id = int(dept_id) if dept_id is not None else None
        normalized_major_id = int(major_id) if major_id is not None else None

        self.input_dept.blockSignals(True)
        self._set_combo_data(self.input_dept, normalized_dept_id)
        self.input_dept.blockSignals(False)
        self._refresh_edit_major_options(normalized_major_id)

    def update_selected_user(self) -> None:
        if self.selected_user_id is None:
            QMessageBox.warning(self, "修改失败", "请先在下方表格中选择一个用户")
            return

        try:
            AdminService.update_user(
                self.selected_user_id,
                self.input_real_name.text(),
                int(self.input_role.currentData()),
                self._optional_combo_int(self.input_dept),
                self._optional_combo_int(self.input_major),
            )
            self.status_label.setText(f"用户 {self.selected_user_id} 修改成功")
            QMessageBox.information(self, "成功", "用户信息已更新")
            self.refresh_users()
        except BusinessError as exc:
            self.status_label.setText(f"修改失败: {exc}")
            QMessageBox.warning(self, "修改失败", str(exc))

    def _show_last_audit(self) -> None:
        try:
            from core.db_manager import DBManager
            logs = DBManager.exec_query("SELECT action_type, detail, created_at FROM sys_audit_logs ORDER BY id DESC LIMIT 5")
            if not logs:
                QMessageBox.information(self, "审计日志", "暂无日志")
                return
            
            msg = "\n".join([f"[{log['created_at']}] {log['action_type']}: {log['detail']}" for log in logs])
            QMessageBox.information(self, "最近5条审计日志", msg)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法读取日志: {e}")
