from __future__ import annotations


def _patch_main_window_student_entry() -> None:
    try:
        from views.main_window import MainWindow
        from views.student.enrollment import EnrollmentWidget

        original = MainWindow._build_placeholder

        def _patched(self, text: str):
            if "学生功能由组员B实现" in text:
                return EnrollmentWidget()
            return original(self, text)

        MainWindow._build_placeholder = _patched  # type: ignore[assignment]
    except Exception:
        return


def _patch_selection_service() -> None:
    try:
        from services.student_selection_patch import apply_selection_patch

        apply_selection_patch()
    except Exception:
        return


_patch_selection_service()
_patch_main_window_student_entry()

