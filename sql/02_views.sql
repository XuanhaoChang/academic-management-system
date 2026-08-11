-- ============================================================
-- 02_views.sql  高级分析视图
-- 依赖: 01_init_schema.sql 已执行完毕
-- ============================================================
USE my_db_project;

-- ------------------------------------------------------------
-- view_class_ranking
-- 利用窗口函数实现课程内排名 + 跨课程课程排名
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW view_class_ranking AS
SELECT
    g.id                                                          AS grade_id,
    g.student_id,
    g.teaching_id,
    t.course_id,
    t.semester,
    g.score,
    CASE
        WHEN g.score IS NULL THEN NULL
        WHEN g.score >= 90 THEN 4.0
        WHEN g.score >= 80 THEN 3.0
        WHEN g.score >= 70 THEN 2.0
        WHEN g.score >= 60 THEN 1.0
        ELSE 0.0
    END                                                           AS gpa_point,
    CASE
        WHEN g.score IS NULL THEN NULL
        WHEN g.score >= 90 THEN 'A'
        WHEN g.score >= 80 THEN 'B'
        WHEN g.score >= 70 THEN 'C'
        WHEN g.score >= 60 THEN 'D'
        ELSE 'F'
    END                                                           AS grade_letter,
    CASE
        WHEN g.score IS NULL THEN 0
        WHEN g.score >= 60 THEN 1
        ELSE 0
    END                                                           AS is_passed,
    -- 同一授课班级内按成绩排名（并列同名次，下一名次跳过）
    RANK()       OVER (PARTITION BY g.teaching_id ORDER BY g.score DESC) AS rank_in_class,
    -- 同课程所有班级按成绩密集排名
    DENSE_RANK() OVER (PARTITION BY t.course_id   ORDER BY g.score DESC) AS rank_in_course,
    -- 同学期内按成绩排名（全局参考）
    RANK()       OVER (PARTITION BY t.semester     ORDER BY g.score DESC) AS rank_in_semester
FROM edu_grades  g
JOIN edu_teaching t ON g.teaching_id = t.id AND t.is_deleted = 0
WHERE g.is_deleted = 0
  AND g.score IS NOT NULL;

-- ------------------------------------------------------------
-- view_grade_stats
-- 每个授课班级的成绩统计：均值、最高/最低分、标准差、及格率
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW view_grade_stats AS
SELECT
    t.id                                                                              AS teaching_id,
    t.course_id,
    c.course_name,
    c.course_code,
    c.credits,
    t.semester,
    t.classroom,
    t.teacher_id,
    COUNT(g.id)                                                                       AS student_count,
    ROUND(AVG(g.score),    2)                                                         AS avg_score,
    MAX(g.score)                                                                      AS max_score,
    MIN(g.score)                                                                      AS min_score,
    ROUND(STDDEV(g.score), 2)                                                         AS std_dev,
    ROUND(
        SUM(CASE WHEN g.score >= 60 THEN 1 ELSE 0 END) * 100.0
        / NULLIF(COUNT(g.id), 0),
    2)                                                                                AS pass_rate,
    -- 各分段人数（可视化用）
    SUM(CASE WHEN g.score <  60                    THEN 1 ELSE 0 END)                AS cnt_below_60,
    SUM(CASE WHEN g.score >= 60 AND g.score < 70   THEN 1 ELSE 0 END)                AS cnt_60_69,
    SUM(CASE WHEN g.score >= 70 AND g.score < 80   THEN 1 ELSE 0 END)                AS cnt_70_79,
    SUM(CASE WHEN g.score >= 80 AND g.score < 90   THEN 1 ELSE 0 END)                AS cnt_80_89,
    SUM(CASE WHEN g.score >= 90                    THEN 1 ELSE 0 END)                AS cnt_90_100
FROM edu_teaching t
JOIN edu_courses  c ON t.course_id = c.id AND c.is_deleted = 0
LEFT JOIN edu_grades g
    ON g.teaching_id = t.id AND g.is_deleted = 0 AND g.score IS NOT NULL
WHERE t.is_deleted = 0
GROUP BY t.id, t.course_id, c.course_name, c.course_code, c.credits,
         t.semester, t.classroom, t.teacher_id;

-- ------------------------------------------------------------
-- view_student_gpa
-- 每位学生的加权 GPA 汇总（跨所有已录入成绩的课程）
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW view_student_gpa AS
SELECT
    g.student_id,
    u.username,
    u.real_name,
    COUNT(g.id)                                                             AS course_count,
    ROUND(
        SUM(
            CASE
                WHEN g.score >= 90 THEN 4.0
                WHEN g.score >= 80 THEN 3.0
                WHEN g.score >= 70 THEN 2.0
                WHEN g.score >= 60 THEN 1.0
                ELSE 0.0
            END * c.credits
        ) / NULLIF(SUM(c.credits), 0),
    2)                                                                      AS weighted_gpa,
    SUM(c.credits)                                                          AS total_credits
FROM edu_grades  g
JOIN edu_teaching t ON g.teaching_id = t.id AND t.is_deleted = 0
JOIN edu_courses  c ON t.course_id   = c.id AND c.is_deleted = 0
JOIN sys_users    u ON g.student_id  = u.id AND u.is_deleted = 0
WHERE g.is_deleted = 0 AND g.score IS NOT NULL
GROUP BY g.student_id, u.username, u.real_name;
