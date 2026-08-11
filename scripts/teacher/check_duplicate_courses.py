import mysql.connector
from core.config import load_db_config

DB_CONFIG = load_db_config()

try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    # 查询所有教学记录
    cursor.execute('''
        SELECT t.id, c.course_name, t.semester, t.teacher_id, 
               COUNT(DISTINCT g.id) as grade_count
        FROM edu_teaching t
        JOIN edu_courses c ON t.course_id = c.id
        LEFT JOIN edu_grades g ON t.id = g.teaching_id AND g.is_deleted = 0
        WHERE t.teacher_id = 1
        GROUP BY t.id, c.course_name, t.semester
        ORDER BY c.course_name, t.semester
    ''')
    
    print("教师的所有课程:")
    print("-" * 80)
    courses = {}
    for row in cursor.fetchall():
        status = "有成绩" if row['grade_count'] > 0 else "无成绩"
        key = f"{row['course_name']}_{row['semester']}"
        if key not in courses:
            courses[key] = []
        courses[key].append({
            'id': row['id'],
            'grade_count': row['grade_count'],
            'status': status
        })
        print(f"ID: {row['id']}, 课程: {row['course_name']}, 学期: {row['semester']}, {status}")
    
    print("\n重复的课程:")
    print("-" * 80)
    for key, items in courses.items():
        if len(items) > 1:
            print(f"\n课程: {key}")
            for item in items:
                print(f"  ID: {item['id']}, {item['status']}")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"错误: {e}")
