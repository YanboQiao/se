import datetime
import os
from flask import jsonify, g, request, current_app

from login.auth import student_required, teacher_required
from login.db import get_db_connection
from .utils import ensure_dir, get_course_str_id, parse_course_id, normalize_course_id


@teacher_required
def create_assignment_api(course_id):
    """教师在课程中布置新作业
    
    Args:
        course_id: 课程ID，可以是"course_X"格式或纯数字
        
    请求体格式:
    {
        "title": "作业标题",
        "description": "作业描述",
        "dueDate": "2025-06-30",  # 可选，YYYY-MM-DD格式
        "referenceAnswer": "参考答案"  # 可选
    }
    
    Returns:
        成功: 200 OK, {"assignment": {...}}
        失败: 400/403/404/500 错误信息
    """
    teacher_email = g.user["email"]
    data = request.get_json(silent=True) or {}
    
    # 1. 获取并验证请求参数
    title = data.get("title")
    description = data.get("description", "")
    due_date_str = data.get("dueDate")
    reference_answer = data.get("referenceAnswer", "")
    
    # 验证必填字段
    if not title or not title.strip():
        return jsonify({"message": "标题不能为空"}), 400
    
    # 2. 解析课程ID - 支持字符串格式
    clean_course_id = course_id
    if course_id.startswith("course_"):
        clean_course_id = course_id.replace("course_", "")
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 3. 验证教师权限
            cur.execute("SELECT teacher_email FROM course WHERE course_id=%s", (clean_course_id,))
            res = cur.fetchone()
            if not res:
                return jsonify({"message": "课程不存在"}), 404
            if res["teacher_email"] != teacher_email:
                return jsonify({"message": "无权在此课程下创建作业"}), 403
            
            # 4. 获取新作业序号
            cur.execute("SELECT MAX(assign_no) AS max_no FROM assignment WHERE course_id=%s", (clean_course_id,))
            row = cur.fetchone()
            next_no = (row["max_no"] + 1) if row and row["max_no"] else 1
            
            # 5. 处理截止日期
            due_date = None
            if due_date_str:
                try:
                    due_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d")
                except:
                    return jsonify({"message": "日期格式无效，请使用YYYY-MM-DD格式"}), 400
            
            # 6. 插入作业记录
            cur.execute(
                "INSERT INTO assignment (course_id, assign_no, title, description, due_date, reference_answer) VALUES (%s,%s,%s,%s,%s,%s)",
                (clean_course_id, next_no, title, description, due_date, reference_answer)
            )
            
            # 7. 创建作业提交表 (这里使用单独的表而不是一个表，与您现有的实现保持一致)
            assignment_table = f"course_{clean_course_id}_hw_{next_no}"
            create_sql = (
                f"CREATE TABLE IF NOT EXISTS `{assignment_table}` ("
                "studentemail VARCHAR(100) NOT NULL, "
                "content TEXT, "
                "score INT, "
                "comment TEXT, "
                "submit_time DATETIME DEFAULT CURRENT_TIMESTAMP, "
                "PRIMARY KEY (studentemail), "
                "CONSTRAINT `fk_{assignment_table}_student` FOREIGN KEY (studentemail) "
                "REFERENCES student(useremail) ON DELETE CASCADE ON UPDATE CASCADE"
                ")"
            )
            cur.execute(create_sql)
            
            # 8. 提交事务
            conn.commit()
            
            # 9. 创建作业文件存储目录
            base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
            course_folder = os.path.join(base_dir, f"course_{clean_course_id}")
            ensure_dir(course_folder)
            ensure_dir(os.path.join(course_folder, "assignments"))
            asm_folder = os.path.join(course_folder, "assignments", f"assignment_{next_no}")
            ensure_dir(asm_folder)
            
            # 10. 保存作业说明和参考答案文件
            if description:
                try:
                    with open(os.path.join(asm_folder, "description.txt"), "w", encoding="utf-8") as f:
                        f.write(description)
                except Exception as e:
                    current_app.logger.error(f"保存作业描述文件失败: {e}")
            
            if reference_answer:
                try:
                    with open(os.path.join(asm_folder, "reference_answer.txt"), "w", encoding="utf-8") as f:
                        f.write(reference_answer)
                except Exception as e:
                    current_app.logger.error(f"保存参考答案文件失败: {e}")
            
            # 11. 构建响应数据
            status = ""
            if due_date:
                status = "已截止" if due_date < datetime.datetime.now() else "进行中"
            
            assignment_data = {
                "id": f"course_{clean_course_id}_hw_{next_no}",
                "title": title,
                "dueDate": due_date.strftime("%Y-%m-%d") if due_date else None,
                "status": status
            }
            
            return jsonify({"assignment": assignment_data}), 200
            
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"创建作业失败: {str(e)}"}), 500
    finally:
        conn.close()


