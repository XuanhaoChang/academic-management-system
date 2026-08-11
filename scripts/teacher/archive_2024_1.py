"""将2024-1学期的成绩归档并锁定"""
import mysql.connector

from core.config import load_db_config

config = load_db_config()

def archive_2024_1():
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor(dictionary=True)
    
    try:
        print("=" * 60)
        print("归档 2024-1 学期成绩")
        print("=" * 60)
        
        cursor.execute("""
            SELECT g.id, g.student_id, g.teaching_id, t.course_id, t.semester,
                   g.score, g.gpa_point, g.grade_letter, g.is_passed
            FROM edu_grades g
            JOIN edu_teaching t ON g.teaching_id = t.id
            WHERE t.semester = '2024-1' AND g.is_deleted = 0
        """)
        grades = cursor.fetchall()
        
        if not grades:
            print("没有找到2024-1学期的成绩记录")
            return
        
        print(f"\n找到 {len(grades)} 条成绩记录，开始归档...")
        
        archived_count = 0
        for grade in grades:
            try:
                cursor.execute("""
                    INSERT INTO edu_archives 
                    (original_grade_id, student_id, teaching_id, course_id, semester, 
                     score, gpa_point, grade_letter, is_passed, archived_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON DUPLICATE KEY UPDATE
                        score = VALUES(score),
                        gpa_point = VALUES(gpa_point),
                        grade_letter = VALUES(grade_letter),
                        is_passed = VALUES(is_passed)
                """, (
                    grade['id'],
                    grade['student_id'],
                    grade['teaching_id'],
                    grade['course_id'],
                    grade['semester'],
                    grade['score'],
                    grade['gpa_point'],
                    grade['grade_letter'],
                    grade['is_passed']
                ))
                archived_count += 1
            except Exception as e:
                print(f"  归档失败 (grade_id={grade['id']}): {e}")
        
        conn.commit()
        print(f"\n[OK] 已归档 {archived_count} 条成绩到 edu_archives 表")
        
        cursor.execute("""
            UPDATE edu_teaching
            SET is_submitted = 1
            WHERE semester = '2024-1' AND is_deleted = 0
        """)
        conn.commit()
        
        cursor.execute("""
            SELECT COUNT(*) as cnt
            FROM edu_teaching
            WHERE semester = '2024-1' AND is_submitted = 1 AND is_deleted = 0
        """)
        locked = cursor.fetchone()['cnt']
        
        print(f"[OK] 已锁定 {locked} 个2024-1学期的授课班级")
        
        cursor.execute("""
            UPDATE edu_grades g
            JOIN edu_teaching t ON g.teaching_id = t.id
            SET g.is_deleted = 1
            WHERE t.semester = '2024-1'
        """)
        conn.commit()
        
        print(f"[OK] 已软删除 {len(grades)} 条成绩记录（归档后清理）")
        
        print("\n" + "=" * 60)
        print("2024-1 学期归档完成！")
        print("=" * 60)
        
        cursor.execute("""
            SELECT COUNT(*) as cnt
            FROM edu_archives
            WHERE semester = '2024-1'
        """)
        total_archived = cursor.fetchone()['cnt']
        print(f"\nedu_archives 表中 2024-1 学期记录总数: {total_archived}")
        
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    archive_2024_1()
    print("\n现在教师端只能看到2024-2学期的课程了。")
    print("2024-1学期的成绩可以在'历史归档'标签页查询。")
