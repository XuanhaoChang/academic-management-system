from __future__ import annotations

import csv
import hashlib
from datetime import datetime
from pathlib import Path

import mysql.connector

from core.constants import ActionType
from core.db_manager import DBManager
from core.exceptions import ValidationError
from core.logger import AuditLogger
from core.session import Session


class AdminService:
    @staticmethod
    def _hash_password(raw_password: str) -> str:
        return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()

    @staticmethod
    def _current_uid() -> int | None:
        return Session.current_user.id if Session.current_user else None

    @staticmethod
    def _ensure_student_profile(cursor, student_id: int) -> None:
        """
        Keep student-side data consistent with admin-side account creation.
        If stu_info is not initialized in current DB, skip silently.
        """
        try:
            cursor.execute(
                """
                INSERT INTO stu_info (student_id, grade_year, class_name, is_deleted)
                VALUES (%s, YEAR(CURDATE()), '未分班', 0)
                ON DUPLICATE KEY UPDATE
                    is_deleted = 0
                """,
                (student_id,),
            )
        except mysql.connector.Error as exc:
            # Compatible with environments where student extension SQL has not been executed yet.
            if getattr(exc, "errno", None) != 1146:
                raise

    @staticmethod
    def _parse_optional_id(raw_value: int | str | None, field_name: str) -> int | None:
        if raw_value in (None, ""):
            return None
        try:
            return int(raw_value)
        except (TypeError, ValueError) as exc:
            raise ValidationError(f"{field_name}非法") from exc

    @classmethod
    def _validate_user_org_fields(
        cls,
        role_id: int,
        dept_id: int | str | None,
        major_id: int | str | None,
    ) -> tuple[int | None, int | None]:
        if role_id == 1:
            return None, None

        normalized_dept_id = cls._parse_optional_id(dept_id, "院系")
        normalized_major_id = cls._parse_optional_id(major_id, "专业")

        if role_id == 2:
            if normalized_dept_id is None:
                raise ValidationError("教师必须选择所属院系")
            dept_exists = DBManager.exec_query(
                "SELECT id FROM base_dept WHERE id = %s AND is_deleted = 0 LIMIT 1",
                (normalized_dept_id,),
                fetch=True,
            )
            if not dept_exists:
                raise ValidationError("所属院系不存在或已删除")
            return normalized_dept_id, None

        if role_id == 3:
            if normalized_dept_id is None:
                raise ValidationError("学生必须选择所属院系")
            if normalized_major_id is None:
                raise ValidationError("学生必须选择所属专业")

            dept_exists = DBManager.exec_query(
                "SELECT id FROM base_dept WHERE id = %s AND is_deleted = 0 LIMIT 1",
                (normalized_dept_id,),
                fetch=True,
            )
            if not dept_exists:
                raise ValidationError("所属院系不存在或已删除")

            major_exists = DBManager.exec_query(
                """
                SELECT id
                FROM base_major
                WHERE id = %s AND dept_id = %s AND is_deleted = 0
                LIMIT 1
                """,
                (normalized_major_id, normalized_dept_id),
                fetch=True,
            )
            if not major_exists:
                raise ValidationError("所属专业不存在、已删除或不属于所选院系")
            return normalized_dept_id, normalized_major_id

        raise ValidationError("角色非法")

    @staticmethod
    def get_current_semester() -> str:
        now = datetime.now()
        year = now.year
        month = now.month
        if 2 <= month <= 6:
            return f"{year}-1"
        elif 7 <= month <= 8:
            return f"{year}-2"
        else:
            return f"{year}-2"

    @staticmethod
    def get_semester_options() -> list[dict]:
        now = datetime.now()
        current_year = now.year
        semesters = []
        for y in range(current_year - 2, current_year + 1):
            semesters.append({"value": f"{y}-1", "label": f"{y}学年 春季学期"})
            semesters.append({"value": f"{y}-2", "label": f"{y}学年 秋季学期"})
        return semesters

    @staticmethod
    def create_dept(dept_code: str, dept_name: str) -> None:
        code = dept_code.strip()
        name = dept_name.strip()
        if not code:
            raise ValidationError("院系编码不能为空")
        if not name:
            raise ValidationError("院系名称不能为空")

        exists = DBManager.exec_query(
            "SELECT id FROM base_dept WHERE dept_code = %s LIMIT 1",
            (code,),
            fetch=True,
        )
        if exists:
            raise ValidationError("院系编码已存在")

        DBManager.exec_query(
            "INSERT INTO base_dept (dept_code, dept_name, is_deleted) VALUES (%s, %s, 0)",
            (code, name),
            fetch=False,
        )
        AuditLogger.log_action(AdminService._current_uid(), ActionType.CREATE_DEPT, f"Created dept code={code}")

    @staticmethod
    def update_dept(dept_id: int, dept_code: str, dept_name: str) -> None:
        code = dept_code.strip()
        name = dept_name.strip()
        if not code:
            raise ValidationError("院系编码不能为空")
        if not name:
            raise ValidationError("院系名称不能为空")

        dept = DBManager.exec_query(
            "SELECT id FROM base_dept WHERE id = %s AND is_deleted = 0 LIMIT 1",
            (dept_id,),
            fetch=True,
        )
        if not dept:
            raise ValidationError("院系不存在或已删除")

        dup = DBManager.exec_query(
            "SELECT id FROM base_dept WHERE dept_code = %s AND id <> %s LIMIT 1",
            (code, dept_id),
            fetch=True,
        )
        if dup:
            raise ValidationError("院系编码已存在")

        DBManager.exec_query(
            "UPDATE base_dept SET dept_code = %s, dept_name = %s WHERE id = %s",
            (code, name, dept_id),
            fetch=False,
        )
        AuditLogger.log_action(AdminService._current_uid(), ActionType.UPDATE_DEPT, f"Updated dept_id={dept_id}")

    @staticmethod
    def soft_delete_dept(dept_id: int) -> None:
        dept = DBManager.exec_query(
            "SELECT id FROM base_dept WHERE id = %s AND is_deleted = 0 LIMIT 1",
            (dept_id,),
            fetch=True,
        )
        if not dept:
            raise ValidationError("院系不存在或已删除")

        major_check = DBManager.exec_query(
            "SELECT id FROM base_major WHERE dept_id = %s AND is_deleted = 0 LIMIT 1",
            (dept_id,),
            fetch=True,
        )
        if major_check:
            raise ValidationError("该院系存在关联专业，无法删除")

        course_check = DBManager.exec_query(
            "SELECT id FROM edu_courses WHERE dept_id = %s AND is_deleted = 0 LIMIT 1",
            (dept_id,),
            fetch=True,
        )
        if course_check:
            raise ValidationError("该院系存在关联课程，无法删除")

        DBManager.exec_query(
            "UPDATE base_dept SET is_deleted = 1 WHERE id = %s AND is_deleted = 0",
            (dept_id,),
            fetch=False,
        )
        AuditLogger.log_action(
            AdminService._current_uid(), ActionType.SOFT_DELETE_DEPT, f"Soft deleted dept_id={dept_id}"
        )

    @staticmethod
    def list_depts(include_deleted: bool = False) -> list[dict]:
        sql = "SELECT id, dept_code, dept_name, is_deleted, created_at FROM base_dept"
        if not include_deleted:
            sql += " WHERE is_deleted = 0"
        sql += " ORDER BY id ASC"
        return DBManager.exec_query(sql, fetch=True)

    @staticmethod
    def create_major(major_code: str, major_name: str, dept_id: int) -> None:
        code = major_code.strip()
        name = major_name.strip()
        if not code:
            raise ValidationError("专业编码不能为空")
        if not name:
            raise ValidationError("专业名称不能为空")

        dept = DBManager.exec_query(
            "SELECT id FROM base_dept WHERE id = %s AND is_deleted = 0 LIMIT 1",
            (dept_id,),
            fetch=True,
        )
        if not dept:
            raise ValidationError("所属院系不存在或已删除")

        exists = DBManager.exec_query(
            "SELECT id FROM base_major WHERE major_code = %s LIMIT 1",
            (code,),
            fetch=True,
        )
        if exists:
            raise ValidationError("专业编码已存在")

        DBManager.exec_query(
            "INSERT INTO base_major (major_code, major_name, dept_id, is_deleted) VALUES (%s, %s, %s, 0)",
            (code, name, dept_id),
            fetch=False,
        )
        AuditLogger.log_action(AdminService._current_uid(), ActionType.CREATE_MAJOR, f"Created major code={code}")

    @staticmethod
    def update_major(major_id: int, major_code: str, major_name: str, dept_id: int) -> None:
        code = major_code.strip()
        name = major_name.strip()
        if not code:
            raise ValidationError("专业编码不能为空")
        if not name:
            raise ValidationError("专业名称不能为空")

        major = DBManager.exec_query(
            "SELECT id FROM base_major WHERE id = %s AND is_deleted = 0 LIMIT 1",
            (major_id,),
            fetch=True,
        )
        if not major:
            raise ValidationError("专业不存在或已删除")

        dept = DBManager.exec_query(
            "SELECT id FROM base_dept WHERE id = %s AND is_deleted = 0 LIMIT 1",
            (dept_id,),
            fetch=True,
        )
        if not dept:
            raise ValidationError("所属院系不存在或已删除")

        dup = DBManager.exec_query(
            "SELECT id FROM base_major WHERE major_code = %s AND id <> %s LIMIT 1",
            (code, major_id),
            fetch=True,
        )
        if dup:
            raise ValidationError("专业编码已存在")

        DBManager.exec_query(
            "UPDATE base_major SET major_code = %s, major_name = %s, dept_id = %s WHERE id = %s",
            (code, name, dept_id, major_id),
            fetch=False,
        )
        AuditLogger.log_action(AdminService._current_uid(), ActionType.UPDATE_MAJOR, f"Updated major_id={major_id}")

    @staticmethod
    def soft_delete_major(major_id: int) -> None:
        major_rows = DBManager.exec_query(
            "SELECT id, dept_id FROM base_major WHERE id = %s AND is_deleted = 0 LIMIT 1",
            (major_id,),
            fetch=True,
        )
        if not major_rows:
            raise ValidationError("专业不存在或已删除")

        dept_id = major_rows[0]["dept_id"]
        course_check = DBManager.exec_query(
            "SELECT id FROM edu_courses WHERE dept_id = %s AND is_deleted = 0 LIMIT 1",
            (dept_id,),
            fetch=True,
        )
        if course_check:
            raise ValidationError("该专业存在关联课程，无法删除")

        DBManager.exec_query(
            "UPDATE base_major SET is_deleted = 1 WHERE id = %s AND is_deleted = 0",
            (major_id,),
            fetch=False,
        )
        AuditLogger.log_action(
            AdminService._current_uid(), ActionType.SOFT_DELETE_MAJOR, f"Soft deleted major_id={major_id}"
        )

    @staticmethod
    def list_majors(include_deleted: bool = False) -> list[dict]:
        sql = """
        SELECT m.id, m.major_code, m.major_name, m.dept_id, d.dept_name, m.is_deleted, m.created_at
        FROM base_major m
        JOIN base_dept d ON d.id = m.dept_id
        """
        if not include_deleted:
            sql += " WHERE m.is_deleted = 0"
        sql += " ORDER BY m.id ASC"
        return DBManager.exec_query(sql, fetch=True)

    @staticmethod
    def create_course(
        course_code: str,
        course_name: str,
        credits: float,
        capacity: int,
        dept_id: int,
        description: str | None,
    ) -> None:
        code = course_code.strip()
        name = course_name.strip()
        desc = description.strip() if description else None
        if not code:
            raise ValidationError("课程编码不能为空")
        if not name:
            raise ValidationError("课程名称不能为空")
        if credits <= 0:
            raise ValidationError("学分必须大于0")
        _ = capacity  # 课程容量已下沉到教学班 max_count

        dept = DBManager.exec_query(
            "SELECT id FROM base_dept WHERE id = %s AND is_deleted = 0 LIMIT 1",
            (dept_id,),
            fetch=True,
        )
        if not dept:
            raise ValidationError("所属院系不存在或已删除")

        exists = DBManager.exec_query(
            "SELECT id FROM edu_courses WHERE course_code = %s LIMIT 1",
            (code,),
            fetch=True,
        )
        if exists:
            raise ValidationError("课程编码已存在")

        DBManager.exec_query(
            """
            INSERT INTO edu_courses
            (course_code, course_name, credits, dept_id, description, is_deleted)
            VALUES (%s, %s, %s, %s, %s, 0)
            """,
            (code, name, credits, dept_id, desc),
            fetch=False,
        )
        AuditLogger.log_action(AdminService._current_uid(), ActionType.CREATE_COURSE, f"Created course code={code}")

    @staticmethod
    def update_course(
        course_id: int,
        course_code: str,
        course_name: str,
        credits: float,
        capacity: int,
        dept_id: int,
        description: str | None,
    ) -> None:
        code = course_code.strip()
        name = course_name.strip()
        desc = description.strip() if description else None
        if not code:
            raise ValidationError("课程编码不能为空")
        if not name:
            raise ValidationError("课程名称不能为空")
        if credits <= 0:
            raise ValidationError("学分必须大于0")
        _ = capacity  # 课程容量已下沉到教学班 max_count

        course = DBManager.exec_query(
            "SELECT id FROM edu_courses WHERE id = %s AND is_deleted = 0 LIMIT 1",
            (course_id,),
            fetch=True,
        )
        if not course:
            raise ValidationError("课程不存在或已删除")

        dept = DBManager.exec_query(
            "SELECT id FROM base_dept WHERE id = %s AND is_deleted = 0 LIMIT 1",
            (dept_id,),
            fetch=True,
        )
        if not dept:
            raise ValidationError("所属院系不存在或已删除")

        dup = DBManager.exec_query(
            "SELECT id FROM edu_courses WHERE course_code = %s AND id <> %s LIMIT 1",
            (code, course_id),
            fetch=True,
        )
        if dup:
            raise ValidationError("课程编码已存在")

        DBManager.exec_query(
            """
            UPDATE edu_courses
            SET course_code = %s,
                course_name = %s,
                credits = %s,
                dept_id = %s,
                description = %s
            WHERE id = %s
            """,
            (code, name, credits, dept_id, desc, course_id),
            fetch=False,
        )
        AuditLogger.log_action(AdminService._current_uid(), ActionType.UPDATE_COURSE, f"Updated course_id={course_id}")

    @staticmethod
    def soft_delete_course(course_id: int) -> None:
        course = DBManager.exec_query(
            "SELECT id FROM edu_courses WHERE id = %s AND is_deleted = 0 LIMIT 1",
            (course_id,),
            fetch=True,
        )
        if not course:
            raise ValidationError("课程不存在或已删除")

        DBManager.exec_query(
            "UPDATE edu_courses SET is_deleted = 1 WHERE id = %s AND is_deleted = 0",
            (course_id,),
            fetch=False,
        )
        AuditLogger.log_action(
            AdminService._current_uid(), ActionType.SOFT_DELETE_COURSE, f"Soft deleted course_id={course_id}"
        )

    @staticmethod
    def list_courses(include_deleted: bool = False) -> list[dict]:
        sql = """
         SELECT c.id, c.course_code, c.course_name, c.credits,
               COALESCE(
                   (
                       SELECT t.max_count
                       FROM edu_teaching t
                       WHERE t.course_id = c.id AND t.is_deleted = 0
                       ORDER BY t.id DESC
                       LIMIT 1
                   ),
                   50
               ) AS capacity,
               c.dept_id, d.dept_name, c.description, c.is_deleted, c.created_at
        FROM edu_courses c
        JOIN base_dept d ON d.id = c.dept_id
        """
        if not include_deleted:
            sql += " WHERE c.is_deleted = 0"
        sql += " ORDER BY c.id ASC"
        return DBManager.exec_query(sql, fetch=True)

    @staticmethod
    def list_teachers() -> list[dict]:
        sql = """
        SELECT id, username, real_name, dept_id
        FROM sys_users
        WHERE role_id = 2 AND is_deleted = 0
        ORDER BY real_name
        """
        return DBManager.exec_query(sql, fetch=True)

    @staticmethod
    def list_teachings(semester: str | None = None, include_deleted: bool = False) -> list[dict]:
        sql = """
        SELECT t.id, t.course_id, c.course_name, c.course_code,
               t.teacher_id, u.real_name AS teacher_name,
               t.classroom, t.timeslot, t.semester,
               t.enrolled_count, t.max_count, t.status,
               t.created_at, t.is_deleted
        FROM edu_teaching t
        JOIN edu_courses c ON t.course_id = c.id AND c.is_deleted = 0
        JOIN sys_users u ON t.teacher_id = u.id AND u.is_deleted = 0
        """
        conditions = []
        if not include_deleted:
            conditions.append("t.is_deleted = 0")
        if semester:
            conditions.append("t.semester = %s")
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY t.semester DESC, c.course_name"
        params = (semester,) if semester else None
        return DBManager.exec_query(sql, params, fetch=True)

    @staticmethod
    def create_teaching(
        course_id: int,
        teacher_id: int,
        classroom: str | None,
        timeslot: str | None,
        semester: str,
        max_count: int = 50,
    ) -> None:
        if not course_id:
            raise ValidationError("请选择课程")
        if not teacher_id:
            raise ValidationError("请选择授课教师")
        if not semester:
            raise ValidationError("学期不能为空（格式：2024-1）")
        if max_count <= 0:
            raise ValidationError("容量必须大于0")

        course = DBManager.exec_query(
            "SELECT id FROM edu_courses WHERE id = %s AND is_deleted = 0 LIMIT 1",
            (course_id,),
            fetch=True,
        )
        if not course:
            raise ValidationError("课程不存在或已删除")

        teacher = DBManager.exec_query(
            "SELECT id FROM sys_users WHERE id = %s AND role_id = 2 AND is_deleted = 0 LIMIT 1",
            (teacher_id,),
            fetch=True,
        )
        if not teacher:
            raise ValidationError("教师不存在或无权授课")

        DBManager.exec_query(
            """
            INSERT INTO edu_teaching
            (course_id, teacher_id, classroom, timeslot, semester, max_count, enrolled_count, status, is_deleted)
            VALUES (%s, %s, %s, %s, %s, %s, 0, 'OPEN', 0)
            """,
            (course_id, teacher_id, classroom, timeslot, semester, max_count),
            fetch=False,
        )
        AuditLogger.log_action(
            AdminService._current_uid(),
            ActionType.CREATE_TEACHING,
            f"Created teaching: course_id={course_id}, teacher_id={teacher_id}, semester={semester}",
        )

    @staticmethod
    def update_teaching(
        teaching_id: int,
        course_id: int,
        teacher_id: int,
        classroom: str | None,
        timeslot: str | None,
        semester: str,
        max_count: int,
        status: str,
    ) -> None:
        if not course_id or not teacher_id or not semester:
            raise ValidationError("课程、教师、学期不能为空")
        if max_count <= 0:
            raise ValidationError("容量必须大于0")
        if status not in ("OPEN", "CLOSED", "FULL"):
            raise ValidationError("状态非法")

        teaching = DBManager.exec_query(
            "SELECT id FROM edu_teaching WHERE id = %s AND is_deleted = 0 LIMIT 1",
            (teaching_id,),
            fetch=True,
        )
        if not teaching:
            raise ValidationError("授课安排不存在或已删除")

        DBManager.exec_query(
            """
            UPDATE edu_teaching
            SET course_id = %s, teacher_id = %s, classroom = %s,
                timeslot = %s, semester = %s, max_count = %s, status = %s
            WHERE id = %s
            """,
            (course_id, teacher_id, classroom, timeslot, semester, max_count, status, teaching_id),
            fetch=False,
        )
        AuditLogger.log_action(
            AdminService._current_uid(),
            ActionType.UPDATE_TEACHING,
            f"Updated teaching_id={teaching_id}",
        )

    @staticmethod
    def soft_delete_teaching(teaching_id: int) -> None:
        teaching = DBManager.exec_query(
            "SELECT id FROM edu_teaching WHERE id = %s AND is_deleted = 0 LIMIT 1",
            (teaching_id,),
            fetch=True,
        )
        if not teaching:
            raise ValidationError("授课安排不存在或已删除")

        DBManager.exec_query(
            "UPDATE edu_teaching SET is_deleted = 1 WHERE id = %s AND is_deleted = 0",
            (teaching_id,),
            fetch=False,
        )
        AuditLogger.log_action(
            AdminService._current_uid(),
            ActionType.SOFT_DELETE_TEACHING,
            f"Soft deleted teaching_id={teaching_id}",
        )

    @staticmethod
    def get_available_semesters() -> list[str]:
        sql = """
        SELECT DISTINCT semester FROM edu_teaching WHERE is_deleted = 0 ORDER BY semester DESC
        """
        rows = DBManager.exec_query(sql, fetch=True)
        return [r["semester"] for r in rows]

    @staticmethod
    def list_reschedule_requests(status: str | None = None) -> list[dict]:
        """查询教师调课申请列表（管理员端）。"""
        sql = """
        SELECT
            req.id AS req_id,
            req.teaching_id,
            c.course_code,
            c.course_name,
            u.real_name AS teacher_name,
            t.semester,
            req.original_time,
            req.requested_time,
            req.reason,
            req.status,
            req.admin_comment,
            req.created_at,
            req.processed_by,
            admin_u.real_name AS processed_by_name
        FROM edu_schedule_change_req req
        JOIN edu_teaching t ON req.teaching_id = t.id AND t.is_deleted = 0
        JOIN edu_courses c ON t.course_id = c.id AND c.is_deleted = 0
        JOIN sys_users u ON req.teacher_id = u.id AND u.is_deleted = 0
        LEFT JOIN sys_users admin_u ON req.processed_by = admin_u.id
        WHERE req.is_deleted = 0
        """
        params: tuple = ()
        if status in ("PENDING", "APPROVED", "REJECTED"):
            sql += " AND req.status = %s"
            params = (status,)

        sql += " ORDER BY (req.status='PENDING') DESC, req.created_at DESC"
        return DBManager.exec_query(sql, params if params else None, fetch=True)

    @staticmethod
    def process_reschedule_request(req_id: int, decision: str, admin_comment: str | None = None) -> None:
        """审批调课申请。decision 仅允许 APPROVED / REJECTED。"""
        decision = (decision or "").upper().strip()
        if decision not in ("APPROVED", "REJECTED"):
            raise ValidationError("审批动作非法，仅支持 APPROVED/REJECTED")

        uid = AdminService._current_uid()
        comment = (admin_comment or "").strip() or None

        with DBManager.transaction() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute(
                    """
                    SELECT id, teaching_id, requested_time, status
                    FROM edu_schedule_change_req
                    WHERE id = %s AND is_deleted = 0
                    LIMIT 1
                    FOR UPDATE
                    """,
                    (req_id,),
                )
                req = cursor.fetchone()
                if not req:
                    raise ValidationError("调课申请不存在或已删除")
                if req["status"] != "PENDING":
                    raise ValidationError("该申请已处理，不能重复审批")

                if decision == "APPROVED":
                    if not req.get("requested_time"):
                        raise ValidationError("申请时间为空，无法批准")
                    cursor.execute(
                        """
                        UPDATE edu_teaching
                        SET timeslot = %s
                        WHERE id = %s AND is_deleted = 0
                        """,
                        (req["requested_time"], req["teaching_id"]),
                    )

                cursor.execute(
                    """
                    UPDATE edu_schedule_change_req
                    SET status = %s,
                        admin_comment = %s,
                        processed_by = %s
                    WHERE id = %s
                    """,
                    (decision, comment, uid, req_id),
                )
            finally:
                cursor.close()

        action = ActionType.APPROVE_RESCHEDULE if decision == "APPROVED" else ActionType.REJECT_RESCHEDULE
        AuditLogger.log_action(uid, action, f"req_id={req_id}, decision={decision}")

    @staticmethod
    def list_exam_defer_requests(status: str | None = None) -> list[dict]:
        """查询学生缓考申请列表（管理员端）。"""
        sql = """
        SELECT
            req.id AS req_id,
            req.student_id,
            u.username AS student_no,
            u.real_name AS student_name,
            c.course_code,
            c.course_name,
            req.semester,
            req.reason,
            req.status,
            req.created_at
        FROM stu_exam_defer_req req
        JOIN sys_users u ON req.student_id = u.id AND u.is_deleted = 0
        JOIN edu_courses c ON req.course_id = c.id AND c.is_deleted = 0
        WHERE req.is_deleted = 0
        """
        params: tuple = ()
        if status in ("PENDING", "APPROVED", "REJECTED"):
            sql += " AND req.status = %s"
            params = (status,)
        sql += " ORDER BY (req.status='PENDING') DESC, req.created_at DESC"
        return DBManager.exec_query(sql, params if params else None, fetch=True)

    @staticmethod
    def process_exam_defer_request(req_id: int, decision: str) -> None:
        """审批缓考申请。decision 仅允许 APPROVED / REJECTED。"""
        decision = (decision or "").upper().strip()
        if decision not in ("APPROVED", "REJECTED"):
            raise ValidationError("审批动作非法，仅支持 APPROVED/REJECTED")

        uid = AdminService._current_uid()
        with DBManager.transaction() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute(
                    """
                    SELECT id, status
                    FROM stu_exam_defer_req
                    WHERE id = %s AND is_deleted = 0
                    LIMIT 1
                    FOR UPDATE
                    """,
                    (req_id,),
                )
                req = cursor.fetchone()
                if not req:
                    raise ValidationError("缓考申请不存在或已删除")
                if req["status"] != "PENDING":
                    raise ValidationError("该申请已处理，不能重复审批")

                cursor.execute(
                    """
                    UPDATE stu_exam_defer_req
                    SET status = %s
                    WHERE id = %s
                    """,
                    (decision, req_id),
                )
            finally:
                cursor.close()

        action = ActionType.APPROVE_EXAM_DEFER if decision == "APPROVED" else ActionType.REJECT_EXAM_DEFER
        AuditLogger.log_action(uid, action, f"defer_req_id={req_id}, decision={decision}")

    @classmethod
    def import_users_from_csv(cls, file_path: str) -> int:
        path = Path(file_path)
        if not path.exists():
            raise ValidationError("CSV文件不存在")

        processed = 0
        current_uid = Session.current_user.id if Session.current_user else None
        try:
            with path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                required = {"username", "real_name", "role_id", "password"}
                if not required.issubset(set(reader.fieldnames or [])):
                    raise ValidationError("CSV表头必须包含 username, real_name, role_id, password")

                with DBManager.transaction() as conn:
                    cursor = conn.cursor()
                    try:
                        for row in reader:
                            role_id = int(row["role_id"])
                            cursor.execute(
                                """
                                INSERT INTO sys_users (username, real_name, role_id, password_hash, is_deleted)
                                VALUES (%s, %s, %s, %s, 0)
                                ON DUPLICATE KEY UPDATE
                                    real_name = VALUES(real_name),
                                    role_id = VALUES(role_id),
                                    password_hash = VALUES(password_hash),
                                    is_deleted = 0
                                """,
                                (
                                    row["username"],
                                    row["real_name"],
                                    role_id,
                                    cls._hash_password(row["password"]),
                                ),
                            )
                            if role_id == 3:
                                # For imported students, auto-initialize profile row.
                                cursor.execute(
                                    "SELECT id FROM sys_users WHERE username = %s LIMIT 1",
                                    (row["username"],),
                                )
                                user_row = cursor.fetchone()
                                if user_row:
                                    student_id = int(user_row[0])
                                    cls._ensure_student_profile(cursor, student_id)
                            processed += 1
                    finally:
                        cursor.close()
        except ValidationError:
            raise
        except Exception as exc:
            raise ValidationError(f"导入失败: {exc}") from exc

        AuditLogger.log_action(current_uid, ActionType.IMPORT_USERS, f"Imported/updated {processed} users")
        return processed

    @staticmethod
    def soft_delete_user(user_id: int) -> None:
        if Session.current_user and Session.current_user.id == user_id:
            raise ValidationError("不允许删除当前登录账号")

        sql = """
        UPDATE sys_users
        SET is_deleted = 1
        WHERE id = %s AND is_deleted = 0
        """
        DBManager.exec_query(sql, (user_id,), fetch=False)

        current_uid = Session.current_user.id if Session.current_user else None
        AuditLogger.log_action(current_uid, ActionType.SOFT_DELETE_USER, f"Soft deleted user_id={user_id}")

    @staticmethod
    def list_users(include_deleted: bool = True) -> list[dict]:
        sql = """
        SELECT id, username, real_name, role_id, dept_id, major_id, is_deleted, created_at
        FROM sys_users
        """
        if not include_deleted:
            sql += " WHERE is_deleted = 0"
        sql += " ORDER BY id ASC"
        return DBManager.exec_query(sql, fetch=True)

    @staticmethod
    def update_user(
        user_id: int,
        real_name: str,
        role_id: int,
        dept_id: int | str | None = None,
        major_id: int | str | None = None,
    ) -> None:
        if not real_name.strip():
            raise ValidationError("姓名不能为空")
        if role_id not in (1, 2, 3):
            raise ValidationError("角色非法")

        normalized_dept_id, normalized_major_id = AdminService._validate_user_org_fields(role_id, dept_id, major_id)

        sql = """
        UPDATE sys_users
        SET real_name = %s,
            role_id = %s,
            dept_id = %s,
            major_id = %s
        WHERE id = %s
        """
        with DBManager.transaction() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(sql, (real_name.strip(), role_id, normalized_dept_id, normalized_major_id, user_id))
                if role_id == 3:
                    # Role switched to student: ensure student profile exists.
                    AdminService._ensure_student_profile(cursor, user_id)
            finally:
                cursor.close()

        current_uid = Session.current_user.id if Session.current_user else None
        AuditLogger.log_action(current_uid, ActionType.UPDATE_USER, f"Updated user_id={user_id}")

    @classmethod
    def create_user(
        cls,
        username: str,
        real_name: str,
        role_id: int,
        raw_password: str,
        dept_id: int | str | None = None,
        major_id: int | str | None = None,
    ) -> None:
        if not username.strip():
            raise ValidationError("用户名不能为空")
        if not real_name.strip():
            raise ValidationError("姓名不能为空")
        if role_id not in (1, 2, 3):
            raise ValidationError("角色非法")
        if len(raw_password) < 6:
            raise ValidationError("密码至少6位")

        normalized_dept_id, normalized_major_id = cls._validate_user_org_fields(role_id, dept_id, major_id)

        exists_sql = """
        SELECT id
        FROM sys_users
        WHERE username = %s
        LIMIT 1
        """
        if DBManager.exec_query(exists_sql, (username.strip(),), fetch=True):
            raise ValidationError("用户名已存在")

        insert_sql = """
        INSERT INTO sys_users (username, real_name, role_id, dept_id, major_id, password_hash, is_deleted)
        VALUES (%s, %s, %s, %s, %s, %s, 0)
        """
        with DBManager.transaction() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    insert_sql,
                    (
                        username.strip(),
                        real_name.strip(),
                        role_id,
                        normalized_dept_id,
                        normalized_major_id,
                        cls._hash_password(raw_password),
                    ),
                )
                new_user_id = cursor.lastrowid
                if role_id == 3 and new_user_id:
                    cls._ensure_student_profile(cursor, int(new_user_id))
            finally:
                cursor.close()

        current_uid = Session.current_user.id if Session.current_user else None
        AuditLogger.log_action(current_uid, ActionType.CREATE_USER, f"Created user username={username.strip()}")
