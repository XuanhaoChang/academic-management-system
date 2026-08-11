-- ============================================================
-- 07_teacher_demo_data.sql  教师端演示数据
-- 包含：更多学生、多个课程、丰富的成绩数据、平时分记录
-- ============================================================
USE my_db_project;

-- ------------------------------------------------------------
-- 1. 添加更多学生（20名学生用于演示）
-- ------------------------------------------------------------
INSERT INTO sys_users (username, real_name, role_id, dept_id, major_id, password_hash)
SELECT 'stu006', '赵敏', 3, d.id, m.id, SHA2('student123', 256)
FROM base_dept d JOIN base_major m ON m.dept_id = d.id
WHERE d.dept_code = 'CS' AND m.major_code = 'SE'
ON DUPLICATE KEY UPDATE real_name = VALUES(real_name);

INSERT INTO sys_users (username, real_name, role_id, dept_id, major_id, password_hash)
SELECT 'stu007', '周芷若', 3, d.id, m.id, SHA2('student123', 256)
FROM base_dept d JOIN base_major m ON m.dept_id = d.id
WHERE d.dept_code = 'CS' AND m.major_code = 'SE'
ON DUPLICATE KEY UPDATE real_name = VALUES(real_name);

INSERT INTO sys_users (username, real_name, role_id, dept_id, major_id, password_hash)
SELECT 'stu008', '张无忌', 3, d.id, m.id, SHA2('student123', 256)
FROM base_dept d JOIN base_major m ON m.dept_id = d.id
WHERE d.dept_code = 'CS' AND m.major_code = 'SE'
ON DUPLICATE KEY UPDATE real_name = VALUES(real_name);

INSERT INTO sys_users (username, real_name, role_id, dept_id, major_id, password_hash)
SELECT 'stu009', '杨过', 3, d.id, m.id, SHA2('student123', 256)
FROM base_dept d JOIN base_major m ON m.dept_id = d.id
WHERE d.dept_code = 'CS' AND m.major_code = 'SE'
ON DUPLICATE KEY UPDATE real_name = VALUES(real_name);

INSERT INTO sys_users (username, real_name, role_id, dept_id, major_id, password_hash)
SELECT 'stu010', '小龙女', 3, d.id, m.id, SHA2('student123', 256)
FROM base_dept d JOIN base_major m ON m.dept_id = d.id
WHERE d.dept_code = 'CS' AND m.major_code = 'SE'
ON DUPLICATE KEY UPDATE real_name = VALUES(real_name);

INSERT INTO sys_users (username, real_name, role_id, dept_id, major_id, password_hash)
SELECT 'stu011', '郭靖', 3, d.id, m.id, SHA2('student123', 256)
FROM base_dept d JOIN base_major m ON m.dept_id = d.id
WHERE d.dept_code = 'CS' AND m.major_code = 'SE'
ON DUPLICATE KEY UPDATE real_name = VALUES(real_name);

INSERT INTO sys_users (username, real_name, role_id, dept_id, major_id, password_hash)
SELECT 'stu012', '黄蓉', 3, d.id, m.id, SHA2('student123', 256)
FROM base_dept d JOIN base_major m ON m.dept_id = d.id
WHERE d.dept_code = 'CS' AND m.major_code = 'SE'
ON DUPLICATE KEY UPDATE real_name = VALUES(real_name);

INSERT INTO sys_users (username, real_name, role_id, dept_id, major_id, password_hash)
SELECT 'stu013', '令狐冲', 3, d.id, m.id, SHA2('student123', 256)
FROM base_dept d JOIN base_major m ON m.dept_id = d.id
WHERE d.dept_code = 'CS' AND m.major_code = 'SE'
ON DUPLICATE KEY UPDATE real_name = VALUES(real_name);

INSERT INTO sys_users (username, real_name, role_id, dept_id, major_id, password_hash)
SELECT 'stu014', '任盈盈', 3, d.id, m.id, SHA2('student123', 256)
FROM base_dept d JOIN base_major m ON m.dept_id = d.id
WHERE d.dept_code = 'CS' AND m.major_code = 'SE'
ON DUPLICATE KEY UPDATE real_name = VALUES(real_name);

INSERT INTO sys_users (username, real_name, role_id, dept_id, major_id, password_hash)
SELECT 'stu015', '韦小宝', 3, d.id, m.id, SHA2('student123', 256)
FROM base_dept d JOIN base_major m ON m.dept_id = d.id
WHERE d.dept_code = 'CS' AND m.major_code = 'SE'
ON DUPLICATE KEY UPDATE real_name = VALUES(real_name);

