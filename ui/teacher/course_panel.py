"""CoursePanel — 教师工作台主界面

布局:
    左侧：授课课程列表 + 归档按钮
    右侧 Tab：
        Tab 0 成绩录入  —— 卷面成绩录入（×0.7）+ 平时分自动合并 = 最终成绩；支持 Excel 导入；提交锁定
        Tab 1 成绩分析  —— matplotlib 柱状图 + 正态曲线 + 统计摘要
        Tab 2 挂科预警  —— 全局不及格学生列表
        Tab 3 平时分管理 —— 签到/作业/章节测验记录 + 完成率 → 自动给出平时分（最高30分）
        Tab 4 历史归档  —— 查询 edu_archives 中本教师的历史成绩
        Tab 5 批量操作  —— 批量调分、成绩统计、批量导出等高级功能
        Tab 6 课程设置  —— 权重配置、及格线设置、成绩公式自定义
"""
from __future__ import annotations

from typing import Optional
import json
import os
from datetime import datetime

from PyQt6.QtCore import Qt, QThread, QDate, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont, QBrush
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QTextEdit,
    QCheckBox,
    QSpinBox,
    QDoubleSpinBox,
    QGroupBox,
    QProgressBar,
    QLineEdit,
    QStyledItemDelegate,
)

from core.constants import score_to_gpa
from core.exceptions import BusinessError, ValidationError
from core.session import Session
from models.analysis_dao import AnalysisDAO
from services.grade_service import GradeService
from services.teacher_service import TeacherService
from utils.exporter import ReportExporter

# matplotlib 可选导入（若未安装则分析 Tab 降级为纯文字）
try:
    import matplotlib
    matplotlib.use("QtAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib import rcParams

    rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    rcParams["axes.unicode_minus"] = False
    _MPL_AVAILABLE = True
except ImportError:
    _MPL_AVAILABLE = False


# ──────────────────────────────────────────────────────────────
# 居中对齐 Delegate（用于可编辑单元格）
# ──────────────────────────────────────────────────────────────
class _CenterDelegate(QStyledItemDelegate):
    """让内联编辑器（QLineEdit）中的文字居中显示。"""

    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)
        if hasattr(editor, "setAlignment"):
            editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return editor


# ──────────────────────────────────────────────────────────────
# 后台工作线程（避免 DB 查询阻塞 UI 主线程）
# ──────────────────────────────────────────────────────────────
class _Worker(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

    def run(self):
        try:
            result = self._fn(*self._args, **self._kwargs)
            self.finished.emit(result)
        except Exception as exc:  # noqa: BLE001
            self.error.emit(str(exc))


# ──────────────────────────────────────────────────────────────
# matplotlib 画布 Widget
# ──────────────────────────────────────────────────────────────
class _ChartCanvas(QWidget):
    """嵌入 matplotlib 图表的容器，不可用时显示提示文字。"""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if _MPL_AVAILABLE:
            self._fig = Figure(figsize=(10, 4), dpi=96)
            self._canvas = FigureCanvas(self._fig)
            layout.addWidget(self._canvas)
        else:
            lbl = QLabel("matplotlib 未安装，无法显示图表。\n请运行: pip install matplotlib")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: gray; font-size: 13px;")
            layout.addWidget(lbl)

    def plot_distribution(self, dist: dict, title: str = "") -> None:
        if not _MPL_AVAILABLE or not dist:
            return

        self._fig.clf()
        axes = self._fig.subplots(1, 2)

        segments = ["<60", "60-69", "70-79", "80-89", "90-100"]
        counts = [
            int(dist.get("below_60", 0) or 0),
            int(dist.get("cnt_60_69", 0) or 0),
            int(dist.get("cnt_70_79", 0) or 0),
            int(dist.get("cnt_80_89", 0) or 0),
            int(dist.get("cnt_90_100", 0) or 0),
        ]
        colors = ["#E74C3C", "#E67E22", "#F1C40F", "#2ECC71", "#3498DB"]

        ax1 = axes[0]
        bars = ax1.bar(segments, counts, color=colors, edgecolor="white")
        ax1.set_title("成绩分段分布", fontsize=11)
        ax1.set_xlabel("分数段")
        ax1.set_ylabel("人数")
        ax1.set_ylim(0, max(counts + [1]) * 1.35)
        for bar, cnt in zip(bars, counts):
            if cnt > 0:
                ax1.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.05,
                    str(cnt),
                    ha="center", va="bottom", fontweight="bold", fontsize=9,
                )

        ax2 = axes[1]
        avg = float(dist.get("avg_score") or 0)
        std = float(dist.get("std_dev") or 0)
        total = int(dist.get("total") or 0)
        if avg > 0 and std > 0 and total > 0:
            try:
                import numpy as np
                x = np.linspace(max(0, avg - 4 * std), min(100, avg + 4 * std), 300)
                y = np.exp(-0.5 * ((x - avg) / std) ** 2) / (std * np.sqrt(2 * np.pi))
                y_scaled = y * total * 10
                ax2.plot(x, y_scaled, "#3498DB", linewidth=2, label="正态拟合")
                ax2.fill_between(x, y_scaled, alpha=0.12, color="#3498DB")
                ax2.axvline(avg, color="#E74C3C", linestyle="--", linewidth=1.2,
                            label=f"均分 {avg:.1f}")
                ax2.legend(fontsize=8)
            except ImportError:
                ax2.text(0.5, 0.5, "需要 numpy 支持正态拟合",
                         ha="center", va="center", transform=ax2.transAxes, color="gray")
        else:
            ax2.text(0.5, 0.5, "数据不足，无法拟合",
                     ha="center", va="center", transform=ax2.transAxes,
                     fontsize=11, color="gray")
        ax2.set_title("成绩正态分布拟合", fontsize=11)
        ax2.set_xlabel("分数")
        ax2.set_ylabel("频率（估计）")

        if title:
            self._fig.suptitle(title, fontsize=12, fontweight="bold")
        self._fig.tight_layout()
        self._canvas.draw()

    def clear_plot(self) -> None:
        if _MPL_AVAILABLE:
            self._fig.clf()
            self._canvas.draw()


# ──────────────────────────────────────────────────────────────
# 平时分汇总弹窗
# ──────────────────────────────────────────────────────────────
class _DailySummaryDialog(QDialog):
    """显示当前班级所有学生的平时分汇总。"""

    def __init__(self, teaching_id: int, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("平时分汇总")
        self.resize(620, 400)

        layout = QVBoxLayout(self)

        title = QLabel("平时分计算规则：30 × (已完成记录数 / 总记录数)")
        title.setStyleSheet("color: #7f8c8d; font-size: 12px; padding: 4px;")
        layout.addWidget(title)

        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(
            ["学号", "姓名", "总记录数", "已完成", "完成率(%)", "平时分(30分制)"]
        )
        hdr = table.horizontalHeader()
        if hdr:
            hdr.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)  # type: ignore[union-attr]
        layout.addWidget(table)

        try:
            rows = AnalysisDAO().get_daily_score_summary(teaching_id)
        except Exception as exc:
            QMessageBox.warning(self, "加载失败", str(exc))
            rows = []

        table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            vals = [
                r.get("username", ""),
                r.get("real_name", ""),
                str(r.get("total_records", 0)),
                str(r.get("completed_records", 0)),
                f"{r.get('completion_rate', 0):.1f}",
                f"{r.get('daily_score', 0):.2f}",
            ]
            for j, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if j == 5:
                    score_val = float(r.get("daily_score", 0) or 0)
                    if score_val >= 25:
                        item.setForeground(QBrush(QColor("#27AE60")))
                    elif score_val < 15:
                        item.setForeground(QBrush(QColor("#E74C3C")))
                table.setItem(i, j, item)

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn_box.rejected.connect(self.accept)
        layout.addWidget(btn_box)


# ──────────────────────────────────────────────────────────────
# 批量调分对话框
# ──────────────────────────────────────────────────────────────
class _BatchAdjustDialog(QDialog):
    """批量调整成绩：加分、减分、按比例缩放等。"""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("批量调分")
        self.resize(450, 280)

        layout = QVBoxLayout(self)

        info = QLabel("选择调分方式，将应用到所有已录入卷面成绩的学生。")
        info.setStyleSheet("color: #555; font-size: 12px; padding: 6px;")
        layout.addWidget(info)

        self.radio_group = QGroupBox("调分方式")
        radio_layout = QVBoxLayout(self.radio_group)

        self.cmb_method = QComboBox()
        self.cmb_method.addItem("统一加分", "add")
        self.cmb_method.addItem("统一减分", "subtract")
        self.cmb_method.addItem("按比例缩放", "scale")
        self.cmb_method.addItem("开平方×10", "sqrt")
        self.cmb_method.currentIndexChanged.connect(self._on_method_changed)
        radio_layout.addWidget(self.cmb_method)

        layout.addWidget(self.radio_group)

        param_group = QGroupBox("参数设置")
        param_layout = QVBoxLayout(param_group)

        self.lbl_param = QLabel("调整值：")
        param_layout.addWidget(self.lbl_param)

        self.spin_value = QDoubleSpinBox()
        self.spin_value.setRange(-100.0, 100.0)
        self.spin_value.setValue(5.0)
        self.spin_value.setSingleStep(0.5)
        self.spin_value.setDecimals(2)
        param_layout.addWidget(self.spin_value)

        layout.addWidget(param_group)

        self.chk_cap = QCheckBox("调整后自动限制在 [0, 100] 范围内")
        self.chk_cap.setChecked(True)
        layout.addWidget(self.chk_cap)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

        self._on_method_changed()

    def _on_method_changed(self) -> None:
        method = self.cmb_method.currentData()
        if method == "add":
            self.lbl_param.setText("加分值：")
            self.spin_value.setRange(0.0, 100.0)
            self.spin_value.setValue(5.0)
        elif method == "subtract":
            self.lbl_param.setText("减分值：")
            self.spin_value.setRange(0.0, 100.0)
            self.spin_value.setValue(5.0)
        elif method == "scale":
            self.lbl_param.setText("缩放系数（如 1.1 表示乘以 1.1）：")
            self.spin_value.setRange(0.1, 2.0)
            self.spin_value.setValue(1.1)
        elif method == "sqrt":
            self.lbl_param.setText("开平方×10（无需参数）")
            self.spin_value.setEnabled(False)
            return
        self.spin_value.setEnabled(True)

    def get_adjustment_params(self) -> dict:
        return {
            "method": self.cmb_method.currentData(),
            "value": self.spin_value.value(),
            "cap": self.chk_cap.isChecked(),
        }


