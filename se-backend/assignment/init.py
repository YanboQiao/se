import os
import datetime
from flask import jsonify, request, current_app, send_file
from login.auth import student_required, teacher_required
from login.db import get_db_connection

# 工具函数：确保目录存在
def _ensure_dir(path):
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        current_app.logger.error(f"Failed to create directory {path}: {e}")

# 获取课程字符串ID（添加前缀）
def _get_course_str_id(numeric_id):
    return f"course_{numeric_id}"

@student_required
def student_dashboard_api():
    """学生仪表盘：返回我的课程、待办任务、老师评语等"""
    from flask import g
    student_email = g.user["email"]
    data_out = {"courses": [], "todos": [], "messages": []}
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 获取学生已选课程列表
            safe_email = student_email.replace('@', '_').replace('.', '_')
            course_list_table = f"{safe_email}_course"
            try:
                cur.execute(f"SELECT course_id FROM `{course_list_table}`")
                rows = cur.fetchall()
                course_ids = [row["course_id"] for row in rows]
            except Exception:
                course_ids = []
            for cid in course_ids:
                cur.execute("SELECT course_name FROM course WHERE course_id=%s", (cid,))
                res = cur.fetchone()
                course_name = res["course_name"] if res else f"课程 {cid}"
                data_out["courses"].append({"id": cid, "name": course_name})
            # 待办任务和老师评语暂未实现
    finally:
        conn.close()
    return jsonify(data_out), 200

@teacher_required
def teacher_dashboard_api():
    """教师仪表盘：返回我的课程、待批改作业、学生消息等"""
    from flask import g
    teacher_email = g.user["email"]
    data_out = {"courses": [], "gradingList": [], "messages": []}
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT course_id, course_name FROM course WHERE teacher_email=%s", (teacher_email,))
            courses = cur.fetchall()
            course_ids = [c["course_id"] for c in courses]
            data_out["courses"] = [{"id": _get_course_str_id(c["course_id"]), "name": c["course_name"]} for c in courses]
            # 待批改作业列表：存在未评分提交的作业
            grading_list = []
            for cid in course_ids:
                course_str = _get_course_str_id(cid)
                cur.execute("SELECT assign_no, title FROM assignment WHERE course_id=%s", (cid,))
                for asm in cur.fetchall():
                    assign_no, title = asm["assign_no"], asm["title"]
                    assignment_table = f"{course_str}_hw_{assign_no}"
                    try:
                        cur.execute(f"SELECT 1 FROM `{assignment_table}` WHERE score IS NULL")
                        if cur.fetchone():
                            grading_list.append({"id": f"{course_str}_hw_{assign_no}", "title": title})
                    except Exception:
                        continue
            data_out["gradingList"] = grading_list
            data_out["messages"] = []  # 学生消息（如学生提问）暂无实现
    finally:
        conn.close()
    return jsonify(data_out), 200

@student_required
def get_student_course_api(course_id):
    """学生获取课程详情（课程信息及作业列表）"""
    from flask import g
    student_email = g.user["email"]
    # 新结构下课程ID为字符串，直接使用
    num_id = course_id
    if not num_id:
        return jsonify({"message": "课程ID无效"}), 400
    conn = get_db_connection()
    data_out = {"course": {}, "assignments": []}
    try:
        with conn.cursor() as cur:
            # 验证学生已选该课程
            safe_email = student_email.replace('@', '_').replace('.', '_')
            course_list_table = f"{safe_email}_course"
            try:
                cur.execute(f"SELECT 1 FROM `{course_list_table}` WHERE course_id=%s", (course_id,))
                if not cur.fetchone():
                    return jsonify({"message": "未选该课程"}), 403
            except Exception:
                return jsonify({"message": "未选该课程"}), 403
            cur.execute("SELECT course_name FROM course WHERE course_id=%s", (course_id,))
            res = cur.fetchone()
            course_name = res["course_name"] if res else f"课程 {course_id}"
            data_out["course"] = {"id": course_id, "name": course_name}
            # 获取课程所有作业列表及提交状态
            cur.execute("SELECT assign_no, title, due_date FROM assignment WHERE course_id=%s", (course_id,))
            for asm in cur.fetchall():
                no, title, due_date = asm["assign_no"], asm["title"], asm["due_date"]
                assignment_id = f"{course_id}_hw_{no}"
                assignment_table = f"{course_id}_hw_{no}"
                try:
                    cur.execute(f"SELECT score FROM `{assignment_table}` WHERE studentemail=%s", (student_email,))
                    sub = cur.fetchone()
                except Exception:
                    sub = None
                submitted = bool(sub)
                score = sub["score"] if sub and sub["score"] is not None else None
                data_out["assignments"].append({
                    "id": assignment_id,
                    "title": title,
                    "dueDate": due_date.strftime("%Y-%m-%d") if due_date else None,
                    "submitted": submitted,
                    "score": score
                })
    finally:
        conn.close()
    return jsonify(data_out), 200

