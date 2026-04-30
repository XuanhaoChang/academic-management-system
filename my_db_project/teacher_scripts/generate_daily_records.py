"""为所有2024-2学期的课程生成平时记录mock数据"""
import mysql.connector
import random
from datetime import datetime, timedelta

config = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'dbadmin',
    'password': 'DbAdmin2024',
    'database': 'my_db_project',
    'charset': 'utf8mb4',
}

def generate_daily_records():
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT t.id as teaching_id, c.course_name, t.semester
            FROM edu_teaching t
            JOIN edu_courses c ON t.course_id = c.id
            WHERE t.semester = '2024-2' AND t.is_deleted = 0
        """)
        teachings = cursor.fetchall()
        
        cursor.execute("""
            SELECT id as student_id, username
            FROM sys_users
            WHERE role_id = 3 AND is_deleted = 0
            ORDER BY id
        """)
        students = cursor.fetchall()
        
        if not teachings:
            print("没有找到2024-2学期的课程")
            return
        
        if not students:
            print("没有找到学生")
            return
        
        print(f"找到 {len(teachings)} 个课程，{len(students)} 名学生")
        print("=" * 60)
        
        total_records = 0
        
        for teaching in teachings:
            teaching_id = teaching['teaching_id']
            course_name = teaching['course_name']
            
            print(f"\n正在为课程 [{course_name}] (ID: {teaching_id}) 生成平时记录...")
            
            start_date = datetime(2024, 9, 2)
            
            record_configs = [
                ('SIGNIN', 6, 7),
                ('HOMEWORK', 4, 7),
                ('CHAPTER_TEST', 3, 14),
            ]
            
            for record_type, count, interval_days in record_configs:
                for i in range(count):
                    record_date = (start_date + timedelta(days=i * interval_days)).strftime('%Y-%m-%d')
                    
                    for student in students:
                        student_id = student['student_id']
                        
                        completed = 1 if random.random() > 0.15 else 0
                        
                        note = None
                        if record_type == 'SIGNIN':
                            if completed == 0:
                                note = random.choice(['缺勤', '迟到', '请假'])
                        elif record_type == 'HOMEWORK':
                            if completed == 1:
                                note = random.choice(['优秀', '良好', '及格', None, None])
                            else:
                                note = '未交'
                        elif record_type == 'CHAPTER_TEST':
                            if completed == 1:
                                note = f"{random.randint(65, 98)}分"
                            else:
                                note = '缺考'
                        
                        try:
                            cursor.execute("""
                                INSERT INTO edu_daily_records 
                                (teaching_id, student_id, record_date, record_type, completed, note)
                                VALUES (%s, %s, %s, %s, %s, %s)
                                ON DUPLICATE KEY UPDATE 
                                    completed = VALUES(completed),
                                    note = VALUES(note)
                            """, (teaching_id, student_id, record_date, record_type, completed, note))
                            total_records += 1
                        except Exception as e:
                            print(f"  插入失败: {e}")
            
            conn.commit()
            print(f"  [OK] 完成: 签到 {6} 次, 作业 {4} 次, 测验 {3} 次")
        
        print("\n" + "=" * 60)
        print(f"总计生成 {total_records} 条平时记录")
        print("=" * 60)
        
        cursor.execute("""
            SELECT teaching_id, COUNT(*) as cnt
            FROM edu_daily_records
            WHERE is_deleted = 0
            GROUP BY teaching_id
        """)
        summary = cursor.fetchall()
        
        print("\n各课程平时记录统计:")
        for s in summary:
            print(f"  Teaching ID {s['teaching_id']}: {s['cnt']} 条记录")
        
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    print("开始生成平时记录mock数据...")
    generate_daily_records()
    print("\n[OK] 完成！现在可以在教师端使用'一键导入平时分'功能了。")
