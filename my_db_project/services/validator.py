from __future__ import annotations

import re
from dataclasses import dataclass

from core.db_manager import DBManager
from core.exceptions import ValidationError


@dataclass(frozen=True)
class TimeSlot:
    weekday: int  # 0=Mon ... 6=Sun
    start: int
    end: int


class CourseValidator:
    _weekday_map = {
        "一": 0,
        "二": 1,
        "三": 2,
        "四": 3,
        "五": 4,
        "六": 5,
        "日": 6,
        "天": 6,
    }

    @classmethod
    def parse_timeslot(cls, text: str) -> list[TimeSlot]:
        if not text:
            return []

        result: list[TimeSlot] = []
        chunks = re.split(r"[，,]", text)
        range_pat = re.compile(r"周([一二三四五六日天])\s*(\d+)\s*-\s*(\d+)\s*节")
        one_pat = re.compile(r"周([一二三四五六日天])\s*(\d+)\s*节")

        for raw in chunks:
            s = raw.strip().replace(" ", "")
            if not s:
                continue
            m = range_pat.search(s)
            if m:
                w = cls._weekday_map[m.group(1)]
                a = int(m.group(2))
                b = int(m.group(3))
                if b < a:
                    a, b = b, a
                result.append(TimeSlot(w, a, b))
                continue
            m2 = one_pat.search(s)
            if m2:
                w = cls._weekday_map[m2.group(1)]
                p = int(m2.group(2))
                result.append(TimeSlot(w, p, p))

        return result

    @staticmethod
    def _has_overlap(a: TimeSlot, b: TimeSlot) -> bool:
        if a.weekday != b.weekday:
            return False
        return not (a.end < b.start or b.end < a.start)

    def check_prerequisite(self, student_id: int, course_id: int) -> None:
        rows = DBManager.exec_query(
            """
            SELECT p.pre_course_id, c.course_name
            FROM stu_course_prereq p
            JOIN edu_courses c ON c.id = p.pre_course_id AND c.is_deleted = 0
            WHERE p.course_id = %s
              AND p.is_deleted = 0
            """,
            (course_id,),
        )
        if not rows:
            return

        for r in rows:
            pre_id = int(r["pre_course_id"])
            passed = DBManager.exec_query(
                """
                SELECT 1
                FROM edu_grades g
                JOIN edu_teaching t ON g.teaching_id = t.id AND t.is_deleted = 0
                WHERE g.student_id = %s
                  AND t.course_id = %s
                  AND g.score >= 60
                  AND g.is_deleted = 0
                LIMIT 1
                """,
                (student_id, pre_id),
            )
            if not passed:
                raise ValidationError(f"先修课未完成：{r['course_name']}")

    def check_student_scope(self, student_id: int, teaching_id: int) -> None:
        """校验学生选课范围：仅允许本学院且本年级学年的课程。"""
        rows = DBManager.exec_query(
            """
            SELECT
                su.dept_id AS student_dept_id,
                si.grade_year,
                c.dept_id  AS course_dept_id,
                t.semester
            FROM edu_teaching t
            JOIN edu_courses c ON c.id = t.course_id AND c.is_deleted = 0
            JOIN sys_users su ON su.id = %s AND su.role_id = 3 AND su.is_deleted = 0
            LEFT JOIN stu_info si ON si.student_id = su.id AND si.is_deleted = 0
            WHERE t.id = %s
              AND t.is_deleted = 0
            LIMIT 1
            """,
            (student_id, teaching_id),
        )
        if not rows:
            raise ValidationError("学生或教学班不存在。")

        r = rows[0]
        stu_dept = r.get("student_dept_id")
        course_dept = r.get("course_dept_id")
        if stu_dept is not None and course_dept is not None and int(stu_dept) != int(course_dept):
            raise ValidationError("仅允许选择本学院课程。")

        grade_year = r.get("grade_year")
        semester = str(r.get("semester") or "")
        if grade_year is not None and semester:
            try:
                semester_year = int(semester.split("-", 1)[0])
            except ValueError:
                semester_year = None
            if semester_year is not None and int(grade_year) != semester_year:
                raise ValidationError("仅允许选择本年级学年的课程。")

    def check_time_conflict(self, student_id: int, teaching_id: int) -> None:
        target_rows = DBManager.exec_query(
            """
            SELECT t.timeslot, t.semester
            FROM edu_teaching t
            WHERE t.id = %s
              AND t.is_deleted = 0
            LIMIT 1
            """,
            (teaching_id,),
        )
        if not target_rows:
            return

        semester = str(target_rows[0].get("semester") or "")
        target_slots = self.parse_timeslot(str(target_rows[0].get("timeslot") or ""))
        if not target_slots:
            return

        existing_rows = DBManager.exec_query(
            """
            SELECT t.timeslot, c.course_name
            FROM stu_selection s
            JOIN edu_teaching t ON t.id = s.teaching_id AND t.is_deleted = 0
            JOIN edu_courses c ON c.id = t.course_id AND c.is_deleted = 0
            WHERE s.student_id = %s
              AND t.semester = %s
              AND t.id <> %s
                            AND s.deleted_at = 0
            """,
            (student_id, semester, teaching_id),
        )
        for r in existing_rows:
            slots = self.parse_timeslot(str(r.get("timeslot") or ""))
            for a in target_slots:
                for b in slots:
                    if self._has_overlap(a, b):
                        raise ValidationError(f"课程时间冲突：与《{r['course_name']}》冲突")

    def check_exam_conflict(self, student_id: int, teaching_id: int) -> None:
        target_rows = DBManager.exec_query(
            """
            SELECT e.exam_date, e.start_time, e.end_time, t.semester
            FROM edu_teaching t
            JOIN stu_exam_schedule e ON e.course_id = t.course_id
                                    AND e.semester = t.semester
                                    AND e.is_deleted = 0
            WHERE t.id = %s
              AND t.is_deleted = 0
            LIMIT 1
            """,
            (teaching_id,),
        )
        if not target_rows:
            return

        t = target_rows[0]
        semester = str(t.get("semester") or "")
        conflict = DBManager.exec_query(
            """
            SELECT c.course_name
            FROM stu_selection s
            JOIN edu_teaching ts ON ts.id = s.teaching_id AND ts.is_deleted = 0
            JOIN stu_exam_schedule e ON e.course_id = ts.course_id
                                    AND e.semester = ts.semester
                                    AND e.is_deleted = 0
            JOIN edu_courses c ON c.id = ts.course_id AND c.is_deleted = 0
            WHERE s.student_id = %s
              AND ts.semester = %s
              AND ts.id <> %s
                            AND s.deleted_at = 0
              AND e.exam_date = %s
              AND NOT (e.end_time <= %s OR e.start_time >= %s)
            LIMIT 1
            """,
            (student_id, semester, teaching_id, t["exam_date"], t["start_time"], t["end_time"]),
        )
        if conflict:
            raise ValidationError(f"考试时间冲突：与《{conflict[0]['course_name']}》冲突")