INSERT INTO sys_users (username, real_name, role_id, dept_id, major_id, password_hash)
SELECT 'stu016', '陈家洛', 3, d.id, m.id, SHA2('student123', 256)
FROM base_dept d JOIN base_major m ON m.dept_id = d.id
WHERE d.dept_code = 'CS' AND m.major_code = 'SE'
ON DUPLICATE KEY UPDATE real_name = VALUES(real_name);

INSERT INTO sys_users (username, real_name, role_id, dept_id, major_id, password_hash)
SELECT 'stu017', '袁承志', 3, d.id, m.id, SHA2('student123', 256)
FROM base_dept d JOIN base_major m ON m.dept_id = d.id
WHERE d.dept_code = 'CS' AND m.major_code = 'SE'
ON DUPLICATE KEY UPDATE real_name = VALUES(real_name);

INSERT INTO sys_users (username, real_name, role_id, dept_id, major_id, password_hash)
SELECT 'stu018', '胡斐', 3, d.id, m.id, SHA2('student123', 256)
FROM base_dept d JOIN base_major m ON m.dept_id = d.id
WHERE d.dept_code = 'CS' AND m.major_code = 'SE'
ON DUPLICATE KEY UPDATE real_name = VALUES(real_name);

INSERT INTO sys_users (username, real_name, role_id, dept_id, major_id, password_hash)
SELECT 'stu019', '苗若兰', 3, d.id, m.id, SHA2('student123', 256)
FROM base_dept d JOIN base_major m ON m.dept_id = d.id
WHERE d.dept_code = 'CS' AND m.major_code = 'SE'
ON DUPLICATE KEY UPDATE real_name = VALUES(real_name);

INSERT INTO sys_users (username, real_name, role_id, dept_id, major_id, password_hash)
SELECT 'stu020', '石破天', 3, d.id, m.id, SHA2('student123', 256)
FROM base_dept d JOIN base_major m ON m.dept_id = d.id
WHERE d.dept_code = 'CS' AND m.major_code = 'SE'
ON DUPLICATE KEY UPDATE real_name = VALUES(real_name);

-- ------------------------------------------------------------
-- 2. 添加更多课程
-- ------------------------------------------------------------
INSERT INTO edu_courses (course_code, course_name, credits, dept_id, description)
SELECT 'CS103', '数据结构与算法', 4.0, d.id, '线性表、树、图、排序与查找算法'
FROM base_dept d WHERE d.dept_code = 'CS'
ON DUPLICATE KEY UPDATE course_name = VALUES(course_name);

INSERT INTO edu_courses (course_code, course_name, credits, dept_id, description)
SELECT 'CS104', '操作系统', 3.5, d.id, '进程管理、内存管理、文件系统'
FROM base_dept d WHERE d.dept_code = 'CS'
ON DUPLICATE KEY UPDATE course_name = VALUES(course_name);

INSERT INTO edu_courses (course_code, course_name, credits, dept_id, description)
SELECT 'CS105', '计算机网络', 3.0, d.id, 'TCP/IP协议栈、网络编程'
FROM base_dept d WHERE d.dept_code = 'CS'
ON DUPLICATE KEY UPDATE course_name = VALUES(course_name);

INSERT INTO edu_courses (course_code, course_name, credits, dept_id, description)
SELECT 'CS106', 'Web开发技术', 3.0, d.id, 'HTML/CSS/JavaScript、前后端开发'
FROM base_dept d WHERE d.dept_code = 'CS'
ON DUPLICATE KEY UPDATE course_name = VALUES(course_name);

-- ------------------------------------------------------------
-- 3. 为 teacher01 添加更多授课班级（2024-2 学期）
-- ------------------------------------------------------------
INSERT INTO edu_teaching (course_id, teacher_id, classroom, timeslot, semester, max_count, enrolled_count, status)
SELECT c.id, u.id, 'D301', '周一5-6节,周三5-6节', '2024-2', 60, 20, 'OPEN'
FROM edu_courses c, sys_users u
WHERE c.course_code = 'CS103' AND u.username = 'teacher01'
ON DUPLICATE KEY UPDATE classroom = VALUES(classroom);

INSERT INTO edu_teaching (course_id, teacher_id, classroom, timeslot, semester, max_count, enrolled_count, status)
SELECT c.id, u.id, 'D401', '周二5-6节,周四5-6节', '2024-2', 50, 18, 'OPEN'
FROM edu_courses c, sys_users u
WHERE c.course_code = 'CS104' AND u.username = 'teacher01'
ON DUPLICATE KEY UPDATE classroom = VALUES(classroom);

