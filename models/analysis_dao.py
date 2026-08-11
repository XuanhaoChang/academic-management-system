"""AnalysisDAO — 高级查询数据访问层

所有查询均通过 DBManager.exec_query 执行，返回字典列表。
"""
from __future__ import annotations

from core.db_manager import DBManager


class AnalysisDAO:
    # ------------------------------------------------------------------
    # 成绩分布（可视化用）
    # ------------------------------------------------------------------
    def get_score_distribution(self, teaching_id: int) -> dict:
        """返回指定授课班级的成绩分段统计及汇总指标。

        返回单行字典，包含:
            below_60, cnt_60_69, cnt_70_79, cnt_80_89, cnt_90_100,
            total, avg_score, max_score, min_score, std_dev, pass_rate
        """
        sql = """
            SELECT
                SUM(CASE WHEN score < 60                  THEN 1 ELSE 0 END) AS below_60,
                SUM(CASE WHEN score >= 60 AND score < 70  THEN 1 ELSE 0 END) AS cnt_60_69,
                SUM(CASE WHEN score >= 70 AND score < 80  THEN 1 ELSE 0 END) AS cnt_70_79,
                SUM(CASE WHEN score >= 80 AND score < 90  THEN 1 ELSE 0 END) AS cnt_80_89,
                SUM(CASE WHEN score >= 90                 THEN 1 ELSE 0 END) AS cnt_90_100,
                COUNT(id)                                                     AS total,
                ROUND(AVG(score),    2)                                       AS avg_score,
                MAX(score)                                                    AS max_score,
                MIN(score)                                                    AS min_score,
                ROUND(STDDEV(score), 2)                                       AS std_dev,
                ROUND(
                    SUM(CASE WHEN score >= 60 THEN 1 ELSE 0 END)
                    * 100.0 / NULLIF(COUNT(id), 0),
                2)                                                            AS pass_rate
            FROM edu_grades
            WHERE teaching_id = %s AND is_deleted = 0 AND score IS NOT NULL
        """
        rows = DBManager.exec_query(sql, (teaching_id,))
        return rows[0] if rows else {}

    # ------------------------------------------------------------------
    # 挂科预警
    # ------------------------------------------------------------------
    def get_failed_students_warning(self) -> list[dict]:
        """返回所有有不及格记录的学生列表（含课程信息）。"""
        sql = """
            SELECT
                u.id          AS student_id,
                u.username,
                u.real_name,
                c.course_name,
                c.course_code,
                t.semester,
                g.score,
                CASE
                    WHEN g.score IS NULL THEN NULL
                    WHEN g.score >= 90 THEN 'A'
                    WHEN g.score >= 80 THEN 'B'
                    WHEN g.score >= 70 THEN 'C'
                    WHEN g.score >= 60 THEN 'D'
                    ELSE 'F'
                END AS grade_letter
            FROM edu_grades  g
            JOIN sys_users   u ON g.student_id  = u.id AND u.is_deleted = 0
            JOIN edu_teaching t ON g.teaching_id = t.id AND t.is_deleted = 0
            JOIN edu_courses  c ON t.course_id   = c.id AND c.is_deleted = 0
            WHERE g.score      < 60
              AND g.is_deleted = 0
              AND g.score IS NOT NULL
            ORDER BY t.semester DESC, u.real_name, c.course_name
        """
        return DBManager.exec_query(sql)

    # ------------------------------------------------------------------
    # 课程内排名（来自视图）
    # ------------------------------------------------------------------
    def get_course_ranking(self, teaching_id: int) -> list[dict]:
        """返回指定授课班级的学生排名（来自 view_class_ranking + sys_users）。"""
        sql = """
            SELECT
                r.student_id,
                u.username,
                u.real_name,
                r.score,
                r.gpa_point,
                r.grade_letter,
                r.is_passed,
                r.rank_in_class
            FROM view_class_ranking r
            JOIN sys_users u ON r.student_id = u.id AND u.is_deleted = 0
            WHERE r.teaching_id = %s
            ORDER BY r.rank_in_class
        """
        return DBManager.exec_query(sql, (teaching_id,))

    # ------------------------------------------------------------------
    # 授课班级统计（来自视图）
    # ------------------------------------------------------------------
    def get_teaching_stats(self, teaching_id: int) -> dict:
        """返回 view_grade_stats 中指定授课班级的统计行。"""
        sql = "SELECT * FROM view_grade_stats WHERE teaching_id = %s"
        rows = DBManager.exec_query(sql, (teaching_id,))
        return rows[0] if rows else {}

    # ------------------------------------------------------------------
    # 学生 GPA 汇总（来自视图）
    # ------------------------------------------------------------------
    def get_student_gpa_list(self) -> list[dict]:
        """返回所有学生的加权 GPA 汇总（来自 view_student_gpa）。"""
        sql = """
            SELECT student_id, username, real_name, course_count,
                   weighted_gpa, total_credits
            FROM view_student_gpa
            ORDER BY weighted_gpa DESC
        """
        return DBManager.exec_query(sql)

    # ------------------------------------------------------------------
    # 平时分汇总（来自 view_daily_score）
    # ------------------------------------------------------------------
    def get_daily_score_summary(self, teaching_id: int) -> list[dict]:
        """返回指定授课班级所有学生的平时分汇总。

        字段: student_id, username, real_name,
              total_records, completed_records, completion_rate, daily_score
        """
        sql = """
            SELECT
                ds.student_id,
                u.username,
                u.real_name,
                ds.total_records,
                ds.completed_records,
                ds.completion_rate,
                ds.daily_score
            FROM view_daily_score ds
            JOIN sys_users u ON ds.student_id = u.id AND u.is_deleted = 0
            WHERE ds.teaching_id = %s
            ORDER BY u.real_name
        """
        return DBManager.exec_query(sql, (teaching_id,))

    # ------------------------------------------------------------------
    # 历史归档成绩查询（按教师+学期）
    # ------------------------------------------------------------------
    def get_archive_by_teacher(self, teacher_id: int, semester: str) -> list[dict]:
        """返回指定教师在指定学期的归档成绩记录。

        字段: archive_id, student_id, username, real_name,
              course_name, course_code, credits, score, gpa_point,
              grade_letter, is_passed, semester, archived_at
        """
        sql = """
            SELECT
                a.id           AS archive_id,
                a.student_id,
                u.username,
                u.real_name,
                c.course_name,
                c.course_code,
                c.credits,
                a.score,
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
                END AS is_passed,
                t.semester,
                a.archived_at
            FROM edu_archives  a
            JOIN edu_teaching  t ON a.teaching_id = t.id AND t.is_deleted = 0
            JOIN edu_courses   c ON t.course_id   = c.id AND c.is_deleted = 0
            JOIN sys_users     u ON a.student_id  = u.id AND u.is_deleted = 0
            WHERE t.teacher_id = %s
              AND t.semester   = %s
              AND a.is_deleted = 0
            ORDER BY c.course_name, u.real_name
        """
        return DBManager.exec_query(sql, (teacher_id, semester))