@teacher_required
def get_teacher_course_api(course_id):
    """教师获取课程详情（课程信息及作业列表）"""
    from flask import g
    teacher_email = g.user["email"]
    # 解析课程ID字符串
    num_id = None
    if course_id.startswith("course_"):
        try:
            num_id = int(course_id.split("course_")[1])
        except:
            num_id = None
    elif "_" in course_id:
        try:
            num_id = int(course_id.split('_')[-1])
        except:
            num_id = None
    else:
        try:
            num_id = int(course_id)
        except:
            num_id = None
    if num_id is None:
        return jsonify({"message": "课程ID无效"}), 400
    conn = get_db_connection()
    data_out = {"course": {}, "assignments": []}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT course_name, teacher_email FROM course WHERE course_id=%s", (num_id,))
            course = cur.fetchone()
            if not course:
                return jsonify({"message": "课程不存在"}), 404
            if course["teacher_email"] != teacher_email:
                return jsonify({"message": "无权限访问该课程"}), 403
            data_out["course"] = {"id": course_id, "name": course["course_name"]}
            cur.execute("SELECT assign_no, title, due_date FROM assignment WHERE course_id=%s", (num_id,))
            now = datetime.datetime.now()
            for asm in cur.fetchall():
                no, title, due_date = asm["assign_no"], asm["title"], asm["due_date"]
                status = ""
                if due_date:
                    status = "已截止" if due_date < now else "进行中"
                data_out["assignments"].append({
                    "id": f"{_get_course_str_id(num_id)}_hw_{no}",
                    "title": title,
                    "dueDate": due_date.strftime("%Y-%m-%d") if due_date else None,
                    "status": status
                })
    finally:
        conn.close()
    return jsonify(data_out), 200

@teacher_required
def create_assignment_api(course_id):
    """教师在课程中布置新作业"""
    from flask import g
    teacher_email = g.user["email"]
    data = request.get_json(silent=True) or {}
    title = data.get("title")
    description = data.get("description", "")
    due_date_str = data.get("dueDate")
    reference_answer = data.get("referenceAnswer", "")
    if not title or not title.strip():
        return jsonify({"message": "标题不能为空"}), 400
    # 解析课程ID
    num_id = None
    if course_id.startswith("course_"):
        try:
            num_id = int(course_id.split("course_")[1])
        except:
            num_id = None
    elif "_" in course_id:
        try:
            num_id = int(course_id.split('_')[-1])
        except:
            num_id = None
    else:
        try:
            num_id = int(course_id)
        except:
            num_id = None
    if num_id is None:
        return jsonify({"message": "课程ID无效"}), 400
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT teacher_email FROM course WHERE course_id=%s", (num_id,))
            res = cur.fetchone()
            if not res:
                return jsonify({"message": "课程不存在"}), 404
            if res["teacher_email"] != teacher_email:
                return jsonify({"message": "无权限"}), 403
            # 新作业序号
            cur.execute("SELECT MAX(assign_no) AS max_no FROM assignment WHERE course_id=%s", (num_id,))
            row = cur.fetchone()
            next_no = (row["max_no"] + 1) if row and row["max_no"] else 1
            due_date = None
            if due_date_str:
                try:
                    due_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d")
                except:
                    due_date = None
            # 插入作业记录
            cur.execute(
                "INSERT INTO assignment (course_id, assign_no, title, description, due_date, reference_answer) VALUES (%s,%s,%s,%s,%s,%s)",
                (num_id, next_no, title, description, due_date, reference_answer)
            )
            # 创建作业提交记录表
            course_str = _get_course_str_id(num_id)
            assignment_table = f"{course_str}_hw_{next_no}"
            create_sql = (
                f"CREATE TABLE `{assignment_table}` ("
                "studentemail VARCHAR(320) NOT NULL, "
                "content TEXT, score INT, comment TEXT, submit_time DATETIME, "
                "PRIMARY KEY (studentemail))"
            )
            cur.execute(create_sql)
        conn.commit()
        # 创建作业文件夹结构
        base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        course_folder = os.path.join(base_dir, course_str)
        _ensure_dir(course_folder)
        _ensure_dir(os.path.join(course_folder, "homeworkList"))
        asm_folder = os.path.join(course_folder, "homeworkList", f"hm{next_no}")
        _ensure_dir(asm_folder)
        if description:
            try:
                with open(os.path.join(asm_folder, "homeworkRequirement.txt"), "w", encoding="utf-8") as f:
                    f.write(description)
            except Exception as e:
                current_app.logger.error(f"Failed to write homeworkRequirement: {e}")
        if reference_answer:
            try:
                with open(os.path.join(asm_folder, "homeworkAnswer.txt"), "w", encoding="utf-8") as f:
                    f.write(reference_answer)
            except Exception as e:
                current_app.logger.error(f"Failed to write homeworkAnswer: {e}")
        status = ""
        if due_date:
            status = "已截止" if due_date < datetime.datetime.now() else "进行中"
        assignment_data = {
            "id": f"{course_str}_hw_{next_no}",
            "title": title,
            "dueDate": due_date.strftime("%Y-%m-%d") if due_date else None,
            "status": status
        }
        return jsonify({"assignment": assignment_data}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"创建作业失败: {e}"}), 500
    finally:
        conn.close()

