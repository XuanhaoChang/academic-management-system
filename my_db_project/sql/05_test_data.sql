-- ============================================================
-- 05_test_data.sql  完整测试数据（含组员A所需数据）
-- ============================================================
USE my_db_project;

-- 角色
INSERT INTO sys_roles (id, role_name, role_code) VALUES
    (1, '管理员', 'ADMIN'),
    (2, '教师',   'TEACHER'),
    (3, '学生',   'STUDENT')
ON DUPLICATE KEY UPDATE role_name = VALUES(role_name), role_code = VALUES(role_code);

-- 院系
INSERT INTO base_dept (dept_code, dept_name) VALUES
    ('CS', '计算机学院'),
    ('MA', '数学学院')
ON DUPLICATE KEY UPDATE dept_name = VALUES(dept_name);

-- 专业
INSERT INTO base_major (major_code, major_name, dept_id)
SELECT 'SE', '软件工程', d.id FROM base_dept d WHERE d.dept_code = 'CS'
ON DUPLICATE KEY UPDATE major_name = VALUES(major_name);

INSERT INTO base_major (major_code, major_name, dept_id)
SELECT 'AM', '应用数学', d.id FROM base_dept d WHERE d.dept_code = 'MA'
ON DUPLICATE KEY UPDATE major_name = VALUES(major_name);

-- 系统管理员
INSERT INTO sys_users (username, real_name, role_id, password_hash) VALUES
    ('admin', '系统管理员', 1, SHA2('admin123', 256))
ON DUPLICATE KEY UPDATE real_name = VALUES(real_name);

-- 教师账户（密码: teacher123）
INSERT INTO sys_users (username, real_name, role_id, dept_id, password_hash)
SELECT 'teacher01', '张三', 2, d.id, SHA2('teacher123', 256)
FROM base_dept d WHERE d.dept_code = 'CS'
ON DUPLICATE KEY UPDATE real_name = VALUES(real_name);

INSERT INTO sys_users (username, real_name, role_id, dept_id, password_hash)
SELECT 'teacher02', '李四', 2, d.id, SHA2('teacher123', 256)
FROM base_dept d WHERE d.dept_code = 'MA'
ON DUPLICATE KEY UPDATE real_name = VALUES(real_name);

-- 学生账户（密码: student123）
INSERT INTO sys_users (username, real_name, role_id, dept_id, major_id, password_hash)
SELECT 'stu001', '王小明', 3, d.id, m.id, SHA2('student123', 256)
FROM base_dept d JOIN base_major m ON m.dept_id = d.id
WHERE d.dept_code = 'CS' AND m.major_code = 'SE'
ON DUPLICATE KEY UPDATE real_name = VALUES(real_name);

INSERT INTO sys_users (username, real_name, role_id, dept_id, major_id, password_hash)
SELECT 'stu002', '李小红', 3, d.id, m.id, SHA2('student123', 256)
FROM base_dept d JOIN base_major m ON m.dept_id = d.id
WHERE d.dept_code = 'CS' AND m.major_code = 'SE'
ON DUPLICATE KEY UPDATE real_name = VALUES(real_name);

INSERT INTO sys_users (username, real_name, role_id, dept_id, major_id, password_hash)
SELECT 'stu003', '张大海', 3, d.id, m.id, SHA2('student123', 256)
FROM base_dept d JOIN base_major m ON m.dept_id = d.id
WHERE d.dept_code = 'CS' AND m.major_code = 'SE'
ON DUPLICATE KEY UPDATE real_name = VALUES(real_name);

INSERT INTO sys_users (username, real_name, role_id, dept_id, major_id, password_hash)
SELECT 'stu004', '刘明明', 3, d.id, m.id, SHA2('student123', 256)
FROM base_dept d JOIN base_major m ON m.dept_id = d.id
WHERE d.dept_code = 'CS' AND m.major_code = 'SE'
ON DUPLICATE KEY UPDATE real_name = VALUES(real_name);

INSERT INTO sys_users (username, real_name, role_id, dept_id, major_id, password_hash)
SELECT 'stu005', '陈晓晓', 3, d.id, m.id, SHA2('student123', 256)
FROM base_dept d JOIN base_major m ON m.dept_id = d.id
WHERE d.dept_code = 'CS' AND m.major_code = 'SE'
ON DUPLICATE KEY UPDATE real_name = VALUES(real_name);

