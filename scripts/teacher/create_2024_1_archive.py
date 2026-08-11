"""为2024-1学期创建成绩并归档"""
import mysql.connector

from core.config import load_db_config

config = load_db_config()

def create_and_archive():
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor(dictionary=True)
    
    try:
        print("=" * 60)
        print("为 2024-1 学期创建归档数据")
        print("=" * 60)
        
        cursor.execute("""
            SELECT id as teaching_id, course_id
            FROM edu_teaching
            WHERE semester = '2024-1' AND is_deleted = 0
        """)
        teachings = cursor.fetchall()
        
        if not teachings:
            print("没有找到2024-1学期的课程")
            return
        
        cursor.execute("""
            SELECT id as student_id
            FROM sys_users
            WHERE role_id = 3 AND is_deleted = 0
            LIMIT 15
        """)
        students = cursor.fetchall()
        
        print(f"\n找到 {len(teachings)} 个课程，{len(students)} 名学生")
        
        import random
        archived_count = 0
        
        for teaching in teachings:
            teaching_id = teaching['teaching_id']
            course_id = teaching['course_id']
            
            print(f"\n处理 teaching_id={teaching_id}...")
            
            for student in students:
                student_id = student['student_id']
                
                score = round(random.uniform(55, 95), 2)
                
                if score >= 90:
                    gpa, letter = 4.0, 'A+'
                elif score >= 85:
                    gpa, letter = 4.0, 'A'
                elif score >= 82:
                    gpa, letter = 3.0, 'B+'
                elif score >= 78:
                    gpa, letter = 3.0, 'B'
                elif score >= 75:
                    gpa, letter = 2.0, 'C+'
                elif score >= 72:
                    gpa, letter = 2.0, 'C'
                elif score >= 60:
                    gpa, letter = 1.0, 'D'
                else:
                    gpa, letter = 0.0, 'F'
                
                is_passed = 1 if score >= 60 else 0
                
                original_grade_id = teaching_id * 10000 + student_id
                
                try:
                    cursor.execute("""
                        INSERT INTO edu_archives 
                        (original_grade_id, student_id, teaching_id, course_id, semester,
                         score, gpa_point, grade_letter, is_passed, archived_at)
                        VALUES (%s, %s, %s, %s, '2024-1', %s, %s, %s, %s, '2024-02-15 14:30:00')
                        ON DUPLICATE KEY UPDATE
                            score = VALUES(score),
                            gpa_point = VALUES(gpa_point),
                            grade_letter = VALUES(grade_letter),
                            is_passed = VALUES(is_passed)
                    """, (
                        original_grade_id,
                        student_id,
                        teaching_id,
                        course_id,
                        score,
                        gpa,
                        letter,
                        is_passed
                    ))
                    archived_count += 1
                except Exception as e:
                    print(f"  插入失败: {e}")
            
            conn.commit()
        
        print(f"\n[OK] 已创建 {archived_count} 条归档记录")
        
        cursor.execute("""
            UPDATE edu_teaching
            SET is_submitted = 1
            WHERE semester = '2024-1' AND is_deleted = 0
        """)
        conn.commit()
        print("[OK] 已锁定所有2024-1学期的课程")
        
        print("\n" + "=" * 60)
        print("2024-1 学期归档数据创建完成！")
        print("=" * 60)
        
        cursor.execute("""
            SELECT COUNT(*) as cnt
            FROM edu_archives
            WHERE semester = '2024-1'
        """)
        total = cursor.fetchone()['cnt']
        print(f"\nedu_archives 表中 2024-1 学期记录总数: {total}")
        
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    create_and_archive()
    print("\n现在可以在教师端'历史归档'标签页查询2024-1学期的成绩了。")