@student_required
def get_student_assignment_api(assignment_id):
    """学生获取作业详情和自己的提交"""
    from flask import g
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
            # 验证学生参与课程
            safe_email = student_email.replace('@', '_').replace('.', '_')
            course_list_table = f"{safe_email}_course"
            try:
                cur.execute(f"SELECT 1 FROM `{course_list_table}` WHERE course_id=%s", (course_part,))
                if not cur.fetchone():
                    return jsonify({"message": "无权访问该作业"}), 403
            except Exception:
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
            assignment_table = f"{_get_course_str_id(num_id)}_hw_{assign_no}"
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
    from flask import g
    teacher_email = g.user["email"]
    if "_hw_" not in assignment_id:
        return jsonify({"message": "作业ID无效"}), 400
    course_part, assign_no_part = assignment_id.split("_hw_", 1)
    if not assign_no_part.isdigit():
        return jsonify({"message": "作业ID无效"}), 400
    assign_no = int(assign_no_part)
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
            assignment_table = f"{_get_course_str_id(num_id)}_hw_{assign_no}"
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
    from flask import g
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
    num_id = None
    if course_part.startswith("course_"):
        try:
            num_id = int(course_part.split("course_")[1])
        except:
            num_id = None
    elif "_" in course_part:
        try:
            num_id = int(course_part.split('_')[-1])
        except:
            num_id = None
    else:
        try:
            num_id = int(course_part)
        except:
            num_id = None
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
            course_str_id = _get_course_str_id(num_id)
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
def enroll_course_api(course_id):
    """学生选课（加入课程）"""
    from flask import g
    student_email = g.user["email"]
    # 支持数字ID或字符串ID
    if course_id.isdigit():
        course_id_str = f"course_{course_id}"
        num_id = int(course_id)
    else:
        course_id_str = course_id
        if course_id.startswith("course_"):
            try:
                num_id = int(course_id.split("course_")[1])
            except:
                num_id = None
        elif "_" in course_id:
            try:
                num_id = int(course_id.split('_')[-1])
            except:
                num_id = None
        else:
            try:
                num_id = int(course_id)
            except:
                num_id = None
    if num_id is None:
        return jsonify({"message": "课程ID无效"}), 400
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT course_name FROM course WHERE course_id=%s", (num_id,))
            course = cur.fetchone()
            if not course:
                return jsonify({"message": "课程不存在"}), 404
            course_name = course["course_name"]
            safe_email = student_email.replace('@', '_').replace('.', '_')
            course_list_table = f"{safe_email}_course"
            cur.execute(f"CREATE TABLE IF NOT EXISTS `{course_list_table}` (course_id VARCHAR(128) PRIMARY KEY)")
            cur.execute(f"SELECT 1 FROM `{course_list_table}` WHERE course_id=%s", (course_id_str,))
            if cur.fetchone():
                return jsonify({"message": "已在课程中"}), 400
            cur.execute(f"INSERT INTO `{course_list_table}` (course_id) VALUES (%s)", (course_id_str,))
            students_table = f"{course_id_str}_students"
            cur.execute(f"CREATE TABLE IF NOT EXISTS `{students_table}` (studentemail VARCHAR(320) PRIMARY KEY)")
            cur.execute(f"SELECT 1 FROM `{students_table}` WHERE studentemail=%s", (student_email,))
            if not cur.fetchone():
                cur.execute(f"INSERT INTO `{students_table}` (studentemail) VALUES (%s)", (student_email,))
        conn.commit()
        return jsonify({"course": {"id": course_id_str, "name": course_name}}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"选课失败: {e}"}), 500
    finally:
        conn.close()