-- ------------------------------------------------------------
-- 4. 为 CS101 2024-2 班级添加完整成绩数据（20名学生）
-- ------------------------------------------------------------
SET @tid_cs101_2024_2 = (
    SELECT t.id FROM edu_teaching t
    JOIN edu_courses c ON t.course_id = c.id
    WHERE c.course_code = 'CS101' AND t.semester = '2024-2'
    LIMIT 1
);

-- 为所有20名学生添加成绩记录（包含卷面成绩和平时分）
INSERT INTO edu_grades (student_id, teaching_id, exam_score, score)
SELECT u.id, @tid_cs101_2024_2, 
    CASE u.username
        WHEN 'stu001' THEN 88.0
        WHEN 'stu002' THEN 92.5
        WHEN 'stu003' THEN 45.0
        WHEN 'stu004' THEN 78.5
        WHEN 'stu005' THEN 65.0
        WHEN 'stu006' THEN 95.0
        WHEN 'stu007' THEN 82.0
        WHEN 'stu008' THEN 58.5
        WHEN 'stu009' THEN 91.0
        WHEN 'stu010' THEN 87.5
        WHEN 'stu011' THEN 73.0
        WHEN 'stu012' THEN 96.5
        WHEN 'stu013' THEN 52.0
        WHEN 'stu014' THEN 89.0
        WHEN 'stu015' THEN 67.5
        WHEN 'stu016' THEN 84.0
        WHEN 'stu017' THEN 76.5
        WHEN 'stu018' THEN 93.0
        WHEN 'stu019' THEN 48.0
        WHEN 'stu020' THEN 81.5
    END,
    CASE u.username
        WHEN 'stu001' THEN 85.6
        WHEN 'stu002' THEN 89.8
        WHEN 'stu003' THEN 49.5
        WHEN 'stu004' THEN 77.0
        WHEN 'stu005' THEN 65.5
        WHEN 'stu006' THEN 92.5
        WHEN 'stu007' THEN 81.4
        WHEN 'stu008' THEN 59.0
        WHEN 'stu009' THEN 88.7
        WHEN 'stu010' THEN 85.3
        WHEN 'stu011' THEN 73.1
        WHEN 'stu012' THEN 93.6
        WHEN 'stu013' THEN 54.4
        WHEN 'stu014' THEN 86.3
        WHEN 'stu015' THEN 67.3
        WHEN 'stu016' THEN 82.8
        WHEN 'stu017' THEN 75.6
        WHEN 'stu018' THEN 90.1
        WHEN 'stu019' THEN 51.6
        WHEN 'stu020' THEN 80.1
    END
FROM sys_users u
WHERE u.username IN (
    'stu001', 'stu002', 'stu003', 'stu004', 'stu005',
    'stu006', 'stu007', 'stu008', 'stu009', 'stu010',
    'stu011', 'stu012', 'stu013', 'stu014', 'stu015',
    'stu016', 'stu017', 'stu018', 'stu019', 'stu020'
)
ON DUPLICATE KEY UPDATE 
    exam_score = VALUES(exam_score),
    score = VALUES(score);

-- ------------------------------------------------------------
-- 5. 为 CS103 2024-2 班级添加成绩数据
-- ------------------------------------------------------------
SET @tid_cs103_2024_2 = (
    SELECT t.id FROM edu_teaching t
    JOIN edu_courses c ON t.course_id = c.id
    WHERE c.course_code = 'CS103' AND t.semester = '2024-2'
    LIMIT 1
);

INSERT INTO edu_grades (student_id, teaching_id, exam_score, score)
SELECT u.id, @tid_cs103_2024_2, 
    CASE u.username
        WHEN 'stu001' THEN 85.0
        WHEN 'stu002' THEN 90.0
        WHEN 'stu003' THEN 52.0
        WHEN 'stu004' THEN 75.0
        WHEN 'stu005' THEN 68.0
        WHEN 'stu006' THEN 93.0
        WHEN 'stu007' THEN 80.0
        WHEN 'stu008' THEN 55.0
        WHEN 'stu009' THEN 88.0
        WHEN 'stu010' THEN 84.0
        WHEN 'stu011' THEN 71.0
        WHEN 'stu012' THEN 94.0
        WHEN 'stu013' THEN 49.0
        WHEN 'stu014' THEN 86.0
        WHEN 'stu015' THEN 64.0
        WHEN 'stu016' THEN 82.0
        WHEN 'stu017' THEN 74.0
        WHEN 'stu018' THEN 91.0
        WHEN 'stu019' THEN 46.0
        WHEN 'stu020' THEN 79.0
    END,
    CASE u.username
        WHEN 'stu001' THEN 83.5
        WHEN 'stu002' THEN 87.0
        WHEN 'stu003' THEN 54.4
        WHEN 'stu004' THEN 74.5
        WHEN 'stu005' THEN 67.6
        WHEN 'stu006' THEN 90.1
        WHEN 'stu007' THEN 79.0
        WHEN 'stu008' THEN 56.5
        WHEN 'stu009' THEN 85.6
        WHEN 'stu010' THEN 82.8
        WHEN 'stu011' THEN 71.7
        WHEN 'stu012' THEN 91.8
        WHEN 'stu013' THEN 51.3
        WHEN 'stu014' THEN 84.2
        WHEN 'stu015' THEN 64.8
        WHEN 'stu016' THEN 80.4
        WHEN 'stu017' THEN 73.8
        WHEN 'stu018' THEN 88.7
        WHEN 'stu019' THEN 48.2
        WHEN 'stu020' THEN 77.3
    END
