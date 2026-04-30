from __future__ import annotations

from datetime import datetime
from typing import Any

import mysql.connector

from core.db_manager import DBManager
from core.exceptions import BusinessError


class StudentService:
    @staticmethod
    def current_semester() -> str:
        rows = DBManager.exec_query(
            """
            SELECT config_value
            FROM sys_config
            WHERE config_key = 'current_semester'
              AND is_deleted = 0
            LIMIT 1
            """
        )
        if rows and rows[0].get("config_value"):
            return str(rows[0]["config_value"])

        now = datetime.now()
        if 2 <= now.month <= 6:
            return f"{now.year}-1"
        return f"{now.year}-2"

    @staticmethod
    def get_student_profile(student_id: int) -> dict[str, Any]:
        rows = DBManager.exec_query(
            """
            SELECT
                u.id,
                u.username,
                u.real_name,
                d.dept_name,
                m.major_name,
                si.grade_year,
                si.class_name
            FROM sys_users u
            LEFT JOIN base_dept d ON d.id = u.dept_id AND d.is_deleted = 0
            LEFT JOIN base_major m ON m.id = u.major_id AND m.is_deleted = 0
            LEFT JOIN stu_info si ON si.student_id = u.id AND si.is_deleted = 0
            WHERE u.id = %s
              AND u.role_id = 3
              AND u.is_deleted = 0
            LIMIT 1
            """,
            (student_id,),
        )
        return rows[0] if rows else {}

    @staticmethod
    def major_rank_by_gpa(student_id: int) -> dict[str, Any]:
        rows = DBManager.exec_query(
            """
            SELECT r.rank_no, r.total_in_major
            FROM (
                SELECT
                    u.id,
                    ROW_NUMBER() OVER (ORDER BY COALESCE(g.weighted_gpa, 0) DESC, u.id ASC) AS rank_no,
                    COUNT(*) OVER () AS total_in_major
                FROM sys_users u
                LEFT JOIN view_student_gpa g ON g.student_id = u.id
                WHERE u.role_id = 3
                  AND u.is_deleted = 0
                  AND u.major_id = (
                      SELECT major_id
                      FROM sys_users
                      WHERE id = %s
                      LIMIT 1
                  )
            ) r
            WHERE r.id = %s
            LIMIT 1
            """,
            (student_id, student_id),
        )
        return rows[0] if rows else {"rank_no": None, "total_in_major": 0}

    @staticmethod
    def list_available_courses(student_id: int, semester: str) -> list[dict[str, Any]]:
        return DBManager.exec_query(
            """
            SELECT
                t.id AS teaching_id,
                c.id AS course_id,
                c.course_code,
                c.course_name,
                c.credits,
                t.classroom,
                t.timeslot,
                t.semester,
                t.status,
                t.enrolled_count,
                t.max_count,
                u.real_name AS teacher_name,
                CASE
                    WHEN EXISTS (
                        SELECT 1
                        FROM stu_selection s2
                        WHERE s2.student_id = %s
                          AND s2.teaching_id = t.id
                                                    AND s2.deleted_at = 0
                    ) THEN 1 ELSE 0
                END AS already_selected
            FROM edu_teaching t
            JOIN edu_courses c ON c.id = t.course_id AND c.is_deleted = 0
            JOIN sys_users u ON u.id = t.teacher_id AND u.is_deleted = 0
                        JOIN sys_users su ON su.id = %s AND su.role_id = 3 AND su.is_deleted = 0
                        LEFT JOIN stu_info si ON si.student_id = su.id AND si.is_deleted = 0
            WHERE t.semester = %s
              AND t.is_deleted = 0
                            AND c.dept_id = su.dept_id
                            AND (
                                        si.grade_year IS NULL
                                        OR CAST(SUBSTRING_INDEX(t.semester, '-', 1) AS UNSIGNED) = si.grade_year
                                    )
            ORDER BY c.course_code, t.id DESC
            """,
                        (student_id, student_id, semester),
        )

    @staticmethod
    def list_selected_courses(student_id: int, semester: str) -> list[dict[str, Any]]:
        return DBManager.exec_query(
            """
            SELECT
                s.teaching_id,
                c.id AS course_id,
                c.course_code,
                c.course_name,
                c.credits,
                t.classroom,
                t.timeslot,
                t.semester,
                t.status,
                t.enrolled_count,
                t.max_count,
                u.real_name AS teacher_name
            FROM stu_selection s
                        JOIN edu_teaching t ON t.id = s.teaching_id AND t.is_deleted = 0
                        JOIN edu_courses c ON c.id = t.course_id AND c.is_deleted = 0
            JOIN sys_users u ON u.id = t.teacher_id AND u.is_deleted = 0
            WHERE s.student_id = %s
                            AND t.semester = %s
                            AND s.deleted_at = 0
            ORDER BY c.course_code
            """,
                        (student_id, semester),
        )

    @staticmethod
    def list_waiting(student_id: int, semester: str) -> list[dict[str, Any]]:
        return DBManager.exec_query(
            """
            SELECT
                w.teaching_id,
                w.queue_no,
                c.id AS course_id,
                c.course_code,
                c.course_name,
                u.real_name AS teacher_name,
                t.classroom,
                t.timeslot,
                t.semester
            FROM stu_waiting_list w
                        JOIN edu_teaching t ON t.id = w.teaching_id AND t.is_deleted = 0
                        JOIN edu_courses c ON c.id = t.course_id AND c.is_deleted = 0
            JOIN sys_users u ON u.id = t.teacher_id AND u.is_deleted = 0
            WHERE w.student_id = %s
                            AND t.semester = %s
                            AND w.deleted_at = 0
            ORDER BY w.queue_no
            """,
                        (student_id, semester),
        )

    @staticmethod
    def list_grades_current(student_id: int, semester: str) -> list[dict[str, Any]]:
        return DBManager.exec_query(
            """
            SELECT
                c.id AS course_id,
                c.course_code,
                c.course_name,
                c.credits,
                g.exam_score,
                ds.daily_score AS daily_score,
                g.score AS final_score,
                CASE
                    WHEN g.score IS NULL THEN NULL
                    WHEN g.score >= 90 THEN 4.0
                    WHEN g.score >= 80 THEN 3.0
                    WHEN g.score >= 70 THEN 2.0
                    WHEN g.score >= 60 THEN 1.0
                    ELSE 0.0
                END AS gpa_point,
                CASE
                    WHEN g.score IS NULL THEN NULL
                    WHEN g.score >= 90 THEN 'A'
                    WHEN g.score >= 80 THEN 'B'
                    WHEN g.score >= 70 THEN 'C'
                    WHEN g.score >= 60 THEN 'D'
                    ELSE 'F'
                END AS grade_letter,
                CASE
                    WHEN g.score IS NULL THEN 0
                    WHEN g.score >= 60 THEN 1
                    ELSE 0
                END AS is_passed
            FROM stu_selection s
            JOIN edu_teaching t ON t.id = s.teaching_id AND t.is_deleted = 0
            JOIN edu_courses c ON c.id = t.course_id AND c.is_deleted = 0
            LEFT JOIN edu_grades g ON g.student_id = s.student_id
                                  AND g.teaching_id = t.id
                                  AND g.is_deleted = 0
            LEFT JOIN view_daily_score ds ON ds.student_id = s.student_id
                                        AND ds.teaching_id = t.id
            WHERE s.student_id = %s
                            AND t.semester = %s
                            AND s.deleted_at = 0
            ORDER BY c.course_code
            """,
                        (student_id, semester),
        )

    @staticmethod
    def list_grades_archived(student_id: int) -> list[dict[str, Any]]:
        return DBManager.exec_query(
            """
            SELECT
                t.semester,
                c.id AS course_id,
                c.course_code,
                c.course_name,
                c.credits,
                a.score AS final_score,
                CASE
                    WHEN a.score IS NULL THEN NULL
                    WHEN a.score >= 90 THEN 4.0
                    WHEN a.score >= 80 THEN 3.0
                    WHEN a.score >= 70 THEN 2.0
                    WHEN a.score >= 60 THEN 1.0
                    ELSE 0.0
                END AS gpa_point,
                CASE
                    WHEN a.score IS NULL THEN NULL
                    WHEN a.score >= 90 THEN 'A'
                    WHEN a.score >= 80 THEN 'B'
                    WHEN a.score >= 70 THEN 'C'
                    WHEN a.score >= 60 THEN 'D'
                    ELSE 'F'
                END AS grade_letter,
                CASE
                    WHEN a.score IS NULL THEN 0
                    WHEN a.score >= 60 THEN 1
                    ELSE 0
                END AS is_passed
            FROM edu_archives a
            JOIN edu_teaching t ON t.id = a.teaching_id
            JOIN edu_courses c ON c.id = t.course_id AND c.is_deleted = 0
            WHERE a.student_id = %s
              AND a.is_deleted = 0
            ORDER BY t.semester DESC, c.course_code
            """,
            (student_id,),
        )

    @staticmethod
    def student_rank_in_class(student_id: int, course_id: int, semester: str) -> dict[str, Any]:
        rows = DBManager.exec_query(
            """
            SELECT r.rank_in_class, r.score
            FROM view_class_ranking r
            JOIN edu_teaching t ON t.id = r.teaching_id AND t.is_deleted = 0
            WHERE r.student_id = %s
              AND t.course_id = %s
              AND t.semester = %s
            LIMIT 1
            """,
            (student_id, course_id, semester),
        )
        return rows[0] if rows else {}

    @staticmethod
    def gpa_current(student_id: int) -> dict[str, Any]:
        rows = DBManager.exec_query(
            """
            SELECT weighted_gpa, total_credits, course_count
            FROM view_student_gpa
            WHERE student_id = %s
            LIMIT 1
            """,
            (student_id,),
        )
        return rows[0] if rows else {"weighted_gpa": 0.0, "total_credits": 0.0, "course_count": 0}

    @staticmethod
    def list_upcoming_exams(student_id: int, semester: str) -> list[dict[str, Any]]:
        try:
            return DBManager.exec_query(
                """
                SELECT
                    e.course_id,
                    c.course_code,
                    c.course_name,
                    e.exam_date,
                    e.start_time,
                    e.end_time,
                    e.exam_room,
                    COALESCE(r.status, 'NONE') AS defer_status,
                    CASE WHEN g.id IS NOT NULL THEN 1 ELSE 0 END AS has_grade
                FROM stu_selection s
                                JOIN edu_teaching t ON t.id = s.teaching_id
                                                                        AND t.semester = %s
                                                                        AND t.is_deleted = 0
                                JOIN stu_exam_schedule e ON e.course_id = t.course_id
                                        AND e.semester = %s
                                        AND e.is_deleted = 0
                JOIN edu_courses c ON c.id = e.course_id AND c.is_deleted = 0
                LEFT JOIN stu_exam_defer_req r ON r.student_id = s.student_id
                                                                                            AND r.course_id = t.course_id
                                              AND r.semester = e.semester
                                              AND r.is_deleted = 0
                LEFT JOIN edu_grades g ON g.student_id = s.student_id
                                      AND g.teaching_id = t.id
                                      AND g.is_deleted = 0
                WHERE s.student_id = %s
                                    AND s.deleted_at = 0
                ORDER BY has_grade ASC, e.exam_date, e.start_time
                """,
                                (semester, semester, student_id),
            )
        except mysql.connector.Error as exc:
            # 兼容旧库：尚未执行 08_student_ext.sql 时，stu_exam_defer_req 可能不存在
            if getattr(exc, "errno", None) != 1146:
                raise
            return DBManager.exec_query(
                """
                SELECT
                    e.course_id,
                    c.course_code,
                    c.course_name,
                    e.exam_date,
                    e.start_time,
                    e.end_time,
                    e.exam_room,
                    'NONE' AS defer_status,
                    0 AS has_grade
                FROM stu_selection s
                                JOIN edu_teaching t ON t.id = s.teaching_id
                                                                        AND t.semester = %s
                                                                        AND t.is_deleted = 0
                                JOIN stu_exam_schedule e ON e.course_id = t.course_id
                                        AND e.semester = %s
                                        AND e.is_deleted = 0
                JOIN edu_courses c ON c.id = e.course_id AND c.is_deleted = 0
                WHERE s.student_id = %s
                                    AND s.deleted_at = 0
                ORDER BY e.exam_date, e.start_time
                """,
                                (semester, semester, student_id),
            )

    @staticmethod
    def submit_exam_defer_request(student_id: int, course_id: int, semester: str) -> bool:
        try:
            exists = DBManager.exec_query(
                """
                SELECT id
                FROM stu_exam_defer_req
                WHERE student_id = %s
                  AND course_id = %s
                  AND semester = %s
                  AND is_deleted = 0
                LIMIT 1
                """,
                (student_id, course_id, semester),
            )
            if exists:
                return False

            DBManager.exec_query(
                """
                INSERT INTO stu_exam_defer_req(student_id, course_id, semester, reason, status, is_deleted)
                VALUES (%s, %s, %s, %s, 'PENDING', 0)
                """,
                (student_id, course_id, semester, "自动申请"),
                fetch=False,
            )
            return True
        except mysql.connector.Error as exc:
            if getattr(exc, "errno", None) == 1146:
                raise BusinessError("缓考功能未初始化，请先执行 sql/08_student_ext.sql") from exc
            raise

    @staticmethod
    def cancel_exam_defer_request(student_id: int, course_id: int, semester: str) -> bool:
        try:
            rows = DBManager.exec_query(
                """
                SELECT id
                FROM stu_exam_defer_req
                WHERE student_id = %s
                  AND course_id = %s
                  AND semester = %s
                  AND is_deleted = 0
                LIMIT 1
                """,
                (student_id, course_id, semester),
            )
            if not rows:
                return False
            DBManager.exec_query(
                """
                DELETE FROM stu_exam_defer_req
                WHERE id = %s
                LIMIT 1
                """,
                (rows[0]["id"],),
                fetch=False,
            )
            return True
        except mysql.connector.Error as exc:
            if getattr(exc, "errno", None) == 1146:
                raise BusinessError("缓考功能未初始化，请先执行 sql/08_student_ext.sql") from exc
            raise

    @staticmethod
    def search_course_snapshot(student_id: int, semester: str, keyword: str) -> dict[str, Any]:
        kw = f"%{keyword.strip()}%"
        rows = DBManager.exec_query(
            """
            SELECT
                COUNT(*) AS total_match,
                SUM(CASE WHEN t.status='OPEN' THEN 1 ELSE 0 END) AS open_count,
                SUM(CASE WHEN t.status='FULL' THEN 1 ELSE 0 END) AS full_count,
                ROUND(AVG(t.enrolled_count), 2) AS avg_enrolled
            FROM edu_teaching t
            JOIN edu_courses c ON c.id=t.course_id AND c.is_deleted=0
            LEFT JOIN sys_users u ON u.id=t.teacher_id AND u.is_deleted=0
            WHERE t.semester=%s
              AND t.is_deleted=0
              AND (
                    c.course_code LIKE %s
                 OR c.course_name LIKE %s
                 OR COALESCE(u.real_name,'') LIKE %s
                 OR COALESCE(t.classroom,'') LIKE %s
              )
            """,
            (semester, kw, kw, kw, kw),
        )
        return rows[0] if rows else {"total_match": 0, "open_count": 0, "full_count": 0, "avg_enrolled": 0}

    @staticmethod
    def list_evaluations(student_id: int, semester: str) -> dict[int, dict[str, Any]]:
        rows = DBManager.exec_query(
            """
            SELECT course_id, eval_score, eval_comment
            FROM stu_evaluation
            WHERE student_id = %s
              AND semester = %s
              AND is_deleted = 0
            """,
            (student_id, semester),
        )
        result: dict[int, dict[str, Any]] = {}
        for r in rows:
            cid = int(r.get("course_id") or 0)
            if cid:
                result[cid] = {
                    "eval_score": r.get("eval_score"),
                    "eval_comment": r.get("eval_comment"),
                }
        return result

    @staticmethod
    def reset_student_selection(student_id: int, semester: str) -> None:
        try:
            with DBManager.transaction() as conn:
                cursor = conn.cursor(dictionary=True)
                try:
                    cursor.execute(
                        """
                        UPDATE stu_waiting_list
                        SET deleted_at = UNIX_TIMESTAMP(CURRENT_TIMESTAMP(3))*1000,
                            is_deleted = 1
                        WHERE student_id = %s
                          AND deleted_at = 0
                        """,
                        (student_id,),
                    )
                    cursor.execute(
                        """
                        UPDATE stu_selection
                        SET deleted_at = UNIX_TIMESTAMP(CURRENT_TIMESTAMP(3))*1000,
                            is_deleted = 1
                        WHERE student_id = %s
                          AND deleted_at = 0
                        """,
                        (student_id,),
                    )
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
                        WHERE t.semester = %s
                          AND t.is_deleted = 0
                        """,
                        (semester,),
                    )
                finally:
                    cursor.close()
        except mysql.connector.Error as exc:
            raise BusinessError(f"刷新失败（重置选课数据）: {exc}") from exc

    @staticmethod
    def submit_evaluation(student_id: int, course_id: int, semester: str, score: int, comment: str) -> None:
        DBManager.exec_query(
            """
            INSERT INTO stu_evaluation(student_id, course_id, semester, eval_score, eval_comment, is_deleted)
            VALUES (%s, %s, %s, %s, %s, 0)
            ON DUPLICATE KEY UPDATE
                eval_score = VALUES(eval_score),
                eval_comment = VALUES(eval_comment),
                is_deleted = 0
            """,
            (student_id, course_id, semester, score, comment),
            fetch=False,
        )

