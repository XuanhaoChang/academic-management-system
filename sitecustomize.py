from __future__ import annotations


def _patch_selection_service() -> None:
    try:
        from services.student_selection_patch import apply_selection_patch

        apply_selection_patch()
    except Exception:
        return


_patch_selection_service()