FROM sys_users u
WHERE u.username IN (
    'stu001', 'stu002', 'stu003', 'stu004', 'stu005',
    'stu006', 'stu007', 'stu008', 'stu009', 'stu010',
    'stu011', 'stu012', 'stu013', 'stu014', 'stu015',
    'stu016', 'stu017', 'stu018', 'stu019', 'stu020'
)
ON DUPLICATE KEY UPDATE 
    exam_score = VALUES(exam_score),
    score = VALUES(score);

-- ------------------------------------------------------------
-- 6. 为 CS104 2024-2 班级添加成绩数据
-- ------------------------------------------------------------
SET @tid_cs104_2024_2 = (
    SELECT t.id FROM edu_teaching t
    JOIN edu_courses c ON t.course_id = c.id
    WHERE c.course_code = 'CS104' AND t.semester = '2024-2'
    LIMIT 1
);

INSERT INTO edu_grades (student_id, teaching_id, exam_score, score)
SELECT u.id, @tid_cs104_2024_2, 
    CASE u.username
        WHEN 'stu001' THEN 82.0
        WHEN 'stu002' THEN 88.0
        WHEN 'stu003' THEN 58.0
        WHEN 'stu004' THEN 72.0
        WHEN 'stu005' THEN 66.0
        WHEN 'stu006' THEN 91.0
        WHEN 'stu007' THEN 78.0
        WHEN 'stu008' THEN 53.0
        WHEN 'stu009' THEN 85.0
        WHEN 'stu010' THEN 81.0
        WHEN 'stu011' THEN 69.0
        WHEN 'stu012' THEN 92.0
        WHEN 'stu013' THEN 47.0
        WHEN 'stu014' THEN 83.0
        WHEN 'stu015' THEN 62.0
        WHEN 'stu016' THEN 80.0
        WHEN 'stu017' THEN 71.0
        WHEN 'stu018' THEN 89.0
    END,
    CASE u.username
        WHEN 'stu001' THEN 80.4
        WHEN 'stu002' THEN 85.6
        WHEN 'stu003' THEN 59.6
        WHEN 'stu004' THEN 71.4
        WHEN 'stu005' THEN 65.2
        WHEN 'stu006' THEN 88.7
        WHEN 'stu007' THEN 77.6
        WHEN 'stu008' THEN 54.1
        WHEN 'stu009' THEN 83.5
        WHEN 'stu010' THEN 79.7
        WHEN 'stu011' THEN 68.3
        WHEN 'stu012' THEN 89.4
        WHEN 'stu013' THEN 49.9
        WHEN 'stu014' THEN 81.1
        WHEN 'stu015' THEN 61.4
        WHEN 'stu016' THEN 78.0
        WHEN 'stu017' THEN 70.7
        WHEN 'stu018' THEN 86.3
    END
FROM sys_users u
WHERE u.username IN (
    'stu001', 'stu002', 'stu003', 'stu004', 'stu005',
    'stu006', 'stu007', 'stu008', 'stu009', 'stu010',
    'stu011', 'stu012', 'stu013', 'stu014', 'stu015',
    'stu016', 'stu017', 'stu018'
)
ON DUPLICATE KEY UPDATE 
    exam_score = VALUES(exam_score),
    score = VALUES(score);

-- ------------------------------------------------------------
-- 7. 丰富的平时分记录（CS101 2024-2，模拟一个学期的记录）
-- ------------------------------------------------------------

