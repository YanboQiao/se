from flask import jsonify, g

from login.auth import teacher_required
from login.db import get_db_connection
from .utils import parse_course_id


@teacher_required
def get_course_students_api(course_id):
    """教师查看选课学生列表"""
    teacher_email = g.user["email"]
    
    # 解析课程ID
    num_id = parse_course_id(course_id)
    if num_id is None:
        return jsonify({"message": "课程ID无效"}), 400
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 验证教师是否为该课程的授课教师
            cur.execute("SELECT teacher_email FROM course WHERE course_id=%s", (num_id,))
            course = cur.fetchone()
            if not course:
                return jsonify({"message": "课程不存在"}), 404
            if course["teacher_email"] != teacher_email:
                return jsonify({"message": "无权限访问该课程"}), 403
            
            # 查询选课学生列表(使用student_course表)
            cur.execute("""
                SELECT s.useremail, s.username 
                FROM student_course sc
                JOIN student s ON sc.useremail = s.useremail
                WHERE sc.course_id = %s
                ORDER BY s.username
            """, (num_id,))
            
            students = []
            for row in cur.fetchall():
                students.append({
                    "email": row["useremail"],
                    "name": row["username"]
                })
            
            return jsonify({"students": students}), 200
    except Exception as e:
        return jsonify({"message": f"获取学生列表失败: {e}"}), 500
    finally:
        conn.close()