# ──────────────────────────────────────────────────────────────
# 成绩统计详情对话框
# ──────────────────────────────────────────────────────────────
class _DetailedStatsDialog(QDialog):
    """显示更详细的成绩统计信息，包括四分位数、偏度、峰度等。"""

    def __init__(self, teaching_id: int, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("详细统计信息")
        self.resize(500, 450)

        layout = QVBoxLayout(self)

        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet("font-family: 'Consolas', 'Courier New'; font-size: 11px;")
        layout.addWidget(self.text_area)

        try:
            stats = AnalysisDAO().get_teaching_stats(teaching_id)
            self._display_stats(stats)
        except Exception as exc:
            self.text_area.setText(f"加载统计数据失败：{exc}")

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn_box.rejected.connect(self.accept)
        layout.addWidget(btn_box)

    def _display_stats(self, stats: dict) -> None:
        lines = [
            "=" * 50,
            "详细统计报告",
            "=" * 50,
            "",
            f"参与人数：{stats.get('student_count', 0)} 人",
            f"平均分：{stats.get('avg_score', 0):.2f}",
            f"最高分：{stats.get('max_score', 0):.2f}",
            f"最低分：{stats.get('min_score', 0):.2f}",
            f"标准差：{stats.get('std_dev', 0):.2f}",
            f"及格率：{stats.get('pass_rate', 0):.2f}%",
            "",
            "分数段分布：",
            f"  90-100：{stats.get('cnt_90_100', 0)} 人",
            f"  80-89： {stats.get('cnt_80_89', 0)} 人",
            f"  70-79： {stats.get('cnt_70_79', 0)} 人",
            f"  60-69： {stats.get('cnt_60_69', 0)} 人",
            f"  <60：  {stats.get('below_60', 0)} 人",
            "",
            "等级分布：",
            f"  A+：{stats.get('grade_A_plus', 0)} 人",
            f"  A： {stats.get('grade_A', 0)} 人",
            f"  B+：{stats.get('grade_B_plus', 0)} 人",
            f"  B： {stats.get('grade_B', 0)} 人",
            f"  C+：{stats.get('grade_C_plus', 0)} 人",
            f"  C： {stats.get('grade_C', 0)} 人",
            f"  D： {stats.get('grade_D', 0)} 人",
            f"  F： {stats.get('grade_F', 0)} 人",
            "",
            "=" * 50,
        ]
        self.text_area.setText("\n".join(lines))


# ──────────────────────────────────────────────────────────────
# 课程权重配置对话框
# ──────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────
# 成绩筛选对话框
# ──────────────────────────────────────────────────────────────
class _GradeFilterDialog(QDialog):
    """按条件筛选成绩：分数范围、等级、是否通过等。"""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("成绩筛选")
        self.resize(420, 300)

        layout = QVBoxLayout(self)

        info = QLabel("设置筛选条件，点击确定后在成绩表中高亮显示符合条件的学生。")
        info.setStyleSheet("color: #555; font-size: 12px; padding: 6px;")
        layout.addWidget(info)

        form_layout = QGridLayout()

        form_layout.addWidget(QLabel("最终成绩范围："), 0, 0)
        range_layout = QHBoxLayout()
        self.spin_min = QDoubleSpinBox()
        self.spin_min.setRange(0.0, 100.0)
        self.spin_min.setValue(0.0)
        range_layout.addWidget(self.spin_min)
        range_layout.addWidget(QLabel("至"))
        self.spin_max = QDoubleSpinBox()
        self.spin_max.setRange(0.0, 100.0)
        self.spin_max.setValue(100.0)
        range_layout.addWidget(self.spin_max)
        form_layout.addLayout(range_layout, 0, 1)

        form_layout.addWidget(QLabel("等级筛选："), 1, 0)
        self.cmb_letter = QComboBox()
        self.cmb_letter.addItem("全部", "")
        for letter in ["A+", "A", "B+", "B", "C+", "C", "D", "F"]:
            self.cmb_letter.addItem(letter, letter)
        form_layout.addWidget(self.cmb_letter, 1, 1)

        form_layout.addWidget(QLabel("通过状态："), 2, 0)
        self.cmb_passed = QComboBox()
        self.cmb_passed.addItem("全部", "")
        self.cmb_passed.addItem("仅通过", "passed")
        self.cmb_passed.addItem("仅不通过", "failed")
        form_layout.addWidget(self.cmb_passed, 2, 1)

        layout.addLayout(form_layout)

        layout.addStretch()

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def get_filter_params(self) -> dict:
        return {
            "min_score": self.spin_min.value(),
            "max_score": self.spin_max.value(),
            "letter": self.cmb_letter.currentData(),
            "passed": self.cmb_passed.currentData(),
        }


# ──────────────────────────────────────────────────────────────
# CoursePanel 主体
# ──────────────────────────────────────────────────────────────
class CoursePanel(QWidget):
    """教师工作台顶层 Widget，注册到 MainWindow 页面栈。"""

    _COL_USERNAME   = 0
    _COL_REALNAME   = 1
    _COL_DAILY      = 2
    _COL_EXAM       = 3
    _COL_FINAL      = 4
    _COL_LETTER     = 5
    _COL_GPA        = 6
    _COL_PASSED     = 7

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._grade_svc     = GradeService()
        self._teacher_svc   = TeacherService()
        self._analysis_dao  = AnalysisDAO()
        self._exporter      = ReportExporter()

        self._current_teaching_id: Optional[int] = None
        self._teachings: list[dict] = []
        self._is_submitted: bool = False
        self._daily_score_cache: dict[int, float] = {}

        self._course_settings: dict[int, dict] = {}

        self._auto_save_timer = QTimer(self)
        self._auto_save_timer.timeout.connect(self._auto_save_grades)
        self._auto_save_enabled = False

        self._build_ui()
        self._load_my_courses()

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_left_panel())
        splitter.addWidget(self._build_right_panel())
        splitter.setSizes([300, 900])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setHandleWidth(6)

        root.addWidget(splitter)

    def _build_left_panel(self) -> QWidget:
        from PyQt6.QtWidgets import QFrame, QSizePolicy
        panel = QWidget()
        panel.setObjectName("leftPanel")
        panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QLabel("我的课程")
        title.setFont(QFont("WenQuanYi Micro Hei", 11, QFont.Weight.Bold))
        layout.addWidget(title)

        self.course_list = QListWidget()
        self.course_list.setObjectName("courseList")
        self.course_list.setSpacing(2)
        self.course_list.currentRowChanged.connect(self._on_course_selected)
        layout.addWidget(self.course_list, stretch=2)

        self.btn_refresh = QPushButton("刷新课程列表")
        self.btn_refresh.clicked.connect(self._load_my_courses)
        layout.addWidget(self.btn_refresh)

        self.btn_archive = QPushButton("归档指定学期成绩")
        self.btn_archive.setObjectName("dangerButton")
        self.btn_archive.clicked.connect(self._archive_grades)
        layout.addWidget(self.btn_archive)

        stats_label = QLabel("快速统计")
        stats_label.setFont(QFont("WenQuanYi Micro Hei", 10, QFont.Weight.Bold))
        stats_label.setStyleSheet("margin-top: 8px;")
        layout.addWidget(stats_label)

        self.lbl_quick_stats = QLabel("选择课程后显示")
        self.lbl_quick_stats.setStyleSheet(
            "background-color: #ECF0F1; padding: 8px; border-radius: 4px; "
            "font-size: 10px; color: #555;"
        )
        self.lbl_quick_stats.setWordWrap(True)
        layout.addWidget(self.lbl_quick_stats)

        # ── 分隔线 ──
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setStyleSheet("color: #BDC3C7; margin-top: 4px; margin-bottom: 4px;")
        layout.addWidget(sep)

        # ── 选课名单区域 ──
        enroll_title_row = QHBoxLayout()
        enroll_label = QLabel("选课名单")
        enroll_label.setFont(QFont("WenQuanYi Micro Hei", 10, QFont.Weight.Bold))
        enroll_title_row.addWidget(enroll_label)
        enroll_title_row.addStretch()
        btn_refresh_enroll = QPushButton("↺")
        btn_refresh_enroll.setFixedSize(24, 24)
        btn_refresh_enroll.setToolTip("刷新选课名单")
        btn_refresh_enroll.clicked.connect(self._load_enrollment_panel)
        enroll_title_row.addWidget(btn_refresh_enroll)
        layout.addLayout(enroll_title_row)

        self.lbl_enrollment_summary = QLabel("—")
        self.lbl_enrollment_summary.setStyleSheet(
            "background-color: #EBF5FB; color: #1A5276; "
            "font-size: 10px; padding: 4px 8px; border-radius: 4px;"
        )
        self.lbl_enrollment_summary.setWordWrap(True)
        layout.addWidget(self.lbl_enrollment_summary)

        self.list_enrolled_left = QListWidget()
        self.list_enrolled_left.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.list_enrolled_left.setStyleSheet("font-size: 11px;")
        layout.addWidget(self.list_enrolled_left, stretch=3)

        return panel

    def _build_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        info_row = QHBoxLayout()
        self.lbl_course_info = QLabel("← 请在左侧选择课程")
        self.lbl_course_info.setFont(QFont("WenQuanYi Micro Hei", 10))
        info_row.addWidget(self.lbl_course_info)
        info_row.addStretch()
        layout.addLayout(info_row)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_grade_tab(),    "成绩录入")
        self.tabs.addTab(self._build_analysis_tab(), "成绩分析")
        self.tabs.addTab(self._build_warning_tab(),  "挂科预警")
        self.tabs.addTab(self._build_daily_tab(),    "平时分管理")
        self.tabs.addTab(self._build_archive_tab(),  "历史归档")
        self.tabs.addTab(self._build_batch_tab(),    "批量操作")
        self.tabs.addTab(self._build_settings_tab(), "课程设置")
        self.tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tabs)

        return panel

    def _build_grade_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self.lbl_locked = QLabel("🔒 成绩已提交锁定，不可再修改")
        self.lbl_locked.setStyleSheet(
            "background-color: #FDEDEC; color: #C0392B; "
            "font-weight: bold; padding: 6px 12px; border-radius: 4px;"
        )
        self.lbl_locked.setVisible(False)
        layout.addWidget(self.lbl_locked)

        btn_row1 = QHBoxLayout()

        self.btn_import_daily_quick = QPushButton("⬇️ 一键导入平时分")
        self.btn_import_daily_quick.setEnabled(False)
        self.btn_import_daily_quick.setStyleSheet(
            "QPushButton { background-color: #9B59B6; color: white; "
            "border-radius: 4px; padding: 6px 14px; font-weight: bold; } "
            "QPushButton:hover { background-color: #A569BD; }"
        )
        self.btn_import_daily_quick.setToolTip("从数据库自动读取平时分并填充到平时分列")
        self.btn_import_daily_quick.clicked.connect(self._quick_import_daily)

        self.btn_save_grades = QPushButton("保存成绩")
        self.btn_save_grades.setEnabled(False)
        self.btn_save_grades.clicked.connect(self._save_grades)

        self.btn_export_excel = QPushButton("导出 Excel")
        self.btn_export_excel.setEnabled(False)
        self.btn_export_excel.clicked.connect(self._export_excel)

        self.btn_import_excel = QPushButton("导入 Excel（卷面成绩）")
        self.btn_import_excel.setEnabled(False)
        self.btn_import_excel.setToolTip("Excel 须含'学号'和'卷面成绩'两列")
        self.btn_import_excel.clicked.connect(self._import_grades_excel)

        self.btn_submit_grades = QPushButton("提交成绩（锁定）")
        self.btn_submit_grades.setEnabled(False)
        self.btn_submit_grades.setObjectName("dangerButton")
        self.btn_submit_grades.setToolTip("提交后成绩将被锁定，不可再修改")
        self.btn_submit_grades.clicked.connect(self._submit_grades)

        btn_row1.addWidget(self.btn_import_daily_quick)
        btn_row1.addWidget(self.btn_save_grades)
        btn_row1.addWidget(self.btn_export_excel)
        btn_row1.addWidget(self.btn_import_excel)
        btn_row1.addWidget(self.btn_submit_grades)
        btn_row1.addStretch()
        layout.addLayout(btn_row1)

        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("快速搜索："))
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("输入学号或姓名...")
        self.txt_search.setFixedWidth(200)
        self.txt_search.textChanged.connect(self._filter_grade_table)
        search_row.addWidget(self.txt_search)
        search_row.addStretch()
        layout.addLayout(search_row)

        self.grade_table = QTableWidget()
        self.grade_table.setColumnCount(8)
        self.grade_table.setHorizontalHeaderLabels([
            "学号", "姓名",
            "平时分(30)", "卷面成绩",
            "最终成绩", "等级", "绩点", "是否通过",
        ])
        hdr = self.grade_table.horizontalHeader()
        if hdr is not None:
            hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            for c in range(2, 8):
                hdr.setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)

        vhdr = self.grade_table.verticalHeader()
        if vhdr is not None:
            vhdr.setVisible(False)
        self.grade_table.setAlternatingRowColors(True)
        self.grade_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.grade_table.itemChanged.connect(self._on_grade_cell_changed)
        layout.addWidget(self.grade_table)

        formula_lbl = QLabel(
            "💡 最终成绩 = 卷面成绩 × 0.7 + 平时分 × 1.0  |  "
            "平时分可手动编辑（0-30分）或点击'一键导入平时分'自动填充"
        )
        formula_lbl.setStyleSheet("color: #555; font-size: 11px; padding: 6px; background-color: #E8F8F5; border-radius: 4px;")
        layout.addWidget(formula_lbl)

        return widget

    def _build_analysis_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        stats_frame = QWidget()
        stats_grid = QGridLayout(stats_frame)
        stats_grid.setContentsMargins(0, 0, 0, 0)
        stats_grid.setSpacing(12)

        label_style = "font-weight: bold; color: #555;"
        value_style = "font-size: 15px; font-weight: bold; color: #2C3E50;"

        stat_defs = [
            ("平均分", "lbl_avg"),
            ("最高分", "lbl_max"),
            ("最低分", "lbl_min"),
            ("标准差", "lbl_std"),
            ("及格率", "lbl_pass"),
            ("参与人数", "lbl_count"),
        ]
        for col, (text, attr) in enumerate(stat_defs):
            card = QWidget()
            card.setObjectName("statCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(8, 6, 8, 6)
            card_layout.setSpacing(2)

            title_lbl = QLabel(text)
            title_lbl.setStyleSheet(label_style)
            title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            value_lbl = QLabel("—")
            value_lbl.setStyleSheet(value_style)
            value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            setattr(self, attr, value_lbl)

            card_layout.addWidget(title_lbl)
            card_layout.addWidget(value_lbl)
            stats_grid.addWidget(card, 0, col)

        layout.addWidget(stats_frame)

        self.chart_canvas = _ChartCanvas()
        layout.addWidget(self.chart_canvas, 1)

        btn_row = QHBoxLayout()
        btn_refresh_analysis = QPushButton("刷新分析")
        btn_refresh_analysis.setToolTip("重新从成绩录入表计算并刷新图表（调分后使用）")
        btn_refresh_analysis.clicked.connect(self._load_analysis)

        self.btn_export_report = QPushButton("导出分析报告 (PDF/PNG)")
        self.btn_export_report.setEnabled(False)
        self.btn_export_report.clicked.connect(self._export_report)

        self.btn_detailed_stats = QPushButton("查看详细统计")
        self.btn_detailed_stats.setEnabled(False)
        self.btn_detailed_stats.clicked.connect(self._show_detailed_stats)

        btn_row.addWidget(btn_refresh_analysis)
        btn_row.addWidget(self.btn_export_report)
        btn_row.addWidget(self.btn_detailed_stats)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        return widget

    def _build_warning_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        btn_row = QHBoxLayout()
        self.btn_refresh_warning = QPushButton("刷新预警数据")
        self.btn_refresh_warning.clicked.connect(self._load_warning)

        self.btn_export_warning = QPushButton("导出预警名单")
        self.btn_export_warning.clicked.connect(self._export_warning_list)

        btn_row.addWidget(self.btn_refresh_warning)
        btn_row.addWidget(self.btn_export_warning)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.warning_table = QTableWidget()
        self.warning_table.setColumnCount(6)
        self.warning_table.setHorizontalHeaderLabels(
            ["学号", "姓名", "课程", "学期", "成绩", "等级"]
        )
        hdr = self.warning_table.horizontalHeader()
        if hdr is not None:
            for col in range(6):
                hdr.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
        vhdr = self.warning_table.verticalHeader()
        if vhdr is not None:
            vhdr.setVisible(False)
        self.warning_table.setAlternatingRowColors(True)
        self.warning_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.warning_table)

        return widget

    def _build_daily_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        info = QLabel("平时分自动计算与导入")
        info.setStyleSheet("color: #555; font-size: 13px; font-weight: bold; padding: 6px;")
        layout.addWidget(info)

        hint = QLabel(
            "系统会根据数据库中的平时记录（签到、作业、章节测验）自动计算每位学生的平时分。\n"
            "平时分计算公式：30 × (已完成记录数 / 总记录数)"
        )
        hint.setStyleSheet("color: #7f8c8d; font-size: 11px; padding: 8px; background-color: #ECF0F1; border-radius: 4px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.daily_summary_table = QTableWidget()
        self.daily_summary_table.setColumnCount(6)
        self.daily_summary_table.setHorizontalHeaderLabels(
            ["学号", "姓名", "总记录数", "已完成✏️", "完成率(%)", "平时分(30分制)"]
        )
        hdr = self.daily_summary_table.horizontalHeader()
        if hdr:
            hdr.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            hdr.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.daily_summary_table.setAlternatingRowColors(True)
        self.daily_summary_table.setItemDelegateForColumn(3, _CenterDelegate(self))
        self.daily_summary_table.itemChanged.connect(self._on_daily_completed_changed)
        vhdr = self.daily_summary_table.verticalHeader()
        if vhdr:
            vhdr.setVisible(False)
        layout.addWidget(self.daily_summary_table)

        btn_row = QHBoxLayout()
        
        btn_load_summary = QPushButton("🔄 刷新平时分汇总")
        btn_load_summary.setStyleSheet(
            "QPushButton { background-color: #3498DB; color: white; "
            "border-radius: 4px; padding: 8px 16px; font-size: 13px; font-weight: bold; } "
            "QPushButton:hover { background-color: #5DADE2; }"
        )
        btn_load_summary.clicked.connect(self._load_daily_summary_table)

        btn_save_daily_changes = QPushButton("💾 保存平时分修改")
        btn_save_daily_changes.setStyleSheet(
            "QPushButton { background-color: #E67E22; color: white; "
            "border-radius: 4px; padding: 8px 16px; font-size: 13px; font-weight: bold; } "
            "QPushButton:hover { background-color: #F39C12; }"
        )
        btn_save_daily_changes.setToolTip("保存您对'已完成'列的修改（可选，不保存也能导入）")
        btn_save_daily_changes.clicked.connect(self._save_daily_changes)

        btn_import_daily = QPushButton("⬇️ 一键导入平时分到成绩表")
        btn_import_daily.setStyleSheet(
            "QPushButton { background-color: #27ae60; color: white; "
            "border-radius: 4px; padding: 8px 16px; font-size: 13px; font-weight: bold; } "
            "QPushButton:hover { background-color: #2ecc71; }"
        )
        btn_import_daily.setToolTip("将上表中的平时分自动导入到成绩录入表，并重新计算最终成绩")
        btn_import_daily.clicked.connect(self._import_daily_scores_to_grades)

        btn_row.addWidget(btn_load_summary)
        btn_row.addWidget(btn_save_daily_changes)
        btn_row.addWidget(btn_import_daily)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        explanation = QLabel(
            "💡 使用说明：\n\n"
            "1️⃣ 点击'刷新平时分汇总'加载当前课程的平时分数据\n"
            "2️⃣ 您可以直接修改'已完成'列（黄色背景）的数值，系统会自动重新计算完成率和平时分\n"
            "3️⃣ 点击'一键导入平时分到成绩表'将平时分批量导入到成绩录入页面\n"
            "4️⃣ 导入后切换到'成绩录入'标签页，可继续手动微调平时分（0-30分）\n"
            "5️⃣ 最后在'成绩录入'页面点击'保存成绩'完成录入\n\n"
            "📌 注意：'总记录数'为只读，由系统根据数据库平时记录自动统计"
        )
        explanation.setStyleSheet(
            "color: #555; font-size: 11px; padding: 10px; "
            "background-color: #FFF9E6; border-left: 4px solid #F39C12; border-radius: 4px;"
        )
        explanation.setWordWrap(True)
        layout.addWidget(explanation)

        return widget

    def _build_archive_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("历史学期："))
        self._cmb_archive_semester = QComboBox()
        self._cmb_archive_semester.setFixedWidth(160)
        ctrl.addWidget(self._cmb_archive_semester)

        btn_query_archive = QPushButton("查询归档成绩")
        btn_query_archive.setFixedWidth(110)
        btn_query_archive.clicked.connect(self._load_archive_data)
        ctrl.addWidget(btn_query_archive)
        ctrl.addStretch()
        layout.addLayout(ctrl)

        hint = QLabel("显示本教师在所选学期已归档的所有成绩记录（来自 edu_archives）。")
        hint.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        layout.addWidget(hint)

        self.archive_table = QTableWidget()
        self.archive_table.setColumnCount(8)
        self.archive_table.setHorizontalHeaderLabels(
            ["学号", "姓名", "课程", "学期", "最终成绩", "等级", "绩点", "归档时间"]
        )
        hdr = self.archive_table.horizontalHeader()
        if hdr is not None:
            hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
            for c in range(3, 8):
                hdr.setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        vhdr = self.archive_table.verticalHeader()
        if vhdr is not None:
            vhdr.setVisible(False)
        self.archive_table.setAlternatingRowColors(True)
        self.archive_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.archive_table)

        return widget

    def _build_batch_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        info = QLabel("批量操作工具集：调分、筛选、统计、导出等高级功能")
        info.setStyleSheet("color: #555; font-size: 12px; font-weight: bold; padding: 6px;")
        layout.addWidget(info)

        group_adjust = QGroupBox("批量调分")
        adjust_layout = QVBoxLayout(group_adjust)

        btn_batch_adjust = QPushButton("批量调整卷面成绩")
        btn_batch_adjust.setToolTip("对所有学生的卷面成绩进行统一调整（加分、减分、缩放等）")
        btn_batch_adjust.clicked.connect(self._batch_adjust_grades)
        adjust_layout.addWidget(btn_batch_adjust)

        btn_batch_curve = QPushButton("自动调分（智能曲线）")
        btn_batch_curve.setToolTip("根据统计数据自动调整成绩，使分布更合理")
        btn_batch_curve.clicked.connect(self._auto_curve_grades)
        adjust_layout.addWidget(btn_batch_curve)

        layout.addWidget(group_adjust)

        group_filter = QGroupBox("成绩筛选")
        filter_layout = QVBoxLayout(group_filter)

        btn_filter = QPushButton("按条件筛选成绩")
        btn_filter.setToolTip("按分数范围、等级、通过状态筛选，结果以列表弹窗展示")
        btn_filter.clicked.connect(self._filter_grades)
        filter_layout.addWidget(btn_filter)

        layout.addWidget(group_filter)

        group_export = QGroupBox("批量导出")
        export_layout = QVBoxLayout(group_export)

        btn_export_all = QPushButton("导出所有课程成绩（批量）")
        btn_export_all.setToolTip("将本学期所有课程的成绩导出为多个 Excel 文件")
        btn_export_all.clicked.connect(self._batch_export_all_courses)
        export_layout.addWidget(btn_export_all)

        btn_export_summary = QPushButton("导出学期汇总报告")
        btn_export_summary.setToolTip("生成本学期所有课程的统计汇总报告")
        btn_export_summary.clicked.connect(self._export_semester_summary)
        export_layout.addWidget(btn_export_summary)

        layout.addWidget(group_export)

        group_stats = QGroupBox("高级统计")
        stats_layout = QVBoxLayout(group_stats)

        btn_compare = QPushButton("课程成绩对比分析")
        btn_compare.setToolTip("对比多个课程的成绩分布和统计指标")
        btn_compare.clicked.connect(self._compare_courses)
        stats_layout.addWidget(btn_compare)

        btn_trend = QPushButton("历史趋势分析")
        btn_trend.setToolTip("分析同一课程在不同学期的成绩变化趋势")
        btn_trend.clicked.connect(self._analyze_trend)
        stats_layout.addWidget(btn_trend)

        layout.addWidget(group_stats)

        layout.addStretch()

        return widget

    def _build_settings_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        info = QLabel("课程设置：自动保存、数据备份等")
        info.setStyleSheet("color: #555; font-size: 12px; font-weight: bold; padding: 6px;")
        layout.addWidget(info)

        group_auto = QGroupBox("自动保存")
        auto_layout = QVBoxLayout(group_auto)

        self.chk_auto_save = QCheckBox("启用自动保存（每 2 分钟）")
        self.chk_auto_save.stateChanged.connect(self._toggle_auto_save)
        auto_layout.addWidget(self.chk_auto_save)

        self.lbl_last_save = QLabel("最后保存时间：未保存")
        self.lbl_last_save.setStyleSheet("color: #7f8c8d; font-size: 10px; padding: 4px;")
        auto_layout.addWidget(self.lbl_last_save)

        layout.addWidget(group_auto)

        group_backup = QGroupBox("数据备份")
        backup_layout = QVBoxLayout(group_backup)

        btn_backup = QPushButton("备份当前课程成绩")
        btn_backup.setToolTip("将当前课程的所有成绩数据备份为 JSON 文件")
        btn_backup.clicked.connect(self._backup_course_data)
        backup_layout.addWidget(btn_backup)

        btn_restore = QPushButton("从备份恢复成绩")
        btn_restore.setToolTip("从之前的备份文件恢复成绩数据")
        btn_restore.clicked.connect(self._restore_course_data)
        backup_layout.addWidget(btn_restore)

        layout.addWidget(group_backup)

        layout.addStretch()

        return widget

    def _load_my_courses(self) -> None:
        if Session.current_user is None:
            return
        try:
            all_teachings = self._grade_svc.get_my_teachings(Session.current_user.id)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "加载失败", f"获取课程列表失败：{exc}")
            return

        self.course_list.blockSignals(True)
        self.course_list.clear()
        
        # 过滤重复课程：同一课程和学期只显示一条
        seen_courses = set()
        self._teachings = []
        
        for t in all_teachings:
            course_key = (t['course_name'], t['semester'])
            
            # 如果已经见过这个课程，只在该课程有成绩时才添加
            if course_key in seen_courses:
                continue
            
            seen_courses.add(course_key)
            self._teachings.append(t)
            
            # is_submitted=1 意味着成绩已锁定归档，显示 CLOSED；否则显示数据库原始状态
            display_status = "CLOSED" if t.get("is_submitted", 0) == 1 else t.get("status", "")
            item = QListWidgetItem(
                f"{t['course_name']}\n"
                f"{t['semester']}  {t.get('classroom', '')}  {display_status}"
            )
            item.setData(Qt.ItemDataRole.UserRole, t["teaching_id"])
            self.course_list.addItem(item)
        
        self.course_list.blockSignals(False)

        if self._teachings:
            self.course_list.setCurrentRow(0)

    def _on_course_selected(self, row: int) -> None:
        if row < 0 or row >= len(self._teachings):
            self._current_teaching_id = None
            return

        t = self._teachings[row]
        self._current_teaching_id = t["teaching_id"]
        
        is_locked = t.get("is_submitted", 0) == 1
        
        if is_locked:
            self.lbl_course_info.setText(
                f"🔒 {t['course_name']}  |  学期: {t['semester']}  |  "
                f"教室: {t.get('classroom', '—')}  |  "
                f"【成绩已提交锁定 - 没有使用权限】"
            )
            self.lbl_course_info.setStyleSheet("color: #C0392B; font-weight: bold; padding: 6px;")
        else:
            self.lbl_course_info.setText(
                f"{t['course_name']}  |  学期: {t['semester']}  |  "
                f"教室: {t.get('classroom', '—')}  |  "
                f"时间: {t.get('timeslot', '—')}  |  "
                f"学分: {t.get('credits', '—')}"
            )
            self.lbl_course_info.setStyleSheet("color: #333; padding: 6px;")

        self._is_submitted = is_locked

        # 已归档课程禁用批量操作（tab 5）和课程设置（tab 6）
        self.tabs.setTabEnabled(5, not is_locked)
        self.tabs.setTabEnabled(6, not is_locked)
        # 若当前处于被禁用的 tab，切回成绩录入
        if is_locked and self.tabs.currentIndex() in (5, 6):
            self.tabs.setCurrentIndex(0)

        self._load_grade_table()
        self._load_analysis()
        self._update_quick_stats()
        self._load_enrollment_panel()

    def _on_tab_changed(self, index: int) -> None:
        if index == 1:
            self._load_analysis()
        elif index == 2:
            self._load_warning()
        elif index == 3:
            self._load_daily_summary_table()
        elif index == 4:
            self._refresh_archive_semester_combo()
        elif index == 5:
            pass
        elif index == 6:
            self._load_settings_tab()

    def _load_grade_table(self) -> None:
        if self._current_teaching_id is None:
            return

        try:
            self._is_submitted = self._teacher_svc.is_grades_submitted(
                self._current_teaching_id
            )
        except Exception:
            self._is_submitted = False

        if self._is_submitted:
            self.grade_table.blockSignals(True)
            self.grade_table.setRowCount(1)
            item = QTableWidgetItem("🔒 该课程成绩已提交锁定 - 没有使用权限")
            item.setFont(QFont("", -1, QFont.Weight.Bold))
            item.setForeground(QBrush(QColor("#C0392B")))
            self.grade_table.setItem(0, 0, item)
            self.grade_table.blockSignals(False)
            self._apply_lock_state()
            return

        try:
            daily_rows = self._analysis_dao.get_daily_score_summary(
                self._current_teaching_id
            )
            self._daily_score_cache = {
                int(r["student_id"]): float(r["daily_score"] or 0)
                for r in daily_rows
            }
        except Exception:
            self._daily_score_cache = {}

        try:
            rows = self._grade_svc.get_teaching_grades_with_exam(self._current_teaching_id)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "加载失败", f"获取成绩列表失败：{exc}")
            return

        self.grade_table.blockSignals(True)
        self.grade_table.setRowCount(0)

        for row_data in rows:
            r = self.grade_table.rowCount()
            self.grade_table.insertRow(r)

            student_id = row_data.get("student_id")
            daily_score = float(row_data.get("daily_score") or 0)
            exam_score  = row_data.get("exam_score")
            final_score = row_data.get("score")

            item_no = QTableWidgetItem(str(row_data.get("username", "")))
            item_no.setFlags(item_no.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_no.setData(Qt.ItemDataRole.UserRole, student_id)
            item_no.setData(Qt.ItemDataRole.UserRole + 1, daily_score)
            self.grade_table.setItem(r, self._COL_USERNAME, item_no)

            item_name = QTableWidgetItem(str(row_data.get("real_name", "")))
            item_name.setFlags(item_name.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.grade_table.setItem(r, self._COL_REALNAME, item_name)

            item_daily = QTableWidgetItem(f"{daily_score:.2f}")
            item_daily.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_daily.setForeground(QBrush(QColor("#2980b9")))
            self.grade_table.setItem(r, self._COL_DAILY, item_daily)

            exam_str = f"{float(exam_score):.1f}" if exam_score is not None else ""
            item_exam = QTableWidgetItem(exam_str)
            item_exam.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grade_table.setItem(r, self._COL_EXAM, item_exam)

            final_str = f"{float(final_score):.2f}" if final_score is not None else ""
            item_final = QTableWidgetItem(final_str)
            item_final.setFlags(item_final.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_final.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grade_table.setItem(r, self._COL_FINAL, item_final)

            item_letter = QTableWidgetItem(row_data.get("grade_letter") or "")
            item_letter.setFlags(item_letter.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_letter.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grade_table.setItem(r, self._COL_LETTER, item_letter)

            gpa = row_data.get("gpa_point")
            item_gpa = QTableWidgetItem(f"{float(gpa):.2f}" if gpa is not None else "")
            item_gpa.setFlags(item_gpa.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_gpa.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grade_table.setItem(r, self._COL_GPA, item_gpa)

            is_passed = row_data.get("is_passed")
            passed_text = "通过" if is_passed else ("不通过" if exam_score is not None else "")
            item_passed = QTableWidgetItem(passed_text)
            item_passed.setFlags(item_passed.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_passed.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if is_passed == 0 and exam_score is not None:
                item_passed.setForeground(QBrush(QColor("#E74C3C")))
            self.grade_table.setItem(r, self._COL_PASSED, item_passed)

        self.grade_table.blockSignals(False)

        self._apply_lock_state()

    def _apply_lock_state(self) -> None:
        locked = self._is_submitted

        self.lbl_locked.setVisible(locked)

        for r in range(self.grade_table.rowCount()):
            item_exam = self.grade_table.item(r, self._COL_EXAM)
            item_daily = self.grade_table.item(r, self._COL_DAILY)
            
            if item_exam is not None:
                if locked:
                    item_exam.setFlags(item_exam.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item_exam.setBackground(QBrush(QColor("#f0f0f0")))
                else:
                    item_exam.setFlags(item_exam.flags() | Qt.ItemFlag.ItemIsEditable)
            
            if item_daily is not None:
                if locked:
                    item_daily.setFlags(item_daily.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item_daily.setBackground(QBrush(QColor("#f0f0f0")))
                else:
                    item_daily.setFlags(item_daily.flags() | Qt.ItemFlag.ItemIsEditable)

        self.btn_import_daily_quick.setEnabled(not locked)
        self.btn_save_grades.setEnabled(not locked)
        self.btn_import_excel.setEnabled(not locked)
        self.btn_export_excel.setEnabled(True)
        self.btn_submit_grades.setEnabled(not locked)
        if locked:
            self.btn_submit_grades.setText("✅ 已提交（已锁定）")
        else:
            self.btn_submit_grades.setText("提交成绩（锁定）")

    def _on_grade_cell_changed(self, item: QTableWidgetItem) -> None:
        """处理卷面成绩或平时分变化，重新计算最终成绩"""
        col = item.column()
        if col not in (self._COL_EXAM, self._COL_DAILY):
            return

        row = item.row()
        text = item.text().strip()
        
        if col == self._COL_DAILY:
            if not text:
                return
            try:
                daily_score = float(text)
            except ValueError:
                item.setBackground(QBrush(QColor("#FADBD8")))
                return
            if not (0.0 <= daily_score <= 30.0):
                item.setBackground(QBrush(QColor("#FADBD8")))
                return
            item.setBackground(QBrush(QColor(0, 0, 0, 0)))
            
            col0_item = self.grade_table.item(row, self._COL_USERNAME)
            if col0_item:
                col0_item.setData(Qt.ItemDataRole.UserRole + 1, daily_score)
        
        item_exam = self.grade_table.item(row, self._COL_EXAM)
        item_daily = self.grade_table.item(row, self._COL_DAILY)
        
        if not item_exam or not item_exam.text().strip():
            if col == self._COL_EXAM:
                for c in (self._COL_FINAL, self._COL_LETTER, self._COL_GPA, self._COL_PASSED):
                    cell = self.grade_table.item(row, c)
                    if cell:
                        cell.setText("")
            return

        try:
            exam_score = float(item_exam.text())
        except ValueError:
            if col == self._COL_EXAM:
                item_exam.setBackground(QBrush(QColor("#FADBD8")))
            return

        if not (0.0 <= exam_score <= 100.0):
            if col == self._COL_EXAM:
                item_exam.setBackground(QBrush(QColor("#FADBD8")))
            return

        if col == self._COL_EXAM:
            item_exam.setBackground(QBrush(QColor(0, 0, 0, 0)))

        daily_score = 0.0
        if item_daily and item_daily.text().strip():
            try:
                daily_score = float(item_daily.text())
            except ValueError:
                pass

        weights = self._get_current_weights()
        final_score = round(
            exam_score * weights["exam_weight"] + daily_score * weights["daily_weight"] / 0.3,
            2
        )
        gpa, letter, is_passed = score_to_gpa(final_score)

        self.grade_table.blockSignals(True)

        cell_final = self.grade_table.item(row, self._COL_FINAL)
        if cell_final:
            cell_final.setText(f"{final_score:.2f}")

        cell_letter = self.grade_table.item(row, self._COL_LETTER)
        if cell_letter:
            cell_letter.setText(letter)

        cell_gpa = self.grade_table.item(row, self._COL_GPA)
        if cell_gpa:
            cell_gpa.setText(f"{gpa:.2f}")

        cell_passed = self.grade_table.item(row, self._COL_PASSED)
        if cell_passed:
            cell_passed.setText("通过" if is_passed else "不通过")
            cell_passed.setForeground(
                QBrush(QColor("#27AE60") if is_passed else QColor("#E74C3C"))
            )

        self.grade_table.blockSignals(False)

    def _save_grades(self) -> None:
        if self._current_teaching_id is None:
            return
        if self._is_submitted:
            QMessageBox.warning(self, "已锁定", "成绩已提交，不可再修改。")
            return

        exam_dict: dict[int, float] = {}
        errors: list[str] = []

        for row in range(self.grade_table.rowCount()):
            exam_text = self.grade_table.item(row, self._COL_EXAM).text().strip()
            if not exam_text:
                continue
            try:
                score = float(exam_text)
            except ValueError:
                name = self.grade_table.item(row, self._COL_REALNAME).text()
                errors.append(f"第 {row+1} 行 ({name}) 成绩格式错误")
                continue
            student_id = self.grade_table.item(row, self._COL_USERNAME).data(Qt.ItemDataRole.UserRole)
            exam_dict[student_id] = score

        if errors:
            QMessageBox.warning(self, "格式错误", "\n".join(errors))
            return
        if not exam_dict:
            QMessageBox.information(self, "提示", "没有需要保存的成绩，请先填写卷面成绩列。")
            return

        try:
            count = self._grade_svc.batch_enter_exam_scores(
                self._current_teaching_id, exam_dict
            )
            QMessageBox.information(self, "保存成功", f"已成功保存 {count} 条成绩记录。")
            self.lbl_last_save.setText(f"最后保存时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self._load_grade_table()
            self._load_analysis()
        except (ValidationError, BusinessError) as exc:
            QMessageBox.warning(self, "保存失败", str(exc))
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "系统错误", f"保存失败：{exc}")

    def _import_grades_excel(self) -> None:
        if self._current_teaching_id is None:
            return
        if self._is_submitted:
            QMessageBox.warning(self, "已锁定", "成绩已提交，不可再导入。")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择卷面成绩 Excel 文件", "",
            "Excel 文件 (*.xlsx *.xls);;所有文件 (*)",
        )
        if not file_path:
            return

        try:
            count = self._teacher_svc.import_grades_from_excel(
                self._current_teaching_id, file_path
            )
            QMessageBox.information(self, "导入成功", f"已从 Excel 导入 {count} 条卷面成绩。")
            self._load_grade_table()
            self._load_analysis()
        except (ValidationError, BusinessError) as exc:
            QMessageBox.warning(self, "导入失败", str(exc))
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "系统错误", f"导入失败：{exc}")

    def _submit_grades(self) -> None:
        if self._current_teaching_id is None:
            return

        reply = QMessageBox.question(
            self, "确认提交",
            "提交后成绩将被<b>永久锁定</b>，不可再修改。\n\n"
            "请确认所有卷面成绩已录入完毕，是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            count = self._teacher_svc.submit_grades(self._current_teaching_id)
            QMessageBox.information(
                self, "提交成功",
                f"已成功提交 {count} 条成绩，成绩已锁定。",
            )
            self._is_submitted = True
            self._apply_lock_state()
        except (ValidationError, BusinessError) as exc:
            QMessageBox.warning(self, "提交失败", str(exc))
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "系统错误", f"提交失败：{exc}")

    def _export_excel(self) -> None:
        if self._current_teaching_id is None:
            return
        t = next((x for x in self._teachings
                   if x["teaching_id"] == self._current_teaching_id), {})
        default_name = f"{t.get('course_name', '成绩单')}_{t.get('semester', '')}.xlsx"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出 Excel 成绩单", default_name,
            "Excel 文件 (*.xlsx);;所有文件 (*)",
        )
        if not file_path:
            return
        try:
            self._exporter.export_class_grade_sheet(self._current_teaching_id, file_path)
            QMessageBox.information(self, "导出成功", f"成绩单已保存至：\n{file_path}")
        except BusinessError as exc:
            QMessageBox.warning(self, "导出失败", str(exc))
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "系统错误", f"导出失败：{exc}")

    def _load_analysis(self) -> None:
        if self._current_teaching_id is None:
            self.chart_canvas.clear_plot()
            return

        try:
            dist  = self._analysis_dao.get_score_distribution(self._current_teaching_id)
            stats = self._analysis_dao.get_teaching_stats(self._current_teaching_id)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "加载失败", f"获取统计数据失败：{exc}")
            return

        def _fmt(val, suffix=""):
            return f"{val}{suffix}" if val is not None else "—"

        self.lbl_avg.setText(_fmt(stats.get("avg_score")))
        self.lbl_max.setText(_fmt(stats.get("max_score")))
        self.lbl_min.setText(_fmt(stats.get("min_score")))
        self.lbl_std.setText(_fmt(stats.get("std_dev")))
        self.lbl_pass.setText(_fmt(stats.get("pass_rate"), "%"))
        self.lbl_count.setText(_fmt(stats.get("student_count"), " 人"))

        if self._is_submitted:
            self.chart_canvas.clear_plot()
            self.btn_export_report.setEnabled(False)
            self.btn_detailed_stats.setEnabled(False)
        else:
            t = next((x for x in self._teachings
                       if x["teaching_id"] == self._current_teaching_id), {})
            title = f"{t.get('course_name', '')} {t.get('semester', '')} 成绩分析"
            self.chart_canvas.plot_distribution(dist, title)
            self.btn_export_report.setEnabled(bool(dist.get("total")))
            self.btn_detailed_stats.setEnabled(bool(dist.get("total")))

    def _export_report(self) -> None:
        if self._current_teaching_id is None:
            return
        t = next((x for x in self._teachings
                   if x["teaching_id"] == self._current_teaching_id), {})
        default_name = f"{t.get('course_name', '报告')}_{t.get('semester', '')}_分析报告.pdf"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出分析报告", default_name,
            "PDF 文件 (*.pdf);;PNG 图片 (*.png);;所有文件 (*)",
        )
        if not file_path:
            return
        try:
            title = f"{t.get('course_name', '')} {t.get('semester', '')} 成绩分析报告"
            self._exporter.export_analysis_report(
                self._current_teaching_id, file_path, title
            )
            QMessageBox.information(self, "导出成功", f"分析报告已保存至：\n{file_path}")
        except BusinessError as exc:
            QMessageBox.warning(self, "导出失败", str(exc))
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "系统错误", f"导出失败：{exc}")

    def _show_detailed_stats(self) -> None:
        if self._current_teaching_id is None:
            return
        dlg = _DetailedStatsDialog(self._current_teaching_id, self)
        dlg.exec()

    def _load_warning(self) -> None:
        # 归档课程同样允许查看挂科预警，只是成绩不可再修改
        if self._current_teaching_id is None:
            self.warning_table.setRowCount(0)
            return
        
        try:
            rows = self._analysis_dao.get_failed_students_warning()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "加载失败", f"获取预警数据失败：{exc}")
            return

        self.warning_table.setRowCount(0)
        
        # 只显示当前课程的学生
        current_course_name = None
        current_semester = None
        if self._current_teaching_id is not None and len(self._teachings) > 0:
            for t in self._teachings:
                if t["teaching_id"] == self._current_teaching_id:
                    current_course_name = t.get("course_name")
                    current_semester = t.get("semester")
                    break
        
        for row_data in rows:
            # 只添加属于当前课程的学生
            if (row_data.get("course_name") != current_course_name or 
                row_data.get("semester") != current_semester):
                continue
            
            r = self.warning_table.rowCount()
            self.warning_table.insertRow(r)
            cells = [
                row_data.get("username", ""),
                row_data.get("real_name", ""),
                row_data.get("course_name", ""),
                row_data.get("semester", ""),
                str(row_data.get("score", "")),
                row_data.get("grade_letter", ""),
            ]
            for col, val in enumerate(cells):
                cell = QTableWidgetItem(val)
                cell.setFlags(cell.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col in (4, 5):
                    cell.setForeground(QBrush(QColor("#E74C3C")))
                self.warning_table.setItem(r, col, cell)

    def _export_warning_list(self) -> None:
        if self.warning_table.rowCount() == 0:
            QMessageBox.information(self, "提示", "当前没有预警数据可导出。")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出预警名单", "挂科预警名单.xlsx",
            "Excel 文件 (*.xlsx);;所有文件 (*)",
        )
        if not file_path:
            return

        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "挂科预警"

            headers = ["学号", "姓名", "课程", "学期", "成绩", "等级"]
            ws.append(headers)

            for row in range(self.warning_table.rowCount()):
                row_data = []
                for col in range(6):
                    item = self.warning_table.item(row, col)
                    row_data.append(item.text() if item else "")
                ws.append(row_data)

            wb.save(file_path)
            QMessageBox.information(self, "导出成功", f"预警名单已保存至：\n{file_path}")
        except ImportError:
            QMessageBox.warning(self, "导出失败", "需要安装 openpyxl 库：pip install openpyxl")
        except Exception as exc:
            QMessageBox.critical(self, "导出失败", str(exc))

    def _load_daily_summary_table(self) -> None:
        """加载平时分汇总表格"""
        if self._current_teaching_id is None:
            QMessageBox.warning(self, "提示", "请先在左侧选择课程。")
            return

        if self._is_submitted:
            self.daily_summary_table.setRowCount(1)
            item = QTableWidgetItem("🔒 该课程成绩已提交锁定 - 没有使用权限")
            item.setFont(QFont("", -1, QFont.Weight.Bold))
            item.setForeground(QBrush(QColor("#C0392B")))
            self.daily_summary_table.setItem(0, 0, item)
            return

        try:
            rows = self._analysis_dao.get_daily_score_summary(self._current_teaching_id)
        except Exception as exc:
            QMessageBox.warning(self, "加载失败", f"获取平时分汇总失败：{exc}")
            return

        self.daily_summary_table.blockSignals(True)
        self.daily_summary_table.setRowCount(len(rows))
        
        for i, r in enumerate(rows):
            student_id = r.get("student_id")
            total_records = int(r.get("total_records", 0))
            completed_records = int(r.get("completed_records", 0))
            completion_rate = float(r.get("completion_rate", 0))
            daily_score = float(r.get("daily_score", 0))
            
            item_no = QTableWidgetItem(r.get("username", ""))
            item_no.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_no.setFlags(item_no.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_no.setData(Qt.ItemDataRole.UserRole, student_id)
            item_no.setData(Qt.ItemDataRole.UserRole + 1, total_records)
            self.daily_summary_table.setItem(i, 0, item_no)
            
            item_name = QTableWidgetItem(r.get("real_name", ""))
            item_name.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_name.setFlags(item_name.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.daily_summary_table.setItem(i, 1, item_name)
            
            item_total = QTableWidgetItem(str(total_records))
            item_total.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_total.setFlags(item_total.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_total.setBackground(QBrush(QColor("#ECF0F1")))
            self.daily_summary_table.setItem(i, 2, item_total)
            
            item_completed = QTableWidgetItem(str(completed_records))
            item_completed.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_completed.setBackground(QBrush(QColor("#FFF9C4")))
            self.daily_summary_table.setItem(i, 3, item_completed)
            
            item_rate = QTableWidgetItem(f"{completion_rate:.1f}")
            item_rate.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_rate.setFlags(item_rate.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.daily_summary_table.setItem(i, 4, item_rate)
            
            item_score = QTableWidgetItem(f"{daily_score:.2f}")
            item_score.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_score.setFlags(item_score.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if daily_score >= 25:
                item_score.setForeground(QBrush(QColor("#27AE60")))
                item_score.setFont(QFont("", -1, QFont.Weight.Bold))
            elif daily_score < 15:
                item_score.setForeground(QBrush(QColor("#E74C3C")))
                item_score.setFont(QFont("", -1, QFont.Weight.Bold))
            self.daily_summary_table.setItem(i, 5, item_score)
        
        self.daily_summary_table.blockSignals(False)
        
        if rows:
            QMessageBox.information(
                self, "加载成功", 
                f"已加载 {len(rows)} 名学生的平时分汇总数据。\n\n"
                f"💡 您可以：\n"
                f"1. 直接修改'已完成'列的数值（黄色背景）\n"
                f"2. 系统会自动重新计算完成率和平时分\n"
                f"3. 点击'一键导入平时分到成绩表'批量导入"
            )
        else:
            QMessageBox.information(
                self, "提示", 
                "当前课程暂无平时记录数据。\n"
                "平时记录由系统管理员或通过数据库统一导入。"
            )

    def _on_daily_completed_changed(self, item: QTableWidgetItem) -> None:
        """已完成数变化时，重新计算完成率和平时分"""
        if item.column() != 3:
            return
        
        row = item.row()
        text = item.text().strip()
        
        try:
            completed = int(text)
        except ValueError:
            item.setBackground(QBrush(QColor("#FADBD8")))
            return
        
        item_no = self.daily_summary_table.item(row, 0)
        if not item_no:
            return
        
        total_records = int(item_no.data(Qt.ItemDataRole.UserRole + 1) or 0)
        
        if completed < 0 or completed > total_records:
            item.setBackground(QBrush(QColor("#FADBD8")))
            return
        
        item.setBackground(QBrush(QColor("#FFF9C4")))
        
        completion_rate = (completed * 100.0 / total_records) if total_records > 0 else 0.0
        daily_score = (completed * 30.0 / total_records) if total_records > 0 else 0.0
        
        self.daily_summary_table.blockSignals(True)
        
        item_rate = self.daily_summary_table.item(row, 4)
        if item_rate:
            item_rate.setText(f"{completion_rate:.1f}")
        
        item_score = self.daily_summary_table.item(row, 5)
        if item_score:
            item_score.setText(f"{daily_score:.2f}")
            if daily_score >= 25:
                item_score.setForeground(QBrush(QColor("#27AE60")))
                item_score.setFont(QFont("", -1, QFont.Weight.Bold))
            elif daily_score < 15:
                item_score.setForeground(QBrush(QColor("#E74C3C")))
                item_score.setFont(QFont("", -1, QFont.Weight.Bold))
            else:
                item_score.setForeground(QBrush(QColor("#000000")))
                item_score.setFont(QFont("", -1, QFont.Weight.Normal))
        
        self.daily_summary_table.blockSignals(False)

    def _save_daily_changes(self) -> None:
        """保存教师对平时分的手动调整（仅供参考，实际不写入数据库）"""
        if self._current_teaching_id is None:
            return
        
        QMessageBox.information(
            self, "提示",
            "平时分修改已在表格中生效。\n\n"
            "这些修改会在您点击'一键导入平时分到成绩表'时应用。\n"
            "无需单独保存到数据库。"
        )

    def _import_daily_scores_to_grades(self) -> None:
        """一键将平时分导入到成绩表，并重新计算最终成绩"""
        if self._current_teaching_id is None:
            QMessageBox.warning(self, "提示", "请先在左侧选择课程。")
            return

        if self._is_submitted:
            QMessageBox.warning(self, "已锁定", "成绩已提交锁定，无法导入平时分。")
            return

        if self.daily_summary_table.rowCount() == 0:
            QMessageBox.warning(
                self, "无数据",
                "平时分汇总表为空。\n\n"
                "请先点击'刷新平时分汇总'加载数据。"
            )
            return

        reply = QMessageBox.question(
            self, "确认导入",
            "即将从当前平时分汇总表导入数据到成绩录入表。\n\n"
            "导入后将自动重新计算所有学生的最终成绩。\n"
            "此操作会覆盖成绩表中的平时分列，是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            new_map = {}
            for i in range(self.daily_summary_table.rowCount()):
                item_no = self.daily_summary_table.item(i, 0)
                item_score = self.daily_summary_table.item(i, 5)
                if item_no and item_score:
                    student_id = item_no.data(Qt.ItemDataRole.UserRole)
                    daily_score = float(item_score.text())
                    new_map[int(student_id)] = daily_score
            
            if not new_map:
                QMessageBox.warning(self, "无数据", "平时分汇总表中没有有效数据。")
                return
            
            self.grade_table.blockSignals(True)
            updated_count = 0
            
            for r in range(self.grade_table.rowCount()):
                item_no = self.grade_table.item(r, self._COL_USERNAME)
                if item_no is None:
                    continue
                
                sid = item_no.data(Qt.ItemDataRole.UserRole)
                daily = new_map.get(int(sid), 0.0)
                
                item_no.setData(Qt.ItemDataRole.UserRole + 1, daily)
                
                item_daily = self.grade_table.item(r, self._COL_DAILY)
                if item_daily:
                    old_daily = item_daily.text()
                    item_daily.setText(f"{daily:.2f}")
                    if old_daily != f"{daily:.2f}":
                        updated_count += 1
                
                item_exam = self.grade_table.item(r, self._COL_EXAM)
                if item_exam and item_exam.text().strip():
                    try:
                        exam_score = float(item_exam.text())
                        weights = self._get_current_weights()
                        final_score = round(
                            exam_score * weights["exam_weight"] + daily * weights["daily_weight"] / 0.3,
                            2
                        )
                        gpa, letter, is_passed = score_to_gpa(final_score)
                        
                        cell_final = self.grade_table.item(r, self._COL_FINAL)
                        if cell_final:
                            cell_final.setText(f"{final_score:.2f}")
                        
                        cell_letter = self.grade_table.item(r, self._COL_LETTER)
                        if cell_letter:
                            cell_letter.setText(letter)
                        
                        cell_gpa = self.grade_table.item(r, self._COL_GPA)
                        if cell_gpa:
                            cell_gpa.setText(f"{gpa:.2f}")
                        
                        cell_passed = self.grade_table.item(r, self._COL_PASSED)
                        if cell_passed:
                            cell_passed.setText("通过" if is_passed else "不通过")
                            cell_passed.setForeground(
                                QBrush(QColor("#27AE60") if is_passed else QColor("#E74C3C"))
                            )
                    except ValueError:
                        pass
            
            self.grade_table.blockSignals(False)
            self._daily_score_cache = new_map
            
            QMessageBox.information(
                self, "导入成功",
                f"✅ 已成功导入 {len(new_map)} 名学生的平时分！\n\n"
                f"更新了 {updated_count} 名学生的平时分数据。\n"
                f"已自动重新计算最终成绩、等级和绩点。\n\n"
                f"请切换到'成绩录入'标签页查看更新后的成绩表。"
            )
            
            self.tabs.setCurrentIndex(0)
            
        except Exception as exc:
            QMessageBox.critical(self, "导入失败", f"导入平时分失败：{exc}")

    def _quick_import_daily(self) -> None:
        """在成绩录入页面快速导入平时分"""
        if self._current_teaching_id is None:
            return
        if self._is_submitted:
            QMessageBox.warning(self, "已锁定", "成绩已提交锁定，无法导入平时分。")
            return

        try:
            daily_rows = self._analysis_dao.get_daily_score_summary(
                self._current_teaching_id
            )
            
            if not daily_rows:
                QMessageBox.information(
                    self, "提示", 
                    "当前课程没有平时记录数据。\n\n"
                    "您可以：\n"
                    "1. 手动在平时分列输入分数（0-30分）\n"
                    "2. 或联系管理员导入平时记录数据"
                )
                return
            
            new_map = {int(r["student_id"]): float(r["daily_score"] or 0) for r in daily_rows}
            
            self.grade_table.blockSignals(True)
            updated_count = 0
            
            for r in range(self.grade_table.rowCount()):
                item_no = self.grade_table.item(r, self._COL_USERNAME)
                if item_no is None:
                    continue
                
                sid = item_no.data(Qt.ItemDataRole.UserRole)
                daily = new_map.get(int(sid), 0.0)
                
                item_no.setData(Qt.ItemDataRole.UserRole + 1, daily)
                
                item_daily = self.grade_table.item(r, self._COL_DAILY)
                if item_daily:
                    item_daily.setText(f"{daily:.2f}")
                    updated_count += 1
            
            self.grade_table.blockSignals(False)
            
            for r in range(self.grade_table.rowCount()):
                item_exam = self.grade_table.item(r, self._COL_EXAM)
                if item_exam:
                    self._on_grade_cell_changed(item_exam)
            
            self._daily_score_cache = new_map
            
            QMessageBox.information(
                self, "导入成功",
                f"✅ 已成功导入 {updated_count} 名学生的平时分！\n\n"
                f"平时分已填充到表格中，您可以手动修改。\n"
                f"系统已自动重新计算最终成绩。\n\n"
                f"请检查后点击'保存成绩'。"
            )
            
        except Exception as exc:
            QMessageBox.critical(self, "导入失败", f"导入平时分失败：{exc}")

    def _refresh_archive_semester_combo(self) -> None:
        if Session.current_user is None:
            return
        try:
            semesters = self._teacher_svc.get_available_archive_semesters(
                Session.current_user.id
            )
        except Exception:
            semesters = []

        self._cmb_archive_semester.blockSignals(True)
        self._cmb_archive_semester.clear()
        self._cmb_archive_semester.addItems(semesters)
        self._cmb_archive_semester.blockSignals(False)

    def _load_archive_data(self) -> None:
        if Session.current_user is None:
            return

        semester = self._cmb_archive_semester.currentText()
        if not semester:
            QMessageBox.information(self, "提示", "没有可查询的归档学期，请先执行学期归档操作。")
            return

        try:
            rows = self._teacher_svc.get_archived_grades(Session.current_user.id, semester)
        except Exception as exc:
            QMessageBox.warning(self, "查询失败", str(exc))
            return

        self.archive_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            gpa = r.get("gpa_point")
            vals = [
                r.get("username", ""),
                r.get("real_name", ""),
                r.get("course_name", ""),
                r.get("semester", ""),
                str(r.get("score", "")) if r.get("score") is not None else "—",
                r.get("grade_letter") or "—",
                f"{float(gpa):.2f}" if gpa is not None else "—",
                str(r.get("archived_at", ""))[:16],
            ]
            for j, val in enumerate(vals):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if j == 5 and r.get("is_passed") == 0:
                    item.setForeground(QBrush(QColor("#E74C3C")))
                self.archive_table.setItem(i, j, item)

    def _archive_grades(self) -> None:
        semester, ok = QInputDialog.getText(
            self, "归档成绩",
            "请输入要归档的学期（格式: 2024-1）：",
        )
        if not ok or not semester.strip():
            return

        reply = QMessageBox.question(
            self, "确认归档",
            f"即将将 【{semester.strip()}】 学期的所有成绩归档。\n"
            "归档后主表记录将被软删除，不影响已存档数据。\n\n确定继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            archived = self._grade_svc.archive_semester_grades(semester.strip())
            QMessageBox.information(
                self, "归档完成",
                f"学期 {semester.strip()} 共归档 {archived} 条成绩记录。",
            )
            self._load_grade_table()
            self._load_analysis()
        except (ValidationError, BusinessError) as exc:
            QMessageBox.warning(self, "归档失败", str(exc))
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "系统错误", f"归档失败：{exc}")

    def _batch_adjust_grades(self) -> None:
        if self._current_teaching_id is None:
            QMessageBox.warning(self, "提示", "请先在左侧选择课程。")
            return
        if self._is_submitted:
            QMessageBox.warning(self, "已锁定", "成绩已提交，不可再调整。")
            return

        dlg = _BatchAdjustDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        params = dlg.get_adjustment_params()
        method = params["method"]
        value = params["value"]
        cap = params["cap"]

        adjusted_count = 0
        self.grade_table.blockSignals(True)

        for row in range(self.grade_table.rowCount()):
            item_exam = self.grade_table.item(row, self._COL_EXAM)
            if not item_exam or not item_exam.text().strip():
                continue

            try:
                old_score = float(item_exam.text())
            except ValueError:
                continue

            if method == "add":
                new_score = old_score + value
            elif method == "subtract":
                new_score = old_score - value
            elif method == "scale":
                new_score = old_score * value
            elif method == "sqrt":
                import math
                new_score = math.sqrt(old_score) * 10
            else:
                new_score = old_score

            if cap:
                new_score = max(0.0, min(100.0, new_score))

            item_exam.setText(f"{new_score:.1f}")
            adjusted_count += 1

        self.grade_table.blockSignals(False)

        for row in range(self.grade_table.rowCount()):
            item_exam = self.grade_table.item(row, self._COL_EXAM)
            if item_exam:
                self._on_grade_cell_changed(item_exam)

        QMessageBox.information(
            self, "调分完成",
            f"已调整 {adjusted_count} 名学生的卷面成绩。\n请检查后点击'保存成绩'。"
        )

    def _auto_curve_grades(self) -> None:
        if self._current_teaching_id is None:
            QMessageBox.warning(self, "提示", "请先在左侧选择课程。")
            return
        if self._is_submitted:
            QMessageBox.warning(self, "已锁定", "成绩已提交，不可再调整。")
            return

        reply = QMessageBox.question(
            self, "智能调分",
            "智能调分将根据当前成绩分布自动调整，使平均分接近 75 分。\n\n"
            "此操作会修改所有卷面成绩，是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        scores = []
        for row in range(self.grade_table.rowCount()):
            item_exam = self.grade_table.item(row, self._COL_EXAM)
            if item_exam and item_exam.text().strip():
                try:
                    scores.append(float(item_exam.text()))
                except ValueError:
                    pass

        if not scores:
            QMessageBox.warning(self, "提示", "没有可调整的成绩数据。")
            return

        avg = sum(scores) / len(scores)
        target_avg = 75.0
        adjustment = target_avg - avg

        self.grade_table.blockSignals(True)
        for row in range(self.grade_table.rowCount()):
            item_exam = self.grade_table.item(row, self._COL_EXAM)
            if not item_exam or not item_exam.text().strip():
                continue
            try:
                old_score = float(item_exam.text())
                new_score = max(0.0, min(100.0, old_score + adjustment))
                item_exam.setText(f"{new_score:.1f}")
            except ValueError:
                pass
        self.grade_table.blockSignals(False)

        for row in range(self.grade_table.rowCount()):
            item_exam = self.grade_table.item(row, self._COL_EXAM)
            if item_exam:
                self._on_grade_cell_changed(item_exam)

        QMessageBox.information(
            self, "调分完成",
            f"已自动调整成绩，平均分从 {avg:.2f} 调整至约 {target_avg:.2f}。\n"
            f"调整幅度：{adjustment:+.2f} 分。"
        )

    def _filter_grades(self) -> None:
        if self._current_teaching_id is None:
            QMessageBox.warning(self, "提示", "请先在左侧选择课程。")
            return

        dlg = _GradeFilterDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        params = dlg.get_filter_params()
        min_score   = params["min_score"]
        max_score   = params["max_score"]
        letter_filter = params["letter"]
        passed_filter = params["passed"]

        matched: list[tuple[str, str, str, str, str]] = []  # (学号, 姓名, 最终成绩, 等级, 是否通过)
        for row in range(self.grade_table.rowCount()):
            item_final  = self.grade_table.item(row, self._COL_FINAL)
            item_letter = self.grade_table.item(row, self._COL_LETTER)
            item_passed = self.grade_table.item(row, self._COL_PASSED)

            if not item_final or not item_final.text().strip():
                continue
            try:
                final_score = float(item_final.text())
            except ValueError:
                continue

            if not (min_score <= final_score <= max_score):
                continue
            if letter_filter and item_letter and item_letter.text() != letter_filter:
                continue
            if passed_filter == "passed" and item_passed and item_passed.text() != "通过":
                continue
            if passed_filter == "failed" and item_passed and item_passed.text() != "不通过":
                continue

            no   = (self.grade_table.item(row, self._COL_USERNAME) or QTableWidgetItem("")).text()
            name = (self.grade_table.item(row, self._COL_REALNAME) or QTableWidgetItem("")).text()
            matched.append((no, name, item_final.text(),
                            item_letter.text() if item_letter else "",
                            item_passed.text() if item_passed else ""))

        # 弹窗展示结果
        result_dlg = QDialog(self)
        result_dlg.setWindowTitle(f"筛选结果（共 {len(matched)} 人）")
        result_dlg.resize(520, 360)
        v = QVBoxLayout(result_dlg)

        lbl = QLabel(f"符合条件的学生共 <b>{len(matched)}</b> 人：")
        lbl.setStyleSheet("padding: 4px; font-size: 12px;")
        v.addWidget(lbl)

        tbl = QTableWidget(len(matched), 5)
        tbl.setHorizontalHeaderLabels(["学号", "姓名", "最终成绩", "等级", "是否通过"])
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setAlternatingRowColors(True)
        tbl.verticalHeader().setVisible(False)  # type: ignore[union-attr]
        hdr = tbl.horizontalHeader()
        if hdr:
            hdr.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for i, (no, name, score, letter, passed) in enumerate(matched):
            for j, val in enumerate([no, name, score, letter, passed]):
                cell = QTableWidgetItem(val)
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if j == 4 and val == "不通过":
                    cell.setForeground(QBrush(QColor("#E74C3C")))
                tbl.setItem(i, j, cell)
        v.addWidget(tbl)

        close_btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_btn.rejected.connect(result_dlg.accept)
        v.addWidget(close_btn)
        result_dlg.exec()

    def _batch_export_all_courses(self) -> None:
        if not self._teachings:
            QMessageBox.warning(self, "提示", "没有可导出的课程。")
            return

        folder = QFileDialog.getExistingDirectory(self, "选择导出文件夹")
        if not folder:
            return

        progress = QProgressBar()
        progress.setMaximum(len(self._teachings))
        progress.setWindowTitle("批量导出中...")
        progress.show()

        success_count = 0
        for idx, t in enumerate(self._teachings):
            try:
                file_name = f"{t['course_name']}_{t['semester']}.xlsx"
                file_path = os.path.join(folder, file_name)
                self._exporter.export_class_grade_sheet(t["teaching_id"], file_path)
                success_count += 1
            except Exception:
                pass
            progress.setValue(idx + 1)

        progress.close()
        QMessageBox.information(
            self, "导出完成",
            f"已成功导出 {success_count}/{len(self._teachings)} 个课程的成绩单至：\n{folder}"
        )

    def _export_semester_summary(self) -> None:
        if not self._teachings:
            QMessageBox.warning(self, "提示", "没有可统计的课程。")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出学期汇总报告", "学期汇总报告.txt",
            "文本文件 (*.txt);;所有文件 (*)",
        )
        if not file_path:
            return

        lines = ["=" * 60, "学期汇总报告", "=" * 60, ""]

        for t in self._teachings:
            try:
                stats = self._analysis_dao.get_teaching_stats(t["teaching_id"])
                lines.append(f"课程：{t['course_name']} ({t['semester']})")
                lines.append(f"  平均分：{stats.get('avg_score', 0):.2f}")
                lines.append(f"  及格率：{stats.get('pass_rate', 0):.2f}%")
                lines.append(f"  参与人数：{stats.get('student_count', 0)} 人")
                lines.append("")
            except Exception:
                lines.append(f"课程：{t['course_name']} ({t['semester']}) - 数据加载失败")
                lines.append("")

        lines.append("=" * 60)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            QMessageBox.information(self, "导出成功", f"汇总报告已保存至：\n{file_path}")
        except Exception as exc:
            QMessageBox.critical(self, "导出失败", str(exc))

    def _compare_courses(self) -> None:
        QMessageBox.information(
            self, "功能开发中",
            "课程对比分析功能正在开发中，敬请期待。"
        )

    def _analyze_trend(self) -> None:
        QMessageBox.information(
            self, "功能开发中",
            "历史趋势分析功能正在开发中，敬请期待。"
        )

    def _load_settings_tab(self) -> None:
        if self._current_teaching_id is None:
            return

    def _get_current_weights(self) -> dict:
        return {"exam_weight": 0.7, "daily_weight": 0.3}

    def _toggle_auto_save(self, state: int) -> None:
        self._auto_save_enabled = (state == Qt.CheckState.Checked.value)
        if self._auto_save_enabled:
            self._auto_save_timer.start(120000)
            QMessageBox.information(self, "自动保存", "已启用自动保存，每 2 分钟自动保存一次。")
        else:
            self._auto_save_timer.stop()

    def _auto_save_grades(self) -> None:
        if not self._auto_save_enabled or self._is_submitted:
            return
        self._save_grades()

    def _backup_course_data(self) -> None:
        if self._current_teaching_id is None:
            QMessageBox.warning(self, "提示", "请先在左侧选择课程。")
            return

        t = next((x for x in self._teachings
                   if x["teaching_id"] == self._current_teaching_id), {})
        default_name = f"{t.get('course_name', '备份')}_{t.get('semester', '')}_backup.json"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "备份课程数据", default_name,
            "JSON 文件 (*.json);;所有文件 (*)",
        )
        if not file_path:
            return

        try:
            rows = self._grade_svc.get_teaching_grades_with_exam(self._current_teaching_id)
            backup_data = {
                "teaching_id": self._current_teaching_id,
                "course_name": t.get("course_name"),
                "semester": t.get("semester"),
                "backup_time": datetime.now().isoformat(),
                "grades": rows,
            }
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "备份成功", f"课程数据已备份至：\n{file_path}")
        except Exception as exc:
            QMessageBox.critical(self, "备份失败", str(exc))

    def _restore_course_data(self) -> None:
        if self._current_teaching_id is None:
            QMessageBox.warning(self, "提示", "请先在左侧选择课程。")
            return
        if self._is_submitted:
            QMessageBox.warning(self, "已锁定", "成绩已提交，不可恢复备份。")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择备份文件", "",
            "JSON 文件 (*.json);;所有文件 (*)",
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                backup_data = json.load(f)

            if backup_data.get("teaching_id") != self._current_teaching_id:
                reply = QMessageBox.question(
                    self, "课程不匹配",
                    "备份文件的课程 ID 与当前课程不匹配，是否继续恢复？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

            grades = backup_data.get("grades", [])
            exam_dict = {}
            for g in grades:
                if g.get("exam_score") is not None:
                    exam_dict[g["student_id"]] = float(g["exam_score"])

            if not exam_dict:
                QMessageBox.warning(self, "提示", "备份文件中没有卷面成绩数据。")
                return

            count = self._grade_svc.batch_enter_exam_scores(
                self._current_teaching_id, exam_dict
            )
            QMessageBox.information(self, "恢复成功", f"已从备份恢复 {count} 条成绩记录。")
            self._load_grade_table()
            self._load_analysis()
        except Exception as exc:
            QMessageBox.critical(self, "恢复失败", str(exc))

    def _filter_grade_table(self, text: str) -> None:
        text = text.strip().lower()
        for row in range(self.grade_table.rowCount()):
            item_no = self.grade_table.item(row, self._COL_USERNAME)
            item_name = self.grade_table.item(row, self._COL_REALNAME)

            username = item_no.text().lower() if item_no else ""
            realname = item_name.text().lower() if item_name else ""

            if text in username or text in realname:
                self.grade_table.setRowHidden(row, False)
            else:
                self.grade_table.setRowHidden(row, bool(text))

    def _update_quick_stats(self) -> None:
        if self._current_teaching_id is None:
            self.lbl_quick_stats.setText("选择课程后显示")
            return

        try:
            stats = self._analysis_dao.get_teaching_stats(self._current_teaching_id)
            text = (
                f"参与人数：{stats.get('student_count', 0)} 人\n"
                f"平均分：{stats.get('avg_score', 0):.2f}\n"
                f"及格率：{stats.get('pass_rate', 0):.2f}%\n"
                f"不及格：{stats.get('below_60', 0)} 人"
            )
            self.lbl_quick_stats.setText(text)
        except Exception:
            self.lbl_quick_stats.setText("统计数据加载失败")

    # ------------------------------------------------------------------
    # 左侧面板 — 选课名单
    # ------------------------------------------------------------------
    def _load_enrollment_panel(self) -> None:
        """刷新左侧面板的选课名单区域。"""
        if self._current_teaching_id is None:
            self.lbl_enrollment_summary.setText("—")
            self.list_enrolled_left.clear()
            return

        try:
            enrolled = self._teacher_svc.get_enrollment_detail(self._current_teaching_id)
            waiting  = self._teacher_svc.get_waiting_list(self._current_teaching_id)
        except Exception:  # noqa: BLE001
            self.lbl_enrollment_summary.setText("加载失败")
            return

        t = next(
            (x for x in self._teachings if x["teaching_id"] == self._current_teaching_id),
            {},
        )
        max_count = int(t.get("max_count") or 0)
        waiting_count = len(waiting)
        summary = f"已选：{len(enrolled)} / {max_count}"
        if waiting_count:
            summary += f"  候补：{waiting_count}"
        self.lbl_enrollment_summary.setText(summary)

        self.list_enrolled_left.clear()
        for r in enrolled:
            self.list_enrolled_left.addItem(
                f"{r.get('username', '')}  {r.get('real_name', '')}"
            )
        if waiting_count:
            self.list_enrolled_left.addItem("── 候补名单 ──")
            for r in waiting:
                item = QListWidgetItem(
                    f"[{r.get('queue_no', '')}] {r.get('username', '')}  {r.get('real_name', '')}"
                )
                item.setForeground(QBrush(QColor("#7D6608")))
                self.list_enrolled_left.addItem(item)