-- 第1周签到（2024-09-02）
INSERT INTO edu_daily_records (teaching_id, student_id, record_date, record_type, completed, note) VALUES
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu001'), '2024-09-02', 'SIGNIN', 1, '准时到达'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu002'), '2024-09-02', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu003'), '2024-09-02', 'SIGNIN', 0, '缺勤'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu004'), '2024-09-02', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu005'), '2024-09-02', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu006'), '2024-09-02', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu007'), '2024-09-02', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu008'), '2024-09-02', 'SIGNIN', 0, '迟到'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu009'), '2024-09-02', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu010'), '2024-09-02', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu011'), '2024-09-02', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu012'), '2024-09-02', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu013'), '2024-09-02', 'SIGNIN', 0, '请假'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu014'), '2024-09-02', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu015'), '2024-09-02', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu016'), '2024-09-02', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu017'), '2024-09-02', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu018'), '2024-09-02', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu019'), '2024-09-02', 'SIGNIN', 0, '缺勤'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu020'), '2024-09-02', 'SIGNIN', 1, NULL)
ON DUPLICATE KEY UPDATE completed = VALUES(completed);

-- 第2周签到（2024-09-09）
INSERT INTO edu_daily_records (teaching_id, student_id, record_date, record_type, completed, note) VALUES
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu001'), '2024-09-09', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu002'), '2024-09-09', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu003'), '2024-09-09', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu004'), '2024-09-09', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu005'), '2024-09-09', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu006'), '2024-09-09', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu007'), '2024-09-09', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu008'), '2024-09-09', 'SIGNIN', 0, '缺勤'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu009'), '2024-09-09', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu010'), '2024-09-09', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu011'), '2024-09-09', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu012'), '2024-09-09', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu013'), '2024-09-09', 'SIGNIN', 0, '缺勤'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu014'), '2024-09-09', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu015'), '2024-09-09', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu016'), '2024-09-09', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu017'), '2024-09-09', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu018'), '2024-09-09', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu019'), '2024-09-09', 'SIGNIN', 0, '缺勤'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu020'), '2024-09-09', 'SIGNIN', 1, NULL)
ON DUPLICATE KEY UPDATE completed = VALUES(completed);

-- 第1次作业（2024-09-10）
INSERT INTO edu_daily_records (teaching_id, student_id, record_date, record_type, completed, note) VALUES
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu001'), '2024-09-10', 'HOMEWORK', 1, '优秀'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu002'), '2024-09-10', 'HOMEWORK', 1, '优秀'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu003'), '2024-09-10', 'HOMEWORK', 0, '未交'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu004'), '2024-09-10', 'HOMEWORK', 1, '良好'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu005'), '2024-09-10', 'HOMEWORK', 1, '及格'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu006'), '2024-09-10', 'HOMEWORK', 1, '优秀'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu007'), '2024-09-10', 'HOMEWORK', 1, '良好'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu008'), '2024-09-10', 'HOMEWORK', 0, '未交'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu009'), '2024-09-10', 'HOMEWORK', 1, '优秀'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu010'), '2024-09-10', 'HOMEWORK', 1, '良好'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu011'), '2024-09-10', 'HOMEWORK', 1, '及格'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu012'), '2024-09-10', 'HOMEWORK', 1, '优秀'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu013'), '2024-09-10', 'HOMEWORK', 0, '未交'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu014'), '2024-09-10', 'HOMEWORK', 1, '优秀'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu015'), '2024-09-10', 'HOMEWORK', 1, '及格'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu016'), '2024-09-10', 'HOMEWORK', 1, '良好'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu017'), '2024-09-10', 'HOMEWORK', 1, '良好'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu018'), '2024-09-10', 'HOMEWORK', 1, '优秀'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu019'), '2024-09-10', 'HOMEWORK', 0, '未交'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu020'), '2024-09-10', 'HOMEWORK', 1, '良好')
ON DUPLICATE KEY UPDATE completed = VALUES(completed);

-- 第3周签到（2024-09-16）
INSERT INTO edu_daily_records (teaching_id, student_id, record_date, record_type, completed, note) VALUES
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu001'), '2024-09-16', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu002'), '2024-09-16', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu003'), '2024-09-16', 'SIGNIN', 0, '缺勤'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu004'), '2024-09-16', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu005'), '2024-09-16', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu006'), '2024-09-16', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu007'), '2024-09-16', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu008'), '2024-09-16', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu009'), '2024-09-16', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu010'), '2024-09-16', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu011'), '2024-09-16', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu012'), '2024-09-16', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu013'), '2024-09-16', 'SIGNIN', 0, '缺勤'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu014'), '2024-09-16', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu015'), '2024-09-16', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu016'), '2024-09-16', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu017'), '2024-09-16', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu018'), '2024-09-16', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu019'), '2024-09-16', 'SIGNIN', 0, '缺勤'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu020'), '2024-09-16', 'SIGNIN', 1, NULL)
ON DUPLICATE KEY UPDATE completed = VALUES(completed);

