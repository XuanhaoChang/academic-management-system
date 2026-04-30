from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
)


class EvaluationDialog(QDialog):
    def __init__(self, course_title: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("课程评教")
        self.resize(460, 300)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(course_title))
        layout.addWidget(QLabel("评分（1-100）"))

        self.score = QSpinBox()
        self.score.setRange(1, 100)
        self.score.setValue(85)
        layout.addWidget(self.score)

        layout.addWidget(QLabel("评语"))
        self.comment = QTextEdit()
        self.comment.setPlaceholderText("请输入评语（可选）")
        layout.addWidget(self.comment)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