@student_required
def get_student_assignment_api(assignment_id):
    """学生获取作业详情和自己的提交"""
    student_email = g.user["email"]
    if "_hw_" not in assignment_id:
        return jsonify({"message": "作业ID无效"}), 400
    course_part, assign_no_part = assignment_id.split("_hw_", 1)
    if not assign_no_part.isdigit():
        return jsonify({"message": "作业ID无效"}), 400
    assign_no = int(assign_no_part)
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 验证学生参与课程(使用student_course表)
            cur.execute("""
                SELECT 1 FROM student_course 
                WHERE useremail = %s AND course_id = %s
            """, (student_email, course_part))
            if not cur.fetchone():
                return jsonify({"message": "无权访问该作业"}), 403
                
            # 查询作业基本信息
            cur.execute("SELECT title, description, due_date FROM assignment WHERE course_id=%s AND assign_no=%s", (course_part, assign_no))
            meta = cur.fetchone()
            if not meta:
                return jsonify({"message": "作业不存在"}), 404
            assignment_info = {
                "title": meta["title"],
                "description": meta["description"] or "",
                "dueDate": meta["due_date"].strftime("%Y-%m-%d") if meta["due_date"] else None
            }
            # 查询学生提交
            assignment_table = f"{course_part}_hw_{assign_no}"
            try:
                cur.execute(f"SELECT content, score, comment, submit_time FROM `{assignment_table}` WHERE studentemail=%s", (student_email,))
                sub = cur.fetchone()
            except Exception:
                sub = None
            submission_info = None
            if sub:
                submission_info = {
                    "content": sub["content"],
                    "submitTime": sub["submit_time"].strftime("%Y-%m-%d %H:%M:%S") if sub["submit_time"] else None,
                    "score": sub["score"],
                    "feedback": sub["comment"] or ""
                }
            return jsonify({"assignment": assignment_info, "submission": submission_info} if submission_info else {"assignment": assignment_info}), 200
    finally:
        conn.close()


@teacher_required
def get_teacher_assignment_api(assignment_id):
    """教师获取作业详情和所有学生提交情况"""
    teacher_email = g.user["email"]
    if "_hw_" not in assignment_id:
        return jsonify({"message": "作业ID无效"}), 400
    course_part, assign_no_part = assignment_id.split("_hw_", 1)
    if not assign_no_part.isdigit():
        return jsonify({"message": "作业ID无效"}), 400
    assign_no = int(assign_no_part)
    
    # 解析课程ID
    num_id = parse_course_id(course_part)
    if num_id is None:
        return jsonify({"message": "作业ID无效"}), 400
        
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT teacher_email FROM course WHERE course_id=%s", (num_id,))
            c = cur.fetchone()
            if not c:
                return jsonify({"message": "课程不存在"}), 404
            if c["teacher_email"] != teacher_email:
                return jsonify({"message": "无权限访问该作业"}), 403
            cur.execute("SELECT title, description, due_date FROM assignment WHERE course_id=%s AND assign_no=%s", (num_id, assign_no))
            meta = cur.fetchone()
            if not meta:
                return jsonify({"message": "作业不存在"}), 404
            assignment_info = {
                "title": meta["title"],
                "description": meta["description"] or "",
                "dueDate": meta["due_date"].strftime("%Y-%m-%d") if meta["due_date"] else None
            }
            assignment_table = f"{get_course_str_id(num_id)}_hw_{assign_no}"
            submissions_list = []
            try:
                cur.execute(f"SELECT studentemail, content, score, comment FROM `{assignment_table}`")
                subs = cur.fetchall()
            except Exception:
                subs = []
            # 获取学生姓名
            emails = [row["studentemail"] for row in subs] if subs else []
            names_map = {}
            if emails:
                format_str = ','.join(['%s'] * len(emails))
                cur.execute(f"SELECT useremail, username FROM student WHERE useremail IN ({format_str})", tuple(emails))
                for nr in cur.fetchall():
                    names_map[nr["useremail"]] = nr["username"]
            for row in subs:
                content_val = row["content"]
                if content_val and isinstance(content_val, str) and content_val.startswith("f_"):
                    content_val = request.host_url.strip('/') + f"/api/v1/files/{content_val}"
                submissions_list.append({
                    "studentEmail": row["studentemail"],
                    "studentName": names_map.get(row["studentemail"]),
                    "content": content_val,
                    "score": row["score"],
                    "feedback": row["comment"] or ""
                })
            return jsonify({"assignment": assignment_info, "submissions": submissions_list}), 200
    finally:
        conn.close()


