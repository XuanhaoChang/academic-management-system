"""
并发抢课调试脚本
"""
from __future__ import annotations

from threading import Thread

from core.db_manager import DBManager
from services.student_selection_impl import attempt_enroll_impl


class _Dummy:
    pass


def _get_course_id() -> int:
    rows = DBManager.exec_query(
        """
        SELECT c.id
        FROM edu_courses c
        JOIN edu_teaching t ON t.course_id = c.id AND t.is_deleted = 0
        JOIN sys_config sc ON sc.config_key='current_semester' AND sc.config_value=t.semester
        WHERE c.is_deleted = 0
        ORDER BY c.id
        LIMIT 1
        """
    )
    if not rows:
        raise RuntimeError("未找到可演示课程")
    return int(rows[0]["id"])


def _worker(student_id: int, course_id: int) -> None:
    try:
        r = attempt_enroll_impl(_Dummy(), student_id, course_id)
        print(f"[student={student_id}] {r}")
    except Exception as e:  # noqa: BLE001
        print(f"[student={student_id}] error: {e}")


def main() -> None:
    course_id = _get_course_id()
    t1 = Thread(target=_worker, args=(1, course_id))
    t2 = Thread(target=_worker, args=(2, course_id))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    print("[DONE] 并发演示结束")


if __name__ == "__main__":
    main()