-- 第1次章节测验（2024-09-18）
INSERT INTO edu_daily_records (teaching_id, student_id, record_date, record_type, completed, note) VALUES
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu001'), '2024-09-18', 'CHAPTER_TEST', 1, '90分'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu002'), '2024-09-18', 'CHAPTER_TEST', 1, '95分'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu003'), '2024-09-18', 'CHAPTER_TEST', 0, '缺考'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu004'), '2024-09-18', 'CHAPTER_TEST', 1, '82分'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu005'), '2024-09-18', 'CHAPTER_TEST', 1, '70分'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu006'), '2024-09-18', 'CHAPTER_TEST', 1, '98分'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu007'), '2024-09-18', 'CHAPTER_TEST', 1, '85分'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu008'), '2024-09-18', 'CHAPTER_TEST', 0, '缺考'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu009'), '2024-09-18', 'CHAPTER_TEST', 1, '92分'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu010'), '2024-09-18', 'CHAPTER_TEST', 1, '88分'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu011'), '2024-09-18', 'CHAPTER_TEST', 1, '75分'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu012'), '2024-09-18', 'CHAPTER_TEST', 1, '96分'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu013'), '2024-09-18', 'CHAPTER_TEST', 0, '缺考'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu014'), '2024-09-18', 'CHAPTER_TEST', 1, '89分'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu015'), '2024-09-18', 'CHAPTER_TEST', 1, '68分'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu016'), '2024-09-18', 'CHAPTER_TEST', 1, '84分'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu017'), '2024-09-18', 'CHAPTER_TEST', 1, '78分'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu018'), '2024-09-18', 'CHAPTER_TEST', 1, '93分'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu019'), '2024-09-18', 'CHAPTER_TEST', 0, '缺考'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu020'), '2024-09-18', 'CHAPTER_TEST', 1, '81分')
ON DUPLICATE KEY UPDATE completed = VALUES(completed);

-- 第4周签到（2024-09-23）
INSERT INTO edu_daily_records (teaching_id, student_id, record_date, record_type, completed, note) VALUES
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu001'), '2024-09-23', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu002'), '2024-09-23', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu003'), '2024-09-23', 'SIGNIN', 0, '缺勤'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu004'), '2024-09-23', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu005'), '2024-09-23', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu006'), '2024-09-23', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu007'), '2024-09-23', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu008'), '2024-09-23', 'SIGNIN', 0, '迟到'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu009'), '2024-09-23', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu010'), '2024-09-23', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu011'), '2024-09-23', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu012'), '2024-09-23', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu013'), '2024-09-23', 'SIGNIN', 0, '缺勤'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu014'), '2024-09-23', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu015'), '2024-09-23', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu016'), '2024-09-23', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu017'), '2024-09-23', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu018'), '2024-09-23', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu019'), '2024-09-23', 'SIGNIN', 0, '缺勤'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu020'), '2024-09-23', 'SIGNIN', 1, NULL)
ON DUPLICATE KEY UPDATE completed = VALUES(completed);

-- 第2次作业（2024-09-25）
INSERT INTO edu_daily_records (teaching_id, student_id, record_date, record_type, completed, note) VALUES
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu001'), '2024-09-25', 'HOMEWORK', 1, '优秀'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu002'), '2024-09-25', 'HOMEWORK', 1, '优秀'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu003'), '2024-09-25', 'HOMEWORK', 0, '未交'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu004'), '2024-09-25', 'HOMEWORK', 1, '良好'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu005'), '2024-09-25', 'HOMEWORK', 1, '及格'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu006'), '2024-09-25', 'HOMEWORK', 1, '优秀'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu007'), '2024-09-25', 'HOMEWORK', 1, '良好'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu008'), '2024-09-25', 'HOMEWORK', 0, '未交'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu009'), '2024-09-25', 'HOMEWORK', 1, '优秀'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu010'), '2024-09-25', 'HOMEWORK', 1, '优秀'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu011'), '2024-09-25', 'HOMEWORK', 1, '良好'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu012'), '2024-09-25', 'HOMEWORK', 1, '优秀'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu013'), '2024-09-25', 'HOMEWORK', 0, '未交'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu014'), '2024-09-25', 'HOMEWORK', 1, '优秀'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu015'), '2024-09-25', 'HOMEWORK', 1, '及格'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu016'), '2024-09-25', 'HOMEWORK', 1, '良好'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu017'), '2024-09-25', 'HOMEWORK', 1, '良好'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu018'), '2024-09-25', 'HOMEWORK', 1, '优秀'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu019'), '2024-09-25', 'HOMEWORK', 0, '未交'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu020'), '2024-09-25', 'HOMEWORK', 1, '良好')
ON DUPLICATE KEY UPDATE completed = VALUES(completed);