@teacher_required
def grade_submission_api(assignment_id):
    """教师提交学生作业评分"""
    teacher_email = g.user["email"]
    data = request.get_json(silent=True) or {}
    student_email = data.get("studentEmail")
    score = data.get("score")
    feedback = data.get("feedback", "")
    if not student_email or score is None:
        return jsonify({"message": "参数不完整"}), 400
    if "_hw_" not in assignment_id:
        return jsonify({"message": "作业ID无效"}), 400
    course_part, assign_no_part = assignment_id.split("_hw_", 1)
    num_id = parse_course_id(course_part)
    if num_id is None or not assign_no_part.isdigit():
        return jsonify({"message": "作业ID无效"}), 400
    assign_no = int(assign_no_part)
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT teacher_email FROM course WHERE course_id=%s", (num_id,))
            c = cur.fetchone()
            if not c or c["teacher_email"] != teacher_email:
                return jsonify({"message": "无权限"}), 403
            course_str_id = get_course_str_id(num_id)
            students_table = f"{course_str_id}_students"
            try:
                cur.execute(f"SELECT 1 FROM `{students_table}` WHERE studentemail=%s", (student_email,))
                if not cur.fetchone():
                    return jsonify({"message": "学生不在该课程中"}), 404
            except Exception:
                return jsonify({"message": "学生不在该课程中"}), 404
            assignment_table = f"{course_str_id}_hw_{assign_no}"
            cur.execute(f"UPDATE `{assignment_table}` SET score=%s, comment=%s WHERE studentemail=%s",
                        (score, feedback, student_email))
        conn.commit()
        return jsonify({"message": "评分已保存", "status": "success"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"提交成绩失败: {e}"}), 500
    finally:
        conn.close()


@student_required
def submit_assignment_api(assignment_id):
    """学生提交作业接口"""
    student_email = g.user["email"]
    data = request.get_json(silent=True) or {}
    content = data.get("content")
    if content is None:
        return jsonify({"message": "没有提交内容"}), 400
    if "_hw_" not in assignment_id:
        return jsonify({"message": "作业ID无效"}), 400
    course_part, assign_no_part = assignment_id.split("_hw_", 1)
    num_id = parse_course_id(course_part)
    if num_id is None or not assign_no_part.isdigit():
        return jsonify({"message": "作业ID无效"}), 400
    assign_no = int(assign_no_part)
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 验证学生参与课程(使用student_course表)
            cur.execute("""
                SELECT 1 FROM student_course 
                WHERE useremail = %s AND course_id = %s
            """, (student_email, course_part))
            if not cur.fetchone():
                return jsonify({"message": "无权提交此作业"}), 403

            assignment_table = f"{course_part}_hw_{assign_no}"
            cur.execute(f"SELECT 1 FROM `{assignment_table}` WHERE studentemail=%s", (student_email,))
            if cur.fetchone():
                return jsonify({"message": "请勿重复提交"}), 400
            # 如果提交附件，已通过 /uploadfile 接口上传文件，文件标识在 content
            if isinstance(content, str) and content.startswith("f_"):
                file_id = content
                base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
                upload_dir = os.path.join(base_dir, "uploads")
                found_file = next((name for name in os.listdir(upload_dir) if name.startswith(file_id)), None)
                if found_file:
                    file_ext = found_file.split('.', 1)[1] if '.' in found_file else ""
                    asm_folder = os.path.join(base_dir, get_course_str_id(num_id), "homeworkList", f"hm{assign_no}")
                    ensure_dir(asm_folder)
                    dest_name = student_email.replace('@', '_').replace('.', '_') + ('.' + file_ext if file_ext else '')
                    try:
                        import shutil
                        shutil.copy(os.path.join(upload_dir, found_file), os.path.join(asm_folder, dest_name))
                    except Exception as e:
                        current_app.logger.error(f"Failed to copy file to assignment folder: {e}")
            now = datetime.datetime.now()
            cur.execute(f"INSERT INTO `{assignment_table}` (studentemail, content, score, comment, submit_time) VALUES (%s,%s,%s,%s,%s)",
                        (student_email, content, None, "", now))
        conn.commit()
        submission_info = {
            "content": content,
            "submitTime": now.strftime("%Y-%m-%d %H:%M:%S"),
            "score": None,
            "feedback": ""
        }
        return jsonify({"submission": submission_info}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"提交失败: {e}"}), 500
    finally:
        conn.close()