@student_required
def drop_course_api(course_id):
    """学生退课（退出课程）"""
    from flask import g
    student_email = g.user["email"]
    # 新结构下课程ID为字符串，直接使用
    course_id_str = course_id
    if not course_id_str:
        return jsonify({"message": "课程ID无效"}), 400
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            safe_email = student_email.replace('@', '_').replace('.', '_')
            course_list_table = f"{safe_email}_course"
            try:
                cur.execute(f"SELECT 1 FROM `{course_list_table}` WHERE course_id=%s", (course_id_str,))
                if not cur.fetchone():
                    return jsonify({"message": "未选该课程"}), 400
            except Exception:
                return jsonify({"message": "未选该课程"}), 400
            cur.execute(f"DELETE FROM `{course_list_table}` WHERE course_id=%s", (course_id_str,))
            students_table = f"{course_id_str}_students"
            try:
                cur.execute(f"DELETE FROM `{students_table}` WHERE studentemail=%s", (student_email,))
            except Exception:
                pass
        conn.commit()
        return jsonify({"message": "退课成功"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"退课失败: {e}"}), 500
    finally:
        conn.close()

@teacher_required
def create_course_api():
    """教师创建新课程"""
    from flask import g
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
            cur.execute("INSERT INTO course (course_name, course_desc, teacher_email, start_time, end_time) VALUES (%s,%s,%s,%s,%s)",
                        (course_name, course_desc, teacher_email, now, end_time))
            course_id = cur.lastrowid
        conn.commit()
        course_str = _get_course_str_id(course_id)
        # 创建课程学生表
        with conn.cursor() as cur:
            cur.execute(f"CREATE TABLE IF NOT EXISTS `{course_str}_students` (studentemail VARCHAR(320) PRIMARY KEY)")
        conn.commit()
        # 创建课程文件夹结构
        base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        course_folder = os.path.join(base_dir, course_str)
        _ensure_dir(course_folder)
        _ensure_dir(os.path.join(course_folder, "homeworkList"))
        _ensure_dir(os.path.join(course_folder, "courseware"))
        return jsonify({"course": {"id": course_str, "name": course_name}}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"创建课程失败: {e}"}), 500
    finally:
        conn.close()

