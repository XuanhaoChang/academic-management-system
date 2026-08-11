from __future__ import annotations

from services.selection_service import SelectionService
from services.student_selection_impl import attempt_enroll_impl, cancel_waiting_impl, drop_course_impl


def apply_selection_patch() -> None:
    SelectionService.attempt_enroll = attempt_enroll_impl  # type: ignore[method-assign]
    SelectionService.drop_course = drop_course_impl  # type: ignore[method-assign]
    SelectionService.cancel_waiting = cancel_waiting_impl  # type: ignore[method-assign]

