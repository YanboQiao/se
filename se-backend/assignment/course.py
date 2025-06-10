import datetime
import os
from flask import jsonify, g, request

from login.auth import student_required, teacher_required
from login.db import get_db_connection
from .utils import ensure_dir, get_course_str_id, parse_course_id, check_submission_exists, get_assignment_description


@student_required
def get_student_course_api(course_id):
    """学生获取课程详情（含完整信息 + 作业列表）"""
    student_email = g.user["email"]

    if not course_id:
        return jsonify({"message": "课程ID无效"}), 400

    conn = get_db_connection()
    data_out = {"course": {}, "assignments": []}
    try:
        with conn.cursor() as cur:
            # 权限校验
            cur.execute(
                "SELECT 1 FROM student_course WHERE useremail=%s AND course_id=%s",
                (student_email, course_id),
            )
            if not cur.fetchone():
                return jsonify({"message": "未选该课程"}), 403

            # 课程完整信息
            cur.execute(
                """
                SELECT
                    c.course_name,
                    c.course_desc,
                    c.start_time,
                    c.end_time,
                    t.username AS teacher_name
                FROM course c
                LEFT JOIN teacher t ON c.teacher_email = t.useremail
                WHERE c.course_id = %s
                """,
                (course_id,),
            )
            meta = cur.fetchone()
            if not meta:
                return jsonify({"message": "课程不存在"}), 404

            data_out["course"] = {
                "id":          course_id,
                "name":        meta["course_name"],
                "description": meta.get("course_desc") or "",
                "startDate":   meta["start_time"].strftime("%Y-%m-%d") if meta.get("start_time") else None,
                "endDate":     meta["end_time"].strftime("%Y-%m-%d")   if meta.get("end_time")   else None,
                "teacher":     meta.get("teacher_name") or "",
            }

            # 作业列表（使用文件系统检查提交状态）
            cur.execute(
                "SELECT assign_no, title, due_date FROM assignment WHERE course_id=%s ORDER BY assign_no",
                (course_id,),
            )
            for asm in cur.fetchall():
                no, title, due_date = asm["assign_no"], asm["title"], asm["due_date"]
                assignment_id = f"{course_id}_hw_{no}"
                
                # 从文件系统检查提交状态
                submitted = check_submission_exists(course_id, no, student_email)
                
                # 从文件系统获取作业描述
                description = get_assignment_description(course_id, no)
                
                # 如果已提交，从homework表获取评分
                score = None
                if submitted:
                    try:
                        cur.execute(
                            "SELECT score FROM homework WHERE course_id=%s AND assign_no=%s AND student_email=%s",
                            (course_id, no, student_email),
                        )
                        score_result = cur.fetchone()
                        if score_result:
                            score = score_result["score"]
                    except Exception:
                        # 如果查询失败，score保持为None
                        pass

                data_out["assignments"].append(
                    {
                        "id":          assignment_id,
                        "title":       title,
                        "description": description,
                        "dueDate":     due_date.strftime("%Y-%m-%d") if due_date else None,
                        "submitted":   submitted,
                        "score":       score,
                    }
                )
    finally:
        conn.close()
    return jsonify(data_out), 200


@teacher_required
def get_teacher_course_api(course_id):
    """教师获取课程详情（课程信息及作业列表）"""
    teacher_email = g.user["email"]
    # 直接使用传入的course_id，支持字符串格式
    conn = get_db_connection()
    data_out = {"course": {}, "assignments": []}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT course_name, teacher_email FROM course WHERE course_id=%s", (course_id,))
            course = cur.fetchone()
            if not course:
                return jsonify({"message": "课程不存在"}), 404
            if course["teacher_email"] != teacher_email:
                return jsonify({"message": "无权限访问该课程"}), 403
            data_out["course"] = {"id": course_id, "name": course["course_name"]}
            cur.execute("SELECT assign_no, title, due_date FROM assignment WHERE course_id=%s", (course_id,))
            now = datetime.datetime.now()
            for asm in cur.fetchall():
                no, title, due_date = asm["assign_no"], asm["title"], asm["due_date"]
                status = ""
                if due_date:
                    status = "已截止" if due_date < now else "进行中"
                data_out["assignments"].append({
                    "id": f"{course_id}_hw_{no}",
                    "title": title,
                    "dueDate": due_date.strftime("%Y-%m-%d") if due_date else None,
                    "status": status
                })
    finally:
        conn.close()
    return jsonify(data_out), 200