-- 第5周签到（2024-09-30）
INSERT INTO edu_daily_records (teaching_id, student_id, record_date, record_type, completed, note) VALUES
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu001'), '2024-09-30', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu002'), '2024-09-30', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu003'), '2024-09-30', 'SIGNIN', 0, '缺勤'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu004'), '2024-09-30', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu005'), '2024-09-30', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu006'), '2024-09-30', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu007'), '2024-09-30', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu008'), '2024-09-30', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu009'), '2024-09-30', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu010'), '2024-09-30', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu011'), '2024-09-30', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu012'), '2024-09-30', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu013'), '2024-09-30', 'SIGNIN', 0, '缺勤'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu014'), '2024-09-30', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu015'), '2024-09-30', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu016'), '2024-09-30', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu017'), '2024-09-30', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu018'), '2024-09-30', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu019'), '2024-09-30', 'SIGNIN', 0, '缺勤'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu020'), '2024-09-30', 'SIGNIN', 1, NULL)
ON DUPLICATE KEY UPDATE completed = VALUES(completed);

-- 第3次作业（2024-10-08）
INSERT INTO edu_daily_records (teaching_id, student_id, record_date, record_type, completed, note) VALUES
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu001'), '2024-10-08', 'HOMEWORK', 1, '优秀'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu002'), '2024-10-08', 'HOMEWORK', 1, '优秀'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu003'), '2024-10-08', 'HOMEWORK', 0, '未交'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu004'), '2024-10-08', 'HOMEWORK', 1, '良好'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu005'), '2024-10-08', 'HOMEWORK', 1, '良好'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu006'), '2024-10-08', 'HOMEWORK', 1, '优秀'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu007'), '2024-10-08', 'HOMEWORK', 1, '良好'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu008'), '2024-10-08', 'HOMEWORK', 0, '未交'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu009'), '2024-10-08', 'HOMEWORK', 1, '优秀'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu010'), '2024-10-08', 'HOMEWORK', 1, '优秀'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu011'), '2024-10-08', 'HOMEWORK', 1, '良好'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu012'), '2024-10-08', 'HOMEWORK', 1, '优秀'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu013'), '2024-10-08', 'HOMEWORK', 0, '未交'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu014'), '2024-10-08', 'HOMEWORK', 1, '优秀'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu015'), '2024-10-08', 'HOMEWORK', 1, '及格'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu016'), '2024-10-08', 'HOMEWORK', 1, '良好'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu017'), '2024-10-08', 'HOMEWORK', 1, '良好'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu018'), '2024-10-08', 'HOMEWORK', 1, '优秀'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu019'), '2024-10-08', 'HOMEWORK', 0, '未交'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu020'), '2024-10-08', 'HOMEWORK', 1, '良好')
ON DUPLICATE KEY UPDATE completed = VALUES(completed);

-- 第2次章节测验（2024-10-15）
INSERT INTO edu_daily_records (teaching_id, student_id, record_date, record_type, completed, note) VALUES
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu001'), '2024-10-15', 'CHAPTER_TEST', 1, '88分'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu002'), '2024-10-15', 'CHAPTER_TEST', 1, '92分'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu003'), '2024-10-15', 'CHAPTER_TEST', 0, '缺考'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu004'), '2024-10-15', 'CHAPTER_TEST', 1, '80分'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu005'), '2024-10-15', 'CHAPTER_TEST', 1, '72分'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu006'), '2024-10-15', 'CHAPTER_TEST', 1, '96分'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu007'), '2024-10-15', 'CHAPTER_TEST', 1, '83分'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu008'), '2024-10-15', 'CHAPTER_TEST', 1, '55分'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu009'), '2024-10-15', 'CHAPTER_TEST', 1, '90分'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu010'), '2024-10-15', 'CHAPTER_TEST', 1, '86分'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu011'), '2024-10-15', 'CHAPTER_TEST', 1, '73分'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu012'), '2024-10-15', 'CHAPTER_TEST', 1, '94分'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu013'), '2024-10-15', 'CHAPTER_TEST', 0, '缺考'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu014'), '2024-10-15', 'CHAPTER_TEST', 1, '87分'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu015'), '2024-10-15', 'CHAPTER_TEST', 1, '66分'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu016'), '2024-10-15', 'CHAPTER_TEST', 1, '82分'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu017'), '2024-10-15', 'CHAPTER_TEST', 1, '76分'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu018'), '2024-10-15', 'CHAPTER_TEST', 1, '91分'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu019'), '2024-10-15', 'CHAPTER_TEST', 0, '缺考'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu020'), '2024-10-15', 'CHAPTER_TEST', 1, '79分')
ON DUPLICATE KEY UPDATE completed = VALUES(completed);

