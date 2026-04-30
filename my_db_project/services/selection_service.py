from __future__ import annotations

from typing import Any

from core.exceptions import BusinessError


class SelectionService:
    """
    Student selection service entry.

    Real logic is monkey-patched at runtime by:
    services.student_selection_patch.apply_selection_patch()
    """

    def attempt_enroll(self, student_id: int, teaching_id: int) -> dict[str, Any]:
        raise BusinessError("选课服务未初始化，请重启后重试。")

    def drop_course(self, student_id: int, teaching_id: int) -> dict[str, Any]:
        raise BusinessError("退课服务未初始化，请重启后重试。")

    def cancel_waiting(self, student_id: int, teaching_id: int) -> dict[str, Any]:
        raise BusinessError("取消候补服务未初始化，请重启后重试。")