-- 课程基础信息
INSERT INTO edu_courses (course_code, course_name, credits, dept_id, description)
SELECT 'CS101', '数据库原理', 3.0, d.id, '关系型数据库理论与实践'
FROM base_dept d WHERE d.dept_code = 'CS'
ON DUPLICATE KEY UPDATE course_name = VALUES(course_name);

INSERT INTO edu_courses (course_code, course_name, credits, dept_id, description)
SELECT 'MA201', '高等数学', 4.0, d.id, '微积分基础理论'
FROM base_dept d WHERE d.dept_code = 'MA'
ON DUPLICATE KEY UPDATE course_name = VALUES(course_name);

INSERT INTO edu_courses (course_code, course_name, credits, dept_id, description)
SELECT 'CS102', '程序设计基础', 3.0, d.id, 'Python/Java面向对象程序设计'
FROM base_dept d WHERE d.dept_code = 'CS'
ON DUPLICATE KEY UPDATE course_name = VALUES(course_name);

-- 授课安排（2024-1 学期）
INSERT INTO edu_teaching (course_id, teacher_id, classroom, timeslot, semester, max_count, enrolled_count, status)
SELECT c.id, u.id, 'D101', '周一3-4节,周三3-4节', '2024-1', 50, 5, 'CLOSED'
FROM edu_courses c, sys_users u
WHERE c.course_code = 'CS101' AND u.username = 'teacher01'
ON DUPLICATE KEY UPDATE classroom = VALUES(classroom);

INSERT INTO edu_teaching (course_id, teacher_id, classroom, timeslot, semester, max_count, enrolled_count, status)
SELECT c.id, u.id, 'A201', '周二1-2节,周四1-2节', '2024-1', 80, 5, 'CLOSED'
FROM edu_courses c, sys_users u
WHERE c.course_code = 'MA201' AND u.username = 'teacher02'
ON DUPLICATE KEY UPDATE classroom = VALUES(classroom);

INSERT INTO edu_teaching (course_id, teacher_id, classroom, timeslot, semester, max_count, enrolled_count, status)
SELECT c.id, u.id, 'B301', '周五5-6节', '2024-1', 50, 0, 'OPEN'
FROM edu_courses c, sys_users u
WHERE c.course_code = 'CS102' AND u.username = 'teacher01'
ON DUPLICATE KEY UPDATE classroom = VALUES(classroom);

-- 授课安排（2024-2 当前学期）
INSERT INTO edu_teaching (course_id, teacher_id, classroom, timeslot, semester, max_count, enrolled_count, status)
SELECT c.id, u.id, 'D201', '周二3-4节,周四3-4节', '2024-2', 50, 3, 'OPEN'
FROM edu_courses c, sys_users u
WHERE c.course_code = 'CS101' AND u.username = 'teacher01'
ON DUPLICATE KEY UPDATE classroom = VALUES(classroom);

-- 成绩录入（2024-1 学期，CS101班级）
-- 先找 teaching_id
SET @t_cs101_2024_1 = (
    SELECT t.id FROM edu_teaching t
    JOIN edu_courses c ON t.course_id = c.id
    WHERE c.course_code = 'CS101' AND t.semester = '2024-1'
    LIMIT 1
);

INSERT INTO edu_grades (student_id, teaching_id, score)
SELECT u.id, @t_cs101_2024_1, 92.0
FROM sys_users u WHERE u.username = 'stu001'
ON DUPLICATE KEY UPDATE score=VALUES(score);

INSERT INTO edu_grades (student_id, teaching_id, score)
SELECT u.id, @t_cs101_2024_1, 78.0
FROM sys_users u WHERE u.username = 'stu002'
ON DUPLICATE KEY UPDATE score=VALUES(score);

INSERT INTO edu_grades (student_id, teaching_id, score)
SELECT u.id, @t_cs101_2024_1, 55.0
FROM sys_users u WHERE u.username = 'stu003'
ON DUPLICATE KEY UPDATE score=VALUES(score);