def init_app(app: Flask):
    # 挂载各接口路由到 Flask 应用
    app.add_url_rule("/api/student/dashboard", endpoint="student_dashboard", view_func=student_dashboard_api, methods=["GET"])
    app.add_url_rule("/api/teacher/dashboard", endpoint="teacher_dashboard", view_func=teacher_dashboard_api, methods=["GET"])
    app.add_url_rule("/api/student/course/<course_id>", endpoint="student_course_info", view_func=get_student_course_api, methods=["GET"])
    app.add_url_rule("/api/teacher/course/<course_id>", endpoint="teacher_course_info", view_func=get_teacher_course_api, methods=["GET"])
    app.add_url_rule("/api/teacher/course/<course_id>/assignments", endpoint="create_assignment", view_func=create_assignment_api, methods=["POST"])
    app.add_url_rule("/api/student/assignment/<assignment_id>", endpoint="student_assignment_info", view_func=get_student_assignment_api, methods=["GET"])
    app.add_url_rule("/api/teacher/assignment/<assignment_id>", endpoint="teacher_assignment_info", view_func=get_teacher_assignment_api, methods=["GET"])
    app.add_url_rule("/api/teacher/assignment/<assignment_id>/grade", endpoint="grade_assignment", view_func=grade_submission_api, methods=["POST"])
    app.add_url_rule("/api/student/assignment/<assignment_id>/submit", endpoint="submit_assignment", view_func=submit_assignment_api, methods=["POST"])
    app.add_url_rule("/api/student/course/<course_id>/enroll", endpoint="enroll_course", view_func=enroll_course_api, methods=["POST"])
    app.add_url_rule("/api/student/course/<course_id>/drop", endpoint="drop_course", view_func=drop_course_api, methods=["POST"])
    app.add_url_rule("/api/teacher/courses", endpoint="create_course", view_func=create_course_api, methods=["POST"])
    app.add_url_rule("/api/v1/uploadfile", endpoint="upload_file", view_func=upload_file_api, methods=["POST"])
    app.add_url_rule("/api/v1/files/<file_id>", endpoint="get_file", view_func=get_file_api, methods=["GET"])

def upload_file_api():
    """文件上传接口"""
    file = request.files.get('file')
    if not file:
        return jsonify({"code": 400, "message": "No file provided", "data": None}), 400
    filename = file.filename
    import secrets
    file_id = "f_" + secrets.token_hex(5)
    base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    upload_dir = os.path.join(base_dir, "uploads")
    _ensure_dir(upload_dir)
    ext = filename.rsplit('.', 1)[1] if '.' in filename else ""
    save_name = file_id + (("." + ext) if ext else "")
    file_path = os.path.join(upload_dir, save_name)
    try:
        file.save(file_path)
    except Exception as e:
        return jsonify({"code": 500, "message": f"Upload failed: {e}", "data": None}), 500
    file_url = request.host_url.strip('/') + f"/api/v1/files/{file_id}"
    return jsonify({
        "code": 0,
        "message": "Upload success",
        "data": {
            "fileId": file_id,
            "fileName": filename,
            "fileUrl": file_url,
            "contentType": file.mimetype,
            "size": os.path.getsize(file_path),
            "uploadedAt": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        }
    }), 200

@student_required
def submit_assignment_api(assignment_id):
    """学生提交作业接口"""
    from flask import g
    student_email = g.user["email"]
    data = request.get_json(silent=True) or {}
    content = data.get("content")
    if content is None:
        return jsonify({"message": "没有提交内容"}), 400
    if "_hw_" not in assignment_id:
        return jsonify({"message": "作业ID无效"}), 400
    course_part, assign_no_part = assignment_id.split("_hw_", 1)
    num_id = None
    if course_part.startswith("course_"):
        try:
            num_id = int(course_part.split("course_")[1])
        except:
            num_id = None
    elif "_" in course_part:
        try:
            num_id = int(course_part.split('_')[-1])
        except:
            num_id = None
    else:
        try:
            num_id = int(course_part)
        except:
            num_id = None
    if num_id is None or not assign_no_part.isdigit():
        return jsonify({"message": "作业ID无效"}), 400
    assign_no = int(assign_no_part)
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 验证学生参与课程
            safe_email = student_email.replace('@', '_').replace('.', '_')
            course_list_table = f"{safe_email}_course"
            try:
                cur.execute(f"SELECT 1 FROM `{course_list_table}` WHERE course_id=%s", (course_part,))
                if not cur.fetchone():
                    return jsonify({"message": "无权提交此作业"}), 403
            except Exception:
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
                    asm_folder = os.path.join(base_dir, _get_course_str_id(num_id), "homeworkList", f"hm{assign_no}")
                    _ensure_dir(asm_folder)
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

def get_file_api(file_id):
    """文件下载接口"""
    base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    upload_dir = os.path.join(base_dir, "uploads")
    target_file = next((name for name in os.listdir(upload_dir) if name.startswith(file_id)), None)
    if not target_file:
        return jsonify({"message": "文件不存在"}), 404
    return send_file(os.path.join(upload_dir, target_file), as_attachment=True, download_name=target_file)