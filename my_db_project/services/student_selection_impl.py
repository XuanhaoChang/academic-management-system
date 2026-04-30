from __future__ import annotations

from typing import Any

import mysql.connector

from core.db_manager import DBManager
from core.exceptions import BusinessError, ValidationError
from core.logger import AuditLogger
from core.session import Session
from services.validator import CourseValidator


def _uid() -> int | None:
    return Session.current_user.id if Session.current_user else None


def _resolve_teaching(teaching_id: int) -> dict[str, Any]:
    rows = DBManager.exec_query(
        """
        SELECT t.id, t.course_id, t.semester, t.max_count, t.enrolled_count, t.status
        FROM edu_teaching t
        WHERE t.id = %s AND t.is_deleted = 0
        LIMIT 1
        """,
        (teaching_id,),
    )
    if not rows:
        raise ValidationError("教学班不存在或已删除。")
    return rows[0]


def _refresh_teaching_counter(cursor: Any, teaching_id: int) -> None:
    cursor.execute(
        """
        UPDATE edu_teaching t
        SET t.enrolled_count = (
                SELECT COUNT(*)
                FROM stu_selection s
                WHERE s.teaching_id = t.id
                                    AND s.deleted_at = 0
            ),
            t.status = CASE
                WHEN (
                    SELECT COUNT(*)
                    FROM stu_selection s
                    WHERE s.teaching_id = t.id
                                            AND s.deleted_at = 0
                ) >= t.max_count THEN 'FULL'
                ELSE 'OPEN'
            END
        WHERE t.id = %s
        """,
        (teaching_id,),
    )


def attempt_enroll_impl(self, student_id: int, teaching_id: int) -> dict[str, Any]:
    _ = self
    if not student_id or not teaching_id:
        raise ValidationError("参数非法。")

    teaching = _resolve_teaching(teaching_id)
    semester = str(teaching.get("semester") or "")
    course_id = int(teaching.get("course_id") or 0)

    validator = CourseValidator()
    if semester:
        validator.check_student_scope(student_id, teaching_id)
        validator.check_prerequisite(student_id, course_id)
        validator.check_time_conflict(student_id, teaching_id)
        validator.check_exam_conflict(student_id, teaching_id)

    try:
        with DBManager.transaction() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute(
                    """
                    SELECT id FROM stu_selection
                    WHERE student_id=%s AND teaching_id=%s AND deleted_at=0
                    LIMIT 1
                    """,
                    (student_id, teaching_id),
                )
                if cursor.fetchone():
                    raise ValidationError("你已选过该教学班。")

                cursor.execute(
                    "CALL proc_attempt_enroll(%s, %s, @code, @msg)",
                    (student_id, teaching_id),
                )
                while cursor.nextset():
                    pass
                cursor.execute("SELECT @code AS code, @msg AS msg")
                result = cursor.fetchone() or {}
                code = int(result.get("code") or 500)
                msg = str(result.get("msg") or "选课失败")

                if code == 200:
                    cursor.execute(
                        """
                        UPDATE stu_waiting_list
                        SET deleted_at = UNIX_TIMESTAMP(CURRENT_TIMESTAMP(3))*1000,
                            is_deleted = 1
                        WHERE student_id=%s
                          AND teaching_id=%s
                          AND deleted_at=0
                        """,
                        (student_id, teaching_id),
                    )
                    if semester:
                        cursor.execute(
                            """
                            DELETE FROM stu_evaluation
                            WHERE student_id=%s
                              AND course_id=%s
                              AND semester=%s
                            """,
                            (student_id, course_id, semester),
                        )
                    _refresh_teaching_counter(cursor, teaching_id)
                    AuditLogger.log_action(_uid(), "ENROLL_SUCCESS", f"student={student_id}, teaching={teaching_id}")
                    return {"code": 200, "msg": msg}

                if code == 409:
                    cursor.execute(
                        """
                        SELECT id
                        FROM stu_waiting_list
                        WHERE student_id=%s AND teaching_id=%s AND deleted_at=0
                        LIMIT 1
                        """,
                        (student_id, teaching_id),
                    )
                    if not cursor.fetchone():
                        cursor.execute(
                            """
                            SELECT COALESCE(MAX(queue_no),0)+1 AS next_no
                            FROM stu_waiting_list
                            WHERE teaching_id=%s AND deleted_at=0
                            """,
                            (teaching_id,),
                        )
                        nxt = cursor.fetchone() or {}
                        qno = int(nxt.get("next_no") or 1)
                        cursor.execute(
                            """
                            INSERT INTO stu_waiting_list(student_id, teaching_id, queue_no, deleted_at, is_deleted)
                            VALUES(%s,%s,%s,0,0)
                            """,
                            (student_id, teaching_id, qno),
                        )
                    AuditLogger.log_action(_uid(), "ENROLL_WAITING", f"student={student_id}, teaching={teaching_id}")
                    return {"code": 409, "msg": "课程已满，已加入候补队列"}

                raise BusinessError(msg)
            finally:
                cursor.close()
    except mysql.connector.Error as exc:
        raise BusinessError(f"数据库错误（选课）: {exc}") from exc


