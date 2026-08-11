"""加载教师端演示数据"""
import mysql.connector
from pathlib import Path

from core.config import load_db_config

config = load_db_config()

def main():
    print("=" * 60)
    print("加载教师端演示数据")
    print("=" * 60)
    
    sql_file = Path(__file__).resolve().parents[2] / 'sql' / '07_teacher_demo_data.sql'
    
    if not sql_file.exists():
        print(f"错误：文件不存在 {sql_file}")
        return
    
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    
    try:
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        statements = []
        current = []
        
        for line in sql_content.split('\n'):
            line_stripped = line.strip()
            
            if line_stripped and not line_stripped.startswith('--'):
                current.append(line)
            
            if line_stripped.endswith(';'):
                statements.append('\n'.join(current))
                current = []
        
        success = 0
        failed = 0
        
        for stmt in statements:
            stmt = stmt.strip()
            if not stmt or stmt.startswith('--'):
                continue
            
            try:
                cursor.execute(stmt)
                if cursor.with_rows:
                    rows = cursor.fetchall()
                    if rows:
                        for row in rows:
                            print(f"  -> {row}")
                conn.commit()
                success += 1
                
                if 'INSERT INTO sys_users' in stmt:
                    print(f"  [OK] 添加学生数据")
                elif 'INSERT INTO edu_courses' in stmt:
                    print(f"  [OK] 添加课程数据")
                elif 'INSERT INTO edu_teaching' in stmt:
                    print(f"  [OK] 添加授课安排")
                elif 'INSERT INTO edu_grades' in stmt:
                    print(f"  [OK] 添加成绩数据")
                elif 'INSERT INTO edu_daily_records' in stmt:
                    print(f"  [OK] 添加平时记录")
                elif 'INSERT INTO edu_archives' in stmt:
                    print(f"  [OK] 添加归档数据")
                elif 'UPDATE edu_teaching' in stmt:
                    print(f"  [OK] 更新选课人数")
                
            except Exception as e:
                print(f"  [FAIL] 执行失败")
                print(f"    Error: {e}")
                failed += 1
        
        print("\n" + "=" * 60)
        print(f"完成: 成功 {success}, 失败 {failed}")
        print("=" * 60)
        
        print("\n演示数据统计:")
        cursor.execute("SELECT COUNT(*) FROM sys_users WHERE role_id = 3")
        student_count = cursor.fetchone()[0]
        print(f"  学生总数: {student_count}")
        
        cursor.execute("SELECT COUNT(*) FROM edu_courses")
        course_count = cursor.fetchone()[0]
        print(f"  课程总数: {course_count}")
        
        cursor.execute("SELECT COUNT(*) FROM edu_teaching WHERE semester = '2024-2'")
        teaching_count = cursor.fetchone()[0]
        print(f"  2024-2学期授课班级: {teaching_count}")
        
        cursor.execute("SELECT COUNT(*) FROM edu_grades WHERE teaching_id = @tid_cs101_2024_2")
        grade_count = cursor.fetchone()[0]
        print(f"  CS101 2024-2 成绩记录: {grade_count}")
        
        cursor.execute("SELECT COUNT(*) FROM edu_daily_records WHERE teaching_id = @tid_cs101_2024_2")
        daily_count = cursor.fetchone()[0]
        print(f"  CS101 2024-2 平时记录: {daily_count}")
        
        print("\n测试账号:")
        print("  教师: teacher01 / teacher123")
        print("  学生: stu001~stu020 / student123")
        
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()