-- 第6周签到（2024-10-21）
INSERT INTO edu_daily_records (teaching_id, student_id, record_date, record_type, completed, note) VALUES
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu001'), '2024-10-21', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu002'), '2024-10-21', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu003'), '2024-10-21', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu004'), '2024-10-21', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu005'), '2024-10-21', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu006'), '2024-10-21', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu007'), '2024-10-21', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu008'), '2024-10-21', 'SIGNIN', 0, '缺勤'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu009'), '2024-10-21', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu010'), '2024-10-21', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu011'), '2024-10-21', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu012'), '2024-10-21', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu013'), '2024-10-21', 'SIGNIN', 0, '缺勤'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu014'), '2024-10-21', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu015'), '2024-10-21', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu016'), '2024-10-21', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu017'), '2024-10-21', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu018'), '2024-10-21', 'SIGNIN', 1, NULL),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu019'), '2024-10-21', 'SIGNIN', 0, '缺勤'),
    (@tid_cs101_2024_2, (SELECT id FROM sys_users WHERE username = 'stu020'), '2024-10-21', 'SIGNIN', 1, NULL)
ON DUPLICATE KEY UPDATE completed = VALUES(completed);

-- ------------------------------------------------------------
-- 8. 添加历史归档数据（2023-2 学期）
-- ------------------------------------------------------------

-- 为 2023-2 学期创建一个已归档的课程
INSERT INTO edu_teaching (course_id, teacher_id, classroom, timeslot, semester, max_count, enrolled_count, status)
SELECT c.id, u.id, 'D101', '周一3-4节,周三3-4节', '2023-2', 50, 15, 'CLOSED'
FROM edu_courses c, sys_users u
WHERE c.course_code = 'CS101' AND u.username = 'teacher01'
ON DUPLICATE KEY UPDATE classroom = VALUES(classroom);

SET @tid_cs101_2023_2 = (
    SELECT t.id FROM edu_teaching t
    JOIN edu_courses c ON t.course_id = c.id
    WHERE c.course_code = 'CS101' AND t.semester = '2023-2'
    LIMIT 1
);

-- 为该课程添加已归档的成绩
INSERT INTO edu_archives (original_grade_id, student_id, teaching_id, score, archived_at)
SELECT 
    (u.id * 1000 + @tid_cs101_2023_2),
    u.id, 
    @tid_cs101_2023_2, 
    CASE u.username
        WHEN 'stu001' THEN 86.0
        WHEN 'stu002' THEN 91.0
        WHEN 'stu004' THEN 76.0
        WHEN 'stu005' THEN 64.0
        WHEN 'stu006' THEN 94.0
        WHEN 'stu007' THEN 81.0
        WHEN 'stu009' THEN 87.0
        WHEN 'stu010' THEN 83.0
        WHEN 'stu011' THEN 70.0
        WHEN 'stu012' THEN 95.0
        WHEN 'stu014' THEN 88.0
        WHEN 'stu015' THEN 65.0
        WHEN 'stu016' THEN 82.0
        WHEN 'stu018' THEN 90.0
        WHEN 'stu020' THEN 79.0
    END,
    '2024-01-15 10:30:00'
FROM sys_users u
WHERE u.username IN (
    'stu001', 'stu002', 'stu004', 'stu005', 'stu006',
    'stu007', 'stu009', 'stu010', 'stu011', 'stu012',
    'stu014', 'stu015', 'stu016', 'stu018', 'stu020'
)
ON DUPLICATE KEY UPDATE score = VALUES(score);

-- ------------------------------------------------------------
-- 9. 更新 enrolled_count 以匹配实际学生数
-- ------------------------------------------------------------
UPDATE edu_teaching t
SET enrolled_count = (
    SELECT COUNT(DISTINCT g.student_id)
    FROM edu_grades g
    WHERE g.teaching_id = t.id AND g.is_deleted = 0
)
WHERE t.semester = '2024-2';

SELECT 'Teacher demo data inserted successfully. 20 students, multiple courses, rich daily records!' AS status;