@teacher_required
def create_course_api():
    """教师创建新课程"""
    teacher_email = g.user["email"]
    data = request.get_json(silent=True) or {}
    course_name = data.get("name")
    course_desc = data.get("description") or ""
    
    if not course_name or not course_name.strip():
        return jsonify({"message": "课程名称不能为空"}), 400
    
    now = datetime.datetime.now()
    end_time = now + datetime.timedelta(days=120)
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 先获取下一个course_id的数值
            cur.execute("SELECT COALESCE(MAX(CAST(SUBSTRING(course_id, 8) AS UNSIGNED)), 0) + 1 as next_id FROM course WHERE course_id LIKE 'course_%'")
            result = cur.fetchone()
            next_course_num = result["next_id"] if result else 1
            course_id = f"course_{next_course_num}"
            
            # 创建课程记录
            cur.execute("""
                INSERT INTO course (course_id, course_name, course_desc, teacher_email, start_time, end_time) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (course_id, course_name, course_desc, teacher_email, now, end_time))
            
        conn.commit()
        
        # 创建课程学生表(兼容旧代码)
        try:
            with conn.cursor() as cur:
                students_table = f"{course_id}_students"
                cur.execute(f"CREATE TABLE IF NOT EXISTS `{students_table}` (studentemail VARCHAR(100) PRIMARY KEY)")
            conn.commit()
        except Exception as e:
            # 表创建失败不影响课程创建
            print(f"创建课程学生表失败: {e}")
        
        # 创建课程文件夹结构
        try:
            base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
            course_folder = os.path.join(base_dir, course_id)
            ensure_dir(course_folder)
            ensure_dir(os.path.join(course_folder, "homeworkList"))
            ensure_dir(os.path.join(course_folder, "courseware"))
        except Exception as e:
            # 文件夹创建失败不影响课程创建
            print(f"创建课程文件夹失败: {e}")
        
        return jsonify({
            "message": "课程创建成功",
            "course": {
                "id": course_id, 
                "name": course_name,
                "description": course_desc
            }
        }), 200
        
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"创建课程失败: {e}"}), 500
    finally:
        conn.close()


@student_required
def enroll_course_api(course_id):
    """学生选课接口"""
    student_email = g.user["email"]
    
    # 解析课程ID
    num_id = parse_course_id(course_id)
    if num_id is None:
        return jsonify({"message": "课程ID无效"}), 400
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 检查课程是否存在
            cur.execute("SELECT course_name FROM course WHERE course_id=%s", (num_id,))
            course = cur.fetchone()
            if not course:
                return jsonify({"message": "课程不存在"}), 404
            
            # 检查是否已经选课(使用student_course表)
            cur.execute("""
                SELECT 1 FROM student_course 
                WHERE useremail = %s AND course_id = %s
            """, (student_email, num_id))
            
            if cur.fetchone():
                return jsonify({"message": "已经选过该课程"}), 400
            
            # 选课(使用student_course通用表)
            cur.execute("""
                INSERT INTO student_course (useremail, course_id) 
                VALUES (%s, %s)
            """, (student_email, num_id))
            
            # 将学生添加到课程学生表(兼容旧代码)
            course_str = get_course_str_id(num_id)
            students_table = f"{course_str}_students"
            try:
                cur.execute(f"INSERT IGNORE INTO `{students_table}` (studentemail) VALUES (%s)", (student_email,))
            except Exception:
                pass
                
        conn.commit()
        return jsonify({"message": "选课成功", "course": {"id": course_id, "name": course["course_name"]}}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"选课失败: {e}"}), 500
    finally:
        conn.close()