INSERT INTO edu_grades (student_id, teaching_id, score)
SELECT u.id, @t_cs101_2024_1, 85.0
FROM sys_users u WHERE u.username = 'stu004'
ON DUPLICATE KEY UPDATE score=VALUES(score);

INSERT INTO edu_grades (student_id, teaching_id, score)
SELECT u.id, @t_cs101_2024_1, 67.0
FROM sys_users u WHERE u.username = 'stu005'
ON DUPLICATE KEY UPDATE score=VALUES(score);

-- 成绩录入（2024-1 学期，MA201班级）
SET @t_ma201_2024_1 = (
    SELECT t.id FROM edu_teaching t
    JOIN edu_courses c ON t.course_id = c.id
    WHERE c.course_code = 'MA201' AND t.semester = '2024-1'
    LIMIT 1
);

INSERT INTO edu_grades (student_id, teaching_id, score)
SELECT u.id, @t_ma201_2024_1, 74.0
FROM sys_users u WHERE u.username = 'stu001'
ON DUPLICATE KEY UPDATE score=VALUES(score);

INSERT INTO edu_grades (student_id, teaching_id, score)
SELECT u.id, @t_ma201_2024_1, 58.0
FROM sys_users u WHERE u.username = 'stu003'
ON DUPLICATE KEY UPDATE score=VALUES(score);

-- sys_config 初始配置
INSERT INTO sys_config (config_key, config_value) VALUES
    ('current_semester', '2024-2'),
    ('gpa_scale',        '4.0'),
    ('system_name',      '教学管理系统')
ON DUPLICATE KEY UPDATE config_value = VALUES(config_value);

-- ============================================================
-- [组员A 扩展] 平时分记录测试数据 & 调课申请测试数据
-- ============================================================

-- 平时分记录（CS101 2024-2，3种类型 × 3名学生）
SET @dr_t = (
    SELECT t.id FROM edu_teaching t
    JOIN edu_courses c ON t.course_id = c.id
    WHERE c.course_code = 'CS101' AND t.semester = '2024-2'
    LIMIT 1
);
SET @dr_s1 = (SELECT id FROM sys_users WHERE username = 'stu001');
SET @dr_s2 = (SELECT id FROM sys_users WHERE username = 'stu002');
SET @dr_s3 = (SELECT id FROM sys_users WHERE username = 'stu003');

INSERT INTO edu_daily_records (teaching_id, student_id, record_date, record_type, completed) VALUES
    (@dr_t, @dr_s1, '2024-09-09', 'SIGNIN',       1),
    (@dr_t, @dr_s2, '2024-09-09', 'SIGNIN',       1),
    (@dr_t, @dr_s3, '2024-09-09', 'SIGNIN',       0),
    (@dr_t, @dr_s1, '2024-09-16', 'HOMEWORK',     1),
    (@dr_t, @dr_s2, '2024-09-16', 'HOMEWORK',     0),
    (@dr_t, @dr_s3, '2024-09-16', 'HOMEWORK',     1),
    (@dr_t, @dr_s1, '2024-09-23', 'CHAPTER_TEST', 1),
    (@dr_t, @dr_s2, '2024-09-23', 'CHAPTER_TEST', 1),
    (@dr_t, @dr_s3, '2024-09-23', 'CHAPTER_TEST', 0)
ON DUPLICATE KEY UPDATE completed = VALUES(completed);

-- 调课申请测试数据（teacher01 申请调课，状态 PENDING）
SET @req_teacher = (SELECT id FROM sys_users WHERE username = 'teacher01');
SET @req_tid = (
    SELECT t.id FROM edu_teaching t
    JOIN edu_courses c ON t.course_id = c.id
    WHERE c.course_code = 'CS101' AND t.semester = '2024-2'
    LIMIT 1
);

INSERT INTO edu_schedule_change_req
    (teaching_id, teacher_id, reason, original_time, requested_time, status)
VALUES
    (@req_tid, @req_teacher, '与校级教师大会时间冲突', '周二3-4节', '周四5-6节', 'PENDING')
ON DUPLICATE KEY UPDATE reason = VALUES(reason);

SELECT 'Test data inserted successfully.' AS status;
