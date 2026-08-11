"""TeacherService — 教师端业务逻辑层

遵守规约：
  - 只抛出 ValidationError / BusinessError，不 return False，不 print。
  - 数据操作通过 DBManager 执行，使用参数化查询。
  - 每个变更操作在末尾调用 AuditLogger.log_action。
"""
from __future__ import annotations

from typing import Optional

import mysql.connector

from core.constants import ActionType
from core.db_manager import DBManager
from core.exceptions import BusinessError, ValidationError
from core.logger import AuditLogger
from core.session import Session
from models.analysis_dao import AnalysisDAO
from services.grade_service import GradeService


class TeacherService:
    # ------------------------------------------------------------------
    # 个人信息
    # ------------------------------------------------------------------
    def get_profile(self, teacher_id: int) -> dict:
        """返回教师的个人信息（含院系名称）。

        Raises:
            BusinessError: 教师不存在。
        """
        sql = """
            SELECT
                u.id,
                u.username,
                u.real_name,
                u.created_at,
                COALESCE(d.dept_name, '未分配') AS dept_name
            FROM sys_users u
            LEFT JOIN base_dept d ON d.id = u.dept_id AND d.is_deleted = 0
            WHERE u.id = %s AND u.is_deleted = 0
        """
        rows = DBManager.exec_query(sql, (teacher_id,))
        if not rows:
            raise BusinessError("教师账号不存在或已被删除")
        return rows[0]

    # ------------------------------------------------------------------
    # 课表查询
    # ------------------------------------------------------------------
    def get_my_schedule(self, teacher_id: int) -> list[dict]:
        """返回教师的完整课表（来自 view_teacher_schedule）。"""
        sql = """
            SELECT teaching_id, course_code, course_name, credits,
                   classroom, timeslot, semester,
                   enrolled_count, max_count, status, is_submitted, dept_name
            FROM view_teacher_schedule
            WHERE teacher_id = %s
            ORDER BY semester DESC, timeslot
        """
        return DBManager.exec_query(sql, (teacher_id,))

    def get_available_semesters_for_teacher(self, teacher_id: int) -> list[str]:
        """返回该教师有授课安排的所有学期列表（降序）。"""
        sql = """
            SELECT DISTINCT semester
            FROM view_teacher_schedule
            WHERE teacher_id = %s
            ORDER BY semester DESC
        """
        rows = DBManager.exec_query(sql, (teacher_id,))
        return [r["semester"] for r in rows]

    # ------------------------------------------------------------------
    # 成绩提交锁定
    # ------------------------------------------------------------------
    def is_grades_submitted(self, teaching_id: int) -> bool:
        """返回该班级成绩是否已提交锁定。"""
        sql = """
            SELECT is_submitted
            FROM edu_teaching
            WHERE id = %s AND is_deleted = 0
        """
        rows = DBManager.exec_query(sql, (teaching_id,))
        if not rows:
            return False
        return bool(rows[0]["is_submitted"])

    def submit_grades(self, teaching_id: int) -> int:
        """调用存储过程提交锁定指定班级的成绩。

        Returns:
            已提交的成绩条数。

        Raises:
            ValidationError: 提交前校验失败（仍有未录入成绩）。
            BusinessError:   数据库执行失败。
        """
        with DBManager.transaction() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute("CALL proc_submit_grades(%s)", (teaching_id,))
                row = cursor.fetchone()
                while cursor.nextset():
                    pass
            except mysql.connector.errors.DatabaseError as exc:
                raise ValidationError(str(exc)) from exc
            finally:
                cursor.close()

        count = int(row["submitted_count"]) if row and row.get("submitted_count") is not None else 0
        uid = Session.current_user.id if Session.current_user else None
        AuditLogger.log_action(
            uid,
            ActionType.SUBMIT_GRADES,
            f"teaching_id={teaching_id}, submitted_count={count}",
        )
        return count

    # ------------------------------------------------------------------
    # 班级花名册
    # ------------------------------------------------------------------
    def get_class_roster(self, teaching_id: int) -> list[dict]:
        """返回该授课班级的学生名单。

        优先从 stu_selection（选课表）获取；若选课表为空则从 edu_grades 兜底。
        返回字段: student_id, username, real_name, major_name, dept_name
        """
        # 优先：通过 stu_selection → edu_teaching 关联获取选课学生
        sql_selection = """
            SELECT
                u.id          AS student_id,
                u.username,
                u.real_name,
                COALESCE(m.major_name, '未分配') AS major_name,
                COALESCE(d.dept_name,  '未分配') AS dept_name
            FROM edu_teaching   et
            JOIN stu_selection   ss ON ss.teaching_id = et.id AND ss.deleted_at = 0
            JOIN sys_users       u  ON u.id = ss.student_id AND u.is_deleted = 0
            LEFT JOIN base_major m  ON m.id = u.major_id AND m.is_deleted = 0
            LEFT JOIN base_dept  d  ON d.id = u.dept_id  AND d.is_deleted = 0
            WHERE et.id = %s AND et.is_deleted = 0
            ORDER BY u.real_name
        """
        rows = DBManager.exec_query(sql_selection, (teaching_id,))

        if rows:
            return rows

        # 兜底：从 edu_grades 取已有成绩记录的学生
        sql_grades = """
            SELECT
                u.id          AS student_id,
                u.username,
                u.real_name,
                COALESCE(m.major_name, '未分配') AS major_name,
                COALESCE(d.dept_name,  '未分配') AS dept_name
            FROM edu_grades    g
            JOIN sys_users     u ON u.id = g.student_id AND u.is_deleted = 0
            LEFT JOIN base_major m ON m.id = u.major_id AND m.is_deleted = 0
            LEFT JOIN base_dept  d ON d.id = u.dept_id  AND d.is_deleted = 0
            WHERE g.teaching_id = %s AND g.is_deleted = 0
            ORDER BY u.real_name
        """
        return DBManager.exec_query(sql_grades, (teaching_id,))

    # ------------------------------------------------------------------
    # 选课名单
    # ------------------------------------------------------------------
    def get_enrollment_detail(self, teaching_id: int) -> list[dict]:
        """返回该授课班级的学生名单。

        范围 = 已选课（stu_selection）∪ 已有成绩（edu_grades），与成绩录入表保持一致。
        返回字段: student_id, username, real_name, major_name, dept_name, selected_at
        """
        sql = """
            SELECT
                u.id          AS student_id,
                u.username,
                u.real_name,
                COALESCE(m.major_name, '未分配') AS major_name,
                COALESCE(d.dept_name,  '未分配') AS dept_name,
                ss.created_at AS selected_at
            FROM edu_teaching   et
            JOIN stu_selection   ss ON ss.teaching_id = et.id AND ss.deleted_at = 0
            JOIN sys_users       u  ON u.id = ss.student_id AND u.is_deleted = 0
            LEFT JOIN base_major m  ON m.id = u.major_id AND m.is_deleted = 0
            LEFT JOIN base_dept  d  ON d.id = u.dept_id  AND d.is_deleted = 0
            WHERE et.id = %s AND et.is_deleted = 0

            UNION

            SELECT
                u.id          AS student_id,
                u.username,
                u.real_name,
                COALESCE(m.major_name, '未分配') AS major_name,
                COALESCE(d.dept_name,  '未分配') AS dept_name,
                g.created_at  AS selected_at
            FROM edu_grades    g
            JOIN sys_users     u ON u.id = g.student_id AND u.is_deleted = 0
            LEFT JOIN base_major m ON m.id = u.major_id AND m.is_deleted = 0
            LEFT JOIN base_dept  d ON d.id = u.dept_id  AND d.is_deleted = 0
            WHERE g.teaching_id = %s AND g.is_deleted = 0

            ORDER BY real_name
        """
        return DBManager.exec_query(sql, (teaching_id, teaching_id))

    def get_waiting_list(self, teaching_id: int) -> list[dict]:
        """返回该授课班级的候补等候学生名单。

        返回字段: queue_no, student_id, username, real_name, major_name, dept_name, queued_at
        """
        sql = """
            SELECT
                wl.queue_no,
                u.id          AS student_id,
                u.username,
                u.real_name,
                COALESCE(m.major_name, '未分配') AS major_name,
                COALESCE(d.dept_name,  '未分配') AS dept_name,
                wl.created_at AS queued_at
            FROM edu_teaching     et
            JOIN stu_waiting_list  wl ON wl.teaching_id = et.id AND wl.deleted_at = 0
            JOIN sys_users         u  ON u.id = wl.student_id AND u.is_deleted = 0
            LEFT JOIN base_major   m  ON m.id = u.major_id AND m.is_deleted = 0
            LEFT JOIN base_dept    d  ON d.id = u.dept_id  AND d.is_deleted = 0
            WHERE et.id = %s AND et.is_deleted = 0
            ORDER BY wl.queue_no
        """
        return DBManager.exec_query(sql, (teaching_id,))

    # ------------------------------------------------------------------
    # 平时分记录
    # ------------------------------------------------------------------
    def get_daily_records(
        self,
        teaching_id: int,
        record_type: str,
        record_date: str,
    ) -> list[dict]:
        """查询指定日期和类型的平时记录。

        返回字段: record_id, student_id, username, real_name, completed, note
        """
        sql = """
            SELECT
                dr.id        AS record_id,
                dr.student_id,
                u.username,
                u.real_name,
                dr.completed,
                dr.note
            FROM edu_daily_records dr
            JOIN sys_users u ON dr.student_id = u.id AND u.is_deleted = 0
            WHERE dr.teaching_id  = %s
              AND dr.record_type  = %s
              AND dr.record_date  = %s
              AND dr.is_deleted   = 0
            ORDER BY u.real_name
        """
        return DBManager.exec_query(sql, (teaching_id, record_type, record_date))

    def batch_save_daily_records(
        self,
        teaching_id: int,
        record_type: str,
        record_date: str,
        records: list[dict],  # [{student_id, completed, note}]
    ) -> int:
        """批量保存平时记录（UPSERT）。

        Returns:
            实际写入/更新的条数。
        """
        if not records:
            raise ValidationError("记录数据为空。")
        if record_type not in ("SIGNIN", "HOMEWORK", "CHAPTER_TEST"):
            raise ValidationError("记录类型非法。")

        upsert_sql = """
            INSERT INTO edu_daily_records
                (teaching_id, student_id, record_date, record_type, completed, note)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                completed  = VALUES(completed),
                note       = VALUES(note),
                is_deleted = 0
        """
        tasks = [
            (upsert_sql, (
                teaching_id,
                r["student_id"],
                record_date,
                record_type,
                int(r.get("completed", 0)),
                r.get("note") or None,
            ))
            for r in records
        ]
        DBManager.exec_transaction(tasks)

        uid = Session.current_user.id if Session.current_user else None
        AuditLogger.log_action(
            uid,
            ActionType.SAVE_DAILY_RECORDS,
            f"teaching_id={teaching_id}, type={record_type}, date={record_date}, count={len(tasks)}",
        )
        return len(tasks)

    # ------------------------------------------------------------------
    # 历史归档
    # ------------------------------------------------------------------
    def get_available_archive_semesters(self, teacher_id: int) -> list[str]:
        """返回该教师有归档记录的学期列表（降序）。"""
        sql = """
            SELECT DISTINCT a.semester
            FROM edu_archives  a
            JOIN edu_teaching  t ON a.teaching_id = t.id
            WHERE t.teacher_id  = %s
              AND a.is_deleted   = 0
            ORDER BY a.semester DESC
        """
        rows = DBManager.exec_query(sql, (teacher_id,))
        return [r["semester"] for r in rows]

    def get_archived_grades(self, teacher_id: int, semester: str) -> list[dict]:
        """返回指定教师在指定学期的归档成绩。"""
        return AnalysisDAO().get_archive_by_teacher(teacher_id, semester)

    # ------------------------------------------------------------------
    # Excel 导入卷面成绩
    # ------------------------------------------------------------------
    def import_grades_from_excel(self, teaching_id: int, file_path: str) -> int:
        """从 Excel 文件导入卷面成绩，自动计算最终成绩。

        Excel 格式要求（第一行为标题行）:
            学号 | 卷面成绩

        Returns:
            成功导入的条数。

        Raises:
            ValidationError: 文件不存在、格式错误或列缺失。
        """
        try:
            import openpyxl  # type: ignore
        except ImportError as exc:
            raise ValidationError("缺少 openpyxl 依赖，请执行 pip install openpyxl") from exc

        from pathlib import Path
        if not Path(file_path).exists():
            raise ValidationError(f"文件不存在: {file_path}")

        try:
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            ws = wb.active
        except Exception as exc:
            raise ValidationError(f"无法读取 Excel 文件: {exc}") from exc

        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            raise ValidationError("Excel 文件为空。")

        # 检测标题行（支持任意列顺序）
        header = [str(cell).strip() if cell is not None else "" for cell in rows[0]]
        try:
            col_username = header.index("学号")
            col_score    = header.index("卷面成绩")
        except ValueError:
            raise ValidationError(
                f"Excel 标题行缺少必要列。\n"
                f"要求列名: '学号', '卷面成绩'\n"
                f"当前标题: {header}"
            )

        # 解析数据行，构建 {username: exam_score}
        username_score: dict[str, float] = {}
        for row in rows[1:]:
            username_val = row[col_username]
            score_val    = row[col_score]
            if username_val is None or score_val is None:
                continue
            try:
                username_score[str(username_val).strip()] = float(score_val)
            except (TypeError, ValueError):
                continue

        if not username_score:
            raise ValidationError("Excel 文件中无有效数据行。")

        # 批量查询 username → student_id
        placeholders = ",".join(["%s"] * len(username_score))
        user_rows = DBManager.exec_query(
            f"SELECT id, username FROM sys_users WHERE username IN ({placeholders}) AND is_deleted = 0",
            tuple(username_score.keys()),
        )
        name_to_id: dict[str, int] = {r["username"]: r["id"] for r in user_rows}

        exam_dict: dict[int, float] = {}
        for uname, score in username_score.items():
            if uname in name_to_id:
                exam_dict[name_to_id[uname]] = score

        if not exam_dict:
            raise ValidationError("Excel 中的学号与系统用户不匹配，导入失败。")

        count = GradeService().batch_enter_exam_scores(teaching_id, exam_dict)

        uid = Session.current_user.id if Session.current_user else None
        AuditLogger.log_action(
            uid,
            ActionType.IMPORT_GRADES_EXCEL,
            f"teaching_id={teaching_id}, imported={count}",
        )
        return count

    # ------------------------------------------------------------------
    # 调课申请
    # ------------------------------------------------------------------
    def submit_reschedule_request(
        self,
        teaching_id: int,
        teacher_id: int,
        reason: str,
        original_time: Optional[str],
        requested_time: Optional[str],
    ) -> int:
        """提交调课申请。

        Returns:
            新申请的 ID。

        Raises:
            ValidationError: 原因为空。
        """
        reason = reason.strip() if reason else ""
        if not reason:
            raise ValidationError("申请原因不能为空。")

        # 验证授课安排存在
        teaching = DBManager.exec_query(
            "SELECT id FROM edu_teaching WHERE id = %s AND is_deleted = 0 LIMIT 1",
            (teaching_id,),
        )
        if not teaching:
            raise ValidationError("授课安排不存在或已删除。")

        insert_sql = """
            INSERT INTO edu_schedule_change_req
                (teaching_id, teacher_id, reason, original_time, requested_time, status)
            VALUES (%s, %s, %s, %s, %s, 'PENDING')
        """
        DBManager.exec_query(
            insert_sql,
            (teaching_id, teacher_id, reason, original_time, requested_time),
            fetch=False,
        )

        # 获取新插入的 ID
        rows = DBManager.exec_query("SELECT LAST_INSERT_ID() AS new_id")
        new_id = int(rows[0]["new_id"]) if rows else 0

        uid = Session.current_user.id if Session.current_user else None
        AuditLogger.log_action(
            uid,
            ActionType.REQUEST_RESCHEDULE,
            f"teaching_id={teaching_id}, req_id={new_id}",
        )
        return new_id

    def list_my_reschedule_requests(self, teacher_id: int) -> list[dict]:
        """返回该教师提交的所有调课申请。

        返回字段: req_id, course_name, semester, original_time, requested_time,
                  reason, status, admin_comment, created_at
        """
        sql = """
            SELECT
                req.id            AS req_id,
                c.course_name,
                t.semester,
                req.original_time,
                req.requested_time,
                req.reason,
                req.status,
                req.admin_comment,
                req.created_at
            FROM edu_schedule_change_req req
            JOIN edu_teaching            t   ON req.teaching_id = t.id
            JOIN edu_courses             c   ON t.course_id     = c.id AND c.is_deleted = 0
            WHERE req.teacher_id  = %s
              AND req.is_deleted  = 0
            ORDER BY req.created_at DESC
        """
        return DBManager.exec_query(sql, (teacher_id,))
