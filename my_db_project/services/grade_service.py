"""GradeService — [组员A] 成绩业务逻辑层

遵守规约：
  - Service 层只抛出异常，不 return False，不 print。
  - 数据操作通过 DBManager 执行，使用参数化查询。
"""
from __future__ import annotations

from core.constants import score_to_gpa
from core.db_manager import DBManager
from core.exceptions import BusinessError, ValidationError
from core.logger import AuditLogger
from core.session import Session


class GradeService:
    # ------------------------------------------------------------------
    # 成绩录入
    # ------------------------------------------------------------------
    def batch_enter_grades(
        self,
        teaching_id: int,
        grade_dict: dict[int, float],
    ) -> int:
        """批量录入/更新成绩（UPSERT）。

        Args:
            teaching_id: 授课安排 ID。
            grade_dict:  {student_id: score}，score 为百分制 0-100。

        Returns:
            实际写入/更新的条数。

        Raises:
            ValidationError: 成绩数据为空或分数超出范围。
        """
        if not grade_dict:
            raise ValidationError("成绩数据为空，没有可提交的成绩。")

        tasks: list[tuple[str, tuple]] = []
        for student_id, score in grade_dict.items():
            if not (0.0 <= score <= 100.0):
                raise ValidationError(
                    f"成绩必须在 0~100 之间，当前值: {score}（学生 ID={student_id}）"
                )
            upsert_sql = """
                INSERT INTO edu_grades
                    (student_id, teaching_id, score)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    score        = VALUES(score),
                    is_deleted   = 0
            """
            tasks.append((upsert_sql, (student_id, teaching_id, score)))

        DBManager.exec_transaction(tasks)

        uid = Session.current_user.id if Session.current_user else None
        AuditLogger.log_action(
            uid,
            "BATCH_ENTER_GRADES",
            f"teaching_id={teaching_id}, count={len(tasks)}",
        )
        return len(tasks)

    # ------------------------------------------------------------------
    # 绩点计算
    # ------------------------------------------------------------------
    def calculate_gpa(self, student_id: int) -> float:
        """计算学生的加权平均绩点（4.0 制）。

        Args:
            student_id: sys_users.id

        Returns:
            加权 GPA，保留两位小数；无成绩时返回 0.0。
        """
        sql = """
            SELECT g.score, c.credits
            FROM edu_grades   g
            JOIN edu_teaching t ON g.teaching_id = t.id AND t.is_deleted = 0
            JOIN edu_courses  c ON t.course_id   = c.id AND c.is_deleted = 0
            WHERE g.student_id  = %s
              AND g.is_deleted  = 0
                            AND g.score IS NOT NULL
        """
        rows = DBManager.exec_query(sql, (student_id,))
        if not rows:
            return 0.0

        total_credits = sum(float(r["credits"]) for r in rows)
        if total_credits == 0:
            return 0.0

        weighted = sum(float(score_to_gpa(float(r["score"]))[0]) * float(r["credits"]) for r in rows)
        return round(weighted / total_credits, 2)

    # ------------------------------------------------------------------
    # 查询
    # ------------------------------------------------------------------
    def get_teaching_grades(self, teaching_id: int) -> list[dict]:
        """获取授课班级所有学生的成绩（含未录入成绩的学生）。

        返回字段: student_id, username, real_name,
                  grade_id, score, gpa_point, grade_letter, is_passed
        """
        sql = """
            SELECT
                u.id         AS student_id,
                u.username,
                u.real_name,
                g.id         AS grade_id,
                g.score,
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
                CASE WHEN g.score >= 60 THEN 1 ELSE 0 END AS is_passed
            FROM sys_users u
            LEFT JOIN edu_grades g
                ON g.student_id  = u.id
               AND g.teaching_id = %s
               AND g.is_deleted  = 0
            WHERE u.role_id    = 3
              AND u.is_deleted = 0
            ORDER BY u.real_name
        """
        return DBManager.exec_query(sql, (teaching_id,))

    def get_my_teachings(self, teacher_id: int) -> list[dict]:
        """获取教师的所有授课安排（含课程信息）。

        返回字段: teaching_id, course_name, course_code, credits,
                  classroom, timeslot, semester, enrolled_count, max_count, status
        """
        sql = """
            SELECT
                t.id            AS teaching_id,
                c.course_name,
                c.course_code,
                c.credits,
                t.classroom,
                t.timeslot,
                t.semester,
                t.enrolled_count,
                t.max_count,
                t.status,
                t.is_submitted
            FROM edu_teaching t
            JOIN edu_courses  c ON t.course_id = c.id AND c.is_deleted = 0
            WHERE t.teacher_id = %s
              AND t.is_deleted = 0
            ORDER BY t.semester DESC, c.course_name
        """
        return DBManager.exec_query(sql, (teacher_id,))

    # ------------------------------------------------------------------
    # [组员A 扩展] 卷面成绩录入（自动计算最终成绩）
    # ------------------------------------------------------------------
    def batch_enter_exam_scores(
        self,
        teaching_id: int,
        exam_dict: dict[int, float],
    ) -> int:
        """批量录入卷面成绩，自动合并平时分计算最终成绩（UPSERT）。

        成绩公式: final_score = exam_score × 0.7 + daily_score（0~30）
        若该学生无平时分记录，daily_score 默认为 0。

        Args:
            teaching_id: 授课安排 ID。
            exam_dict:   {student_id: exam_score}，exam_score 为百分制 0-100。

        Returns:
            实际写入/更新的条数。

        Raises:
            ValidationError: 数据为空或分数超出范围。
        """
        if not exam_dict:
            raise ValidationError("卷面成绩数据为空，没有可提交的成绩。")

        # 查询该班级所有学生的平时分
        daily_sql = """
            SELECT student_id, daily_score
            FROM view_daily_score
            WHERE teaching_id = %s
        """
        daily_rows = DBManager.exec_query(daily_sql, (teaching_id,))
        daily_map: dict[int, float] = {
            int(r["student_id"]): float(r["daily_score"] or 0)
            for r in daily_rows
        }

        tasks: list[tuple[str, tuple]] = []
        for student_id, exam_score in exam_dict.items():
            if exam_score is None:
                continue
            try:
                exam_score = float(exam_score)
            except (TypeError, ValueError):
                continue
            if not (0.0 <= exam_score <= 100.0):
                raise ValidationError(
                    f"卷面成绩必须在 0~100 之间，当前值: {exam_score}（学生 ID={student_id}）"
                )
            daily_score = daily_map.get(int(student_id), 0.0)
            final_score = round(exam_score * 0.7 + daily_score, 2)
            upsert_sql = """
                INSERT INTO edu_grades
                    (student_id, teaching_id, exam_score, score)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    exam_score   = VALUES(exam_score),
                    score        = VALUES(score),
                    is_deleted   = 0
            """
            tasks.append((
                upsert_sql,
                (student_id, teaching_id, exam_score, final_score)
            ))

        if tasks:
            DBManager.exec_transaction(tasks)

        uid = Session.current_user.id if Session.current_user else None
        AuditLogger.log_action(
            uid,
            "BATCH_ENTER_GRADES",
            f"teaching_id={teaching_id}, exam_scores_count={len(tasks)}",
        )
        return len(tasks)

    def get_teaching_grades_with_exam(self, teaching_id: int) -> list[dict]:
        """获取授课班级学生成绩（含卷面分、平时分、最终分）。

        学生范围 = 已选课（stu_selection）∪ 已有成绩记录（edu_grades），两者取并集。
        返回字段: student_id, username, real_name,
                  exam_score, daily_score, score(最终), gpa_point, grade_letter, is_passed
        """
        sql = """
            SELECT
                u.id          AS student_id,
                u.username,
                u.real_name,
                g.exam_score,
                g.score,
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
                CASE WHEN g.score >= 60 THEN 1 ELSE 0 END AS is_passed,
                COALESCE(ds.daily_score, 0)     AS daily_score,
                COALESCE(ds.completion_rate, 0) AS completion_rate
            FROM sys_users u
            LEFT JOIN edu_grades g
                ON g.student_id  = u.id
               AND g.teaching_id = %s
               AND g.is_deleted  = 0
            LEFT JOIN view_daily_score ds
                ON ds.student_id  = u.id
               AND ds.teaching_id = %s
            WHERE u.role_id    = 3
              AND u.is_deleted = 0
              AND (
                    g.id IS NOT NULL
                    OR EXISTS (
                        SELECT 1
                        FROM stu_selection ss
                        JOIN edu_teaching  et ON et.id = %s AND et.is_deleted = 0
                        WHERE ss.student_id = u.id
                          AND ss.teaching_id = et.id
                                                    AND ss.deleted_at = 0
                    )
              )
            ORDER BY u.real_name
        """
        return DBManager.exec_query(sql, (teaching_id, teaching_id, teaching_id))

    # ------------------------------------------------------------------
    # 归档
    # ------------------------------------------------------------------
    def archive_semester_grades(self, semester: str) -> int:
        """调用存储过程将指定学期成绩归档至 edu_archives。

        Returns:
            归档的成绩条数。

        Raises:
            ValidationError: 学期格式为空。
            BusinessError:   存储过程执行失败。
        """
        if not semester or not semester.strip():
            raise ValidationError("学期参数不能为空（格式示例: 2024-1）")

        with DBManager.transaction() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("CALL proc_archive_grades(%s)", (semester.strip(),))
                row = cursor.fetchone()
                # 消费剩余结果集，防止 Commands out of sync
                while cursor.nextset():
                    pass
            finally:
                cursor.close()

        uid = Session.current_user.id if Session.current_user else None
        archived = int(row["archived_rows"]) if row and row.get("archived_rows") is not None else 0
        AuditLogger.log_action(
            uid,
            "ARCHIVE_GRADES",
            f"semester={semester}, archived_rows={archived}",
        )
        return archived