@teacher_required
def teacher_assignment_summary_api():
    """POST /api/teacher/assignment/summary
    Body: {role,useremail,token,course_id,assign_no}
    返回: {total:int, submitted:int, ungraded:int}
    """
    body = request.get_json(silent=True) or {}
    course_id = body.get("course_id")
    assign_no = body.get("assign_no")

    if not course_id or assign_no is None:
        return jsonify({"message": "参数缺失"}), 400
    try:
        assign_no = int(assign_no)
    except ValueError:
        return jsonify({"message": "assign_no 必须为整数"}), 400

    norm_cid   = normalize_course_id(course_id)
    teacher_em = g.user["email"]

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 权限校验
            cur.execute("SELECT teacher_email FROM course WHERE course_id=%s", (course_id,))
            row = cur.fetchone()
            if not row:
                return jsonify({"message": "课程不存在"}), 404
            if row["teacher_email"] != teacher_em:
                return jsonify({"message": "无权限"}), 403

            # 总人数
            cur.execute("SELECT COUNT(*) AS cnt FROM student_course WHERE course_id=%s", (course_id,))
            total = (cur.fetchone() or {}).get("cnt", 0)

            assignment_table = f"{norm_cid}_hw_{assign_no}"

            # 已提交
            try:
                cur.execute(f"SELECT COUNT(*) AS cnt FROM `{assignment_table}`")
                submitted = (cur.fetchone() or {}).get("cnt", 0)
            except Exception:
                submitted = 0

            # 待批改
            try:
                cur.execute(f"SELECT COUNT(*) AS cnt FROM `{assignment_table}` WHERE score IS NULL")
                ungraded = (cur.fetchone() or {}).get("cnt", 0)
            except Exception:
                ungraded = 0

        return jsonify(
            {"total": total, "submitted": submitted, "ungraded": ungraded}
        ), 200
    finally:
        conn.close()


@teacher_required
def auto_grade_assignment_api():
    """POST /api/teacher/assignment/auto-grade
    Body: {role,useremail,token,course_id,assign_no}
    简易示例：把所有未评分记录打 100 分
    返回: {graded:int, skipped:int}
    """
    body = request.get_json(silent=True) or {}
    course_id = body.get("course_id")
    assign_no = body.get("assign_no")

    if not course_id or assign_no is None:
        return jsonify({"message": "参数缺失"}), 400
    try:
        assign_no = int(assign_no)
    except ValueError:
        return jsonify({"message": "assign_no 必须为整数"}), 400

    norm_cid   = normalize_course_id(course_id)
    teacher_em = g.user["email"]

    conn = get_db_connection()
    graded  = 0
    skipped = 0
    try:
        with conn.cursor() as cur:
            # 权限校验
            cur.execute("SELECT teacher_email FROM course WHERE course_id=%s", (course_id,))
            row = cur.fetchone()
            if not row:
                return jsonify({"message": "课程不存在"}), 404
            if row["teacher_email"] != teacher_em:
                return jsonify({"message": "无权限"}), 403

            assignment_table = f"{norm_cid}_hw_{assign_no}"

            # 查询未评分记录
            try:
                cur.execute(f"SELECT studentemail FROM `{assignment_table}` WHERE score IS NULL")
                pending = [r["studentemail"] for r in cur.fetchall()]
            except Exception as e:
                return jsonify({"message": f"作业表不存在或查询失败: {e}"}), 500

            if not pending:
                return jsonify({"graded": 0, "skipped": 0}), 200

            # 简易批改逻辑：全部记 100 分
            for email in pending:
                cur.execute(
                    f"UPDATE `{assignment_table}` "
                    "SET score=%s, comment=%s WHERE studentemail=%s",
                    (100, "已自动评分", email),
                )
                graded += 1

        conn.commit()
        return jsonify({"graded": graded, "skipped": skipped}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"批改失败: {e}"}), 500
    finally:
        conn.close()
