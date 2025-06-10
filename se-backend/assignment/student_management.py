from flask import jsonify, g, request

from login.auth import teacher_required
from login.db import get_db_connection
from .utils import parse_course_id


@teacher_required
def search_students_api():
    """教师搜索学生（根据邮箱或用户名）"""
    query = request.args.get('query', '').strip()
    if not query:
        return jsonify({"message": "搜索关键词不能为空"}), 400
    
    # 限制搜索结果数量
    limit = min(int(request.args.get('limit', 20)), 50)
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 按邮箱或用户名模糊搜索学生
            cur.execute("""
                SELECT useremail, username 
                FROM student 
                WHERE useremail LIKE %s OR username LIKE %s
                ORDER BY username
                LIMIT %s
            """, (f"%{query}%", f"%{query}%", limit))
            
            students = []
            for row in cur.fetchall():
                students.append({
                    "email": row["useremail"],
                    "name": row["username"]
                })
            
            return jsonify({"students": students}), 200
    except Exception as e:
        return jsonify({"message": f"搜索学生失败: {e}"}), 500
    finally:
        conn.close()


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


@teacher_required 
def batch_enroll_students_api():
    """教师批量为学生选课"""
    data = request.get_json(silent=True) or {}
    course_id = data.get('course_id')
    student_emails = data.get('student_emails', [])
    
    if not course_id:
        return jsonify({"message": "课程ID不能为空"}), 400
    if not student_emails or not isinstance(student_emails, list):
        return jsonify({"message": "学生邮箱列表不能为空"}), 400
    
    conn = get_db_connection()
    success_count = 0
    failed_students = []
    
    try:
        with conn.cursor() as cur:
            # 验证教师是否为该课程的授课教师
            cur.execute("SELECT teacher_email, course_name FROM course WHERE course_id=%s", (course_id,))
            course = cur.fetchone()
            if not course:
                return jsonify({"message": "课程不存在"}), 404
            if course["teacher_email"] != g.user["email"]:
                return jsonify({"message": "无权限操作该课程"}), 403
            
            for email in student_emails:
                try:
                    # 检查学生是否存在
                    cur.execute("SELECT username FROM student WHERE useremail=%s", (email,))
                    student = cur.fetchone()
                    if not student:
                        failed_students.append({"email": email, "reason": "学生不存在"})
                        continue
                    
                    # 检查是否已经选课
                    cur.execute("SELECT 1 FROM student_course WHERE useremail=%s AND course_id=%s", (email, course_id))
                    if cur.fetchone():
                        failed_students.append({"email": email, "reason": "已经选过该课程"})
                        continue
                    
                    # 选课(使用student_course通用表)
                    cur.execute("INSERT INTO student_course (useremail, course_id) VALUES (%s, %s)", (email, course_id))
                    success_count += 1
                    
                except Exception as e:
                    failed_students.append({"email": email, "reason": str(e)})
                    continue
        
        conn.commit()
        
        result = {
            "message": f"成功为 {success_count} 名学生选课",
            "success_count": success_count,
            "total_count": len(student_emails)
        }
        
        if failed_students:
            result["failed_students"] = failed_students
        
        return jsonify(result), 200
        
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"批量选课失败: {e}"}), 500
    finally:
        conn.close()