def drop_course_impl(self, student_id: int, teaching_id: int) -> dict[str, Any]:
    _ = self
    if not student_id or not teaching_id:
        raise ValidationError("参数非法。")

    promoted_student: int | None = None
    try:
        with DBManager.transaction() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute(
                    """
                    SELECT id
                    FROM stu_selection
                    WHERE student_id=%s AND teaching_id=%s AND deleted_at=0
                    LIMIT 1
                    """,
                    (student_id, teaching_id),
                )
                selected_row = cursor.fetchone()
                if not selected_row:
                    raise ValidationError("当前教学班不在已选列表中。")

                cursor.execute(
                    """
                    UPDATE stu_selection
                    SET deleted_at = UNIX_TIMESTAMP(CURRENT_TIMESTAMP(3))*1000,
                        is_deleted = 1
                    WHERE id=%s AND deleted_at=0
                    """,
                    (selected_row["id"],),
                )

                _refresh_teaching_counter(cursor, teaching_id)

                while True:
                    cursor.execute(
                        """
                        SELECT id, student_id
                        FROM stu_waiting_list
                        WHERE teaching_id=%s
                                                    AND deleted_at=0
                        ORDER BY queue_no ASC, id ASC
                        LIMIT 1
                        FOR UPDATE
                        """,
                        (teaching_id,),
                    )
                    next_wait = cursor.fetchone()
                    if not next_wait:
                        break

                    candidate = int(next_wait["student_id"])
                    cursor.execute(
                        """
                        SELECT id
                        FROM stu_selection
                        WHERE student_id=%s
                          AND teaching_id=%s
                          AND deleted_at=0
                        LIMIT 1
                        """,
                        (candidate, teaching_id),
                    )
                    exists = cursor.fetchone()
                    if exists:
                        cursor.execute(
                            """
                            UPDATE stu_waiting_list
                            SET deleted_at = UNIX_TIMESTAMP(CURRENT_TIMESTAMP(3))*1000,
                                is_deleted = 1
                            WHERE id=%s AND deleted_at=0
                            """,
                            (next_wait["id"],),
                        )
                        continue

                    cursor.execute(
                        """
                        INSERT INTO stu_selection(student_id, teaching_id, deleted_at, is_deleted)
                        VALUES(%s, %s, 0, 0)
                        """,
                        (candidate, teaching_id),
                    )
                    cursor.execute(
                        """
                        UPDATE stu_waiting_list
                        SET deleted_at = UNIX_TIMESTAMP(CURRENT_TIMESTAMP(3))*1000,
                            is_deleted = 1
                        WHERE id=%s AND deleted_at=0
                        """,
                        (next_wait["id"],),
                    )
                    promoted_student = candidate
                    break
                _refresh_teaching_counter(cursor, teaching_id)

            finally:
                cursor.close()
    except mysql.connector.Error as exc:
        raise BusinessError(f"数据库错误（退课）: {exc}") from exc

    AuditLogger.log_action(_uid(), "DROP_COURSE", f"student={student_id}, teaching={teaching_id}")
    if promoted_student is not None:
        return {"code": 200, "msg": f"退课成功，候补学生(id={promoted_student})已自动补位"}
    return {"code": 200, "msg": "退课成功"}


def cancel_waiting_impl(self, student_id: int, teaching_id: int) -> dict[str, Any]:
    _ = self
    if not student_id or not teaching_id:
        raise ValidationError("参数非法。")

    try:
        with DBManager.transaction() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute(
                    """
                    SELECT id
                    FROM stu_waiting_list
                    WHERE student_id=%s
                                            AND teaching_id=%s
                                            AND deleted_at=0
                    LIMIT 1
                    """,
                                        (student_id, teaching_id),
                )
                row = cursor.fetchone()
                if not row:
                                        raise ValidationError("当前教学班不在候补队列中。")

                cursor.execute(
                    """
                                        UPDATE stu_waiting_list
                                        SET deleted_at = UNIX_TIMESTAMP(CURRENT_TIMESTAMP(3))*1000,
                                                is_deleted = 1
                                        WHERE id=%s AND deleted_at=0
                    """,
                    (row["id"],),
                )
            finally:
                cursor.close()
    except mysql.connector.Error as exc:
        raise BusinessError(f"数据库错误（取消候补）: {exc}") from exc

    AuditLogger.log_action(_uid(), "CANCEL_WAITING", f"student={student_id}, teaching={teaching_id}")
    return {"code": 200, "msg": "已取消候补"}

