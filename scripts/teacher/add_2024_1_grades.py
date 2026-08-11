"""为2024-1学期的课程添加成绩记录"""
import mysql.connector
import random

from core.config import load_db_config

config = load_db_config()

def add_grades():
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor(dictionary=True)
    
    try:
        print("=" * 60)
        print("为 2024-1 学期添加成绩记录")
        print("=" * 60)
        
        cursor.execute("""
            SELECT id as teaching_id, course_id
            FROM edu_teaching
            WHERE semester = '2024-1' AND is_deleted = 0
        """)
        teachings = cursor.fetchall()
        
        cursor.execute("""
            SELECT id as student_id
            FROM sys_users
            WHERE role_id = 3 AND is_deleted = 0
        """)
        students = cursor.fetchall()
        
        print(f"\n找到 {len(teachings)} 个课程，{len(students)} 名学生")
        
        added_count = 0
        
        for teaching in teachings:
            teaching_id = teaching['teaching_id']
            
            print(f"\n处理 teaching_id={teaching_id}...")
            
            for student in students:
                student_id = student['student_id']
                
                score = round(random.uniform(55, 98), 2)
                
                if score >= 90:
                    gpa, letter, is_passed = 4.0, 'A+', 1
                elif score >= 85:
                    gpa, letter, is_passed = 4.0, 'A', 1
                elif score >= 82:
                    gpa, letter, is_passed = 3.0, 'B+', 1
                elif score >= 78:
                    gpa, letter, is_passed = 3.0, 'B', 1
                elif score >= 75:
                    gpa, letter, is_passed = 2.0, 'C+', 1
                elif score >= 72:
                    gpa, letter, is_passed = 2.0, 'C', 1
                elif score >= 60:
                    gpa, letter, is_passed = 1.0, 'D', 1
                else:
                    gpa, letter, is_passed = 0.0, 'F', 0
                
                try:
                    cursor.execute("""
                        INSERT INTO edu_grades 
                        (student_id, teaching_id, exam_score, score, gpa_point, grade_letter, is_passed)
                        VALUES (%s, %s, NULL, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            score = VALUES(score),
                            gpa_point = VALUES(gpa_point),
                            grade_letter = VALUES(grade_letter),
                            is_passed = VALUES(is_passed)
                    """, (
                        student_id,
                        teaching_id,
                        score,
                        gpa,
                        letter,
                        is_passed
                    ))
                    added_count += 1
                except Exception as e:
                    print(f"  插入失败 (student_id={student_id}): {e}")
            
            conn.commit()
        
        print(f"\n[OK] 已添加 {added_count} 条成绩记录")
        
        cursor.execute("""
            SELECT t.id, c.course_name, COUNT(DISTINCT g.student_id) as grade_count
            FROM edu_teaching t
            JOIN edu_courses c ON t.course_id = c.id
            LEFT JOIN edu_grades g ON t.id = g.teaching_id AND g.is_deleted = 0
            WHERE t.semester = '2024-1' AND t.is_deleted = 0
            GROUP BY t.id
        """)
        summary = cursor.fetchall()
        
        print("\n各课程成绩记录统计:")
        for s in summary:
            print(f"  {s['course_name']}: {s['grade_count']} 条记录")
        
        print("\n" + "=" * 60)
        print("2024-1 学期成绩数据添加完成！")
        print("=" * 60)
        
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    add_grades()
    print("\n现在2024-1学期的课程有成绩数据了。")
    print("在教师端'历史归档'标签页可以查询这些成绩。")
