import datetime
import os
from flask import jsonify, g, request, current_app

from .grading_script import process_grading_task
from login.auth import student_required, teacher_required
from login.db import get_db_connection
from .utils import ensure_dir, get_course_str_id, parse_course_id, normalize_course_id, sanitize_email_for_filename
import json


@teacher_required
def create_assignment_api():
    """教师创建新作业

    请求体格式:
    {
        "course_id": "rg_01",
        "title": "作业标题",
        "description": "作业描述",
        "dueDate": "2025-06-30",  # 可选，YYYY-MM-DD格式
        "referenceAnswer": "参考答案",  # 可选
        "useremail": "teacher@example.com",
        "token": "auth_token"
    }

    Returns:
        成功: 200 OK, {"assignment": {...}}
        失败: 400/403/404/500 错误信息
    """
    teacher_email = g.user["email"]
    data = request.get_json(silent=True) or {}

    # 1. 获取并验证请求参数
    course_id = data.get("course_id")
    title = data.get("title")
    description = data.get("description", "")
    question = data.get("question", "")
    due_date_str = data.get("dueDate")
    reference_answer = data.get("referenceAnswer", "")

    # 验证必填字段
    if not course_id:
        return jsonify({"message": "课程ID不能为空"}), 400
    if not title or not title.strip():
        return jsonify({"message": "标题不能为空"}), 400
    if not question or not question.strip():
        return jsonify({"message": "作业内容不能为空"}), 400

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
                    # 支持多种日期格式
                    if 'T' in due_date_str:
                        # datetime-local格式: "2025-06-30T23:59"
                        due_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%dT%H:%M")
                    else:
                        # 纯日期格式: "2025-06-30"
                        due_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d")
                except Exception as e:
                    return jsonify({"message": f"日期格式无效: {str(e)}，请使用YYYY-MM-DD或YYYY-MM-DDTHH:MM格式"}), 400

            # 6. 插入作业记录（只存储基本信息，不包含reference_answer字段）
            cur.execute(
                "INSERT INTO assignment (course_id, assign_no, title, description, due_date) VALUES (%s,%s,%s,%s,%s)",
                (clean_course_id, next_no, title, description, due_date)
            )

            # 注意：不需要创建单独的作业表，系统使用统一的 homework 表存储所有评分数据

            # 8. 提交事务
            conn.commit()

            # 9. 创建作业文件存储目录（按照新的路径结构）
            base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "courses", "data")
            course_folder = os.path.join(base_dir, clean_course_id)
            homework_folder = os.path.join(course_folder, "homework", str(next_no))
            ensure_dir(homework_folder)

            # 10. 保存作业题目和参考答案为独立的txt文件
            if question:
                try:
                    with open(os.path.join(homework_folder, "question.txt"), "w", encoding="utf-8") as f:
                        f.write(question)
                except Exception as e:
                    current_app.logger.error(f"保存作业题目文件失败: {e}")

            if reference_answer:
                try:
                    with open(os.path.join(homework_folder, "answer.txt"), "w", encoding="utf-8") as f:
                        f.write(reference_answer)
                except Exception as e:
                    current_app.logger.error(f"保存参考答案文件失败: {e}")

            # 11. 构建响应数据
            status = ""
            if due_date:
                status = "已截止" if due_date < datetime.datetime.now() else "进行中"

            assignment_data = {
                "id": f"{clean_course_id}_hw_{next_no}",  # 使用简化的ID格式
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
def get_student_assignment_api():
    """学生获取作业详情和自己的提交
    
    请求体格式:
    {
        "course_id": "rg_01" 或数字,
        "assign_no": 1
    }
    """
    student_email = g.user["email"]
    data = request.get_json(silent=True) or {}
    
    course_id = data.get("course_id")
    assign_no = data.get("assign_no")
    
    if not course_id or assign_no is None:
        return jsonify({"message": "缺少必要参数 course_id 或 assign_no"}), 400
    
    # 解析课程ID
    if isinstance(course_id, str):
        parsed_id = parse_course_id(course_id)
    else:
        parsed_id = str(course_id)
        
    if parsed_id is None:
        return jsonify({"message": "课程ID无效"}), 400
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 验证学生参与课程(使用student_course表)
            cur.execute("""
                        SELECT 1
                        FROM student_course
                        WHERE useremail = %s
                          AND course_id = %s
                        """, (student_email, parsed_id))
            if not cur.fetchone():
                return jsonify({"message": "无权访问该作业"}), 403

            # 查询作业基本信息
            cur.execute("SELECT title, description, due_date FROM assignment WHERE course_id=%s AND assign_no=%s",
                        (parsed_id, assign_no))
            meta = cur.fetchone()
            if not meta:
                return jsonify({"message": "作业不存在"}), 404
            assignment_info = {
                "title": meta["title"],
                "description": meta["description"] or "",
                "dueDate": meta["due_date"].strftime("%Y-%m-%d") if meta["due_date"] else None
            }
            # 查询学生提交（使用统一的homework表）
            try:
                cur.execute(
                    "SELECT content, score, comment, submit_time FROM homework WHERE course_id=%s AND assign_no=%s AND student_email=%s",
                    (parsed_id, assign_no, student_email))
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
            return jsonify({"assignment": assignment_info, "submission": submission_info} if submission_info else {
                "assignment": assignment_info}), 200
    finally:
        conn.close()


@teacher_required
def get_teacher_assignment_api():
    """教师获取作业详情和所有学生提交情况
    
    请求体格式:
    {
        "course_id": "rg_01" 或数字,
        "assign_no": 1
    }
    """
    teacher_email = g.user["email"]
    data = request.get_json(silent=True) or {}
    
    course_id = data.get("course_id")
    assign_no = data.get("assign_no")
    
    if not course_id or assign_no is None:
        return jsonify({"message": "缺少必要参数 course_id 或 assign_no"}), 400
    
    # 解析课程ID - 数据库中的course_id是字符串
    if isinstance(course_id, str):
        parsed_id = parse_course_id(course_id)
    else:
        parsed_id = str(course_id)
        
    if parsed_id is None:
        return jsonify({"message": "课程ID无效"}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT teacher_email FROM course WHERE course_id=%s", (parsed_id,))
            c = cur.fetchone()
            if not c:
                return jsonify({"message": "课程不存在"}), 404
            if c["teacher_email"] != teacher_email:
                return jsonify({"message": "无权限访问该作业"}), 403
            cur.execute("SELECT title, description, due_date FROM assignment WHERE course_id=%s AND assign_no=%s",
                        (parsed_id, assign_no))
            meta = cur.fetchone()
            if not meta:
                return jsonify({"message": "作业不存在"}), 404
            assignment_info = {
                "title": meta["title"],
                "description": meta["description"] or "",
                "dueDate": meta["due_date"].strftime("%Y-%m-%d") if meta["due_date"] else None
            }
            # 获取课程中的所有学生
            cur.execute("""
                SELECT s.useremail, s.username 
                FROM student s 
                JOIN student_course sc ON s.useremail = sc.useremail 
                WHERE sc.course_id = %s
            """, (parsed_id,))
            all_students = cur.fetchall()
            
            # 获取作业评分信息（从homework表）
            homework_grades = {}
            try:
                cur.execute("SELECT student_email, score, comment FROM homework WHERE course_id=%s AND assign_no=%s", (parsed_id, assign_no))
                for row in cur.fetchall():
                    homework_grades[row["student_email"]] = {
                        "score": row["score"],
                        "comment": row["comment"] or ""
                    }
            except Exception:
                pass
            
            # 检查文件系统中的提交
            base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "courses", "data")
            homework_dir = os.path.join(base_dir, parsed_id, "homework", str(assign_no))
            
            submissions_list = []
            for student in all_students:
                student_email = student["useremail"]
                student_name = student["username"]
                
                # 构建文件名（邮箱格式转换）
                # 例如: qiaoyanbo408@gmail.com -> qiaoyanbo408_gmail_com.txt
                filename = student_email.replace('@', '_').replace('.', '_') + '.txt'
                file_path = os.path.join(homework_dir, filename)
                
                # 检查是否有提交文件
                content = None
                has_submission = False
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                        has_submission = True
                    except Exception as e:
                        current_app.logger.error(f"读取作业文件失败 {file_path}: {e}")
                        content = "文件读取失败"
                
                # 如果有提交或者有评分记录，就加入到列表中
                grade_info = homework_grades.get(student_email, {"score": None, "comment": ""})
                if has_submission or grade_info["score"] is not None:
                    # 限制内容预览长度
                    content_preview = content[:10] + "..." if content and len(content) > 10 else content or ""
                    
                    submissions_list.append({
                        "studentEmail": student_email,
                        "studentName": student_name,
                        "content": content or "",  # 完整内容，用于评分弹窗
                        "contentPreview": content_preview,  # 预览内容，用于卡片显示
                        "score": grade_info["score"],
                        "feedback": grade_info["comment"],
                        "hasSubmission": has_submission,
                        "gradingStatus": "已评分" if grade_info["score"] is not None else ("已提交" if has_submission else "未提交")
                    })
            return jsonify({"assignment": assignment_info, "submissions": submissions_list}), 200
    finally:
        conn.close()


@teacher_required
def grade_submission_api():
    """教师提交学生作业评分
    
    请求体格式:
    {
        "course_id": "rg_01" 或数字,
        "assign_no": 1,
        "studentEmail": "student@example.com",
        "score": 85,
        "feedback": "做得很好"
    }
    """
    teacher_email = g.user["email"]
    data = request.get_json(silent=True) or {}
    
    course_id = data.get("course_id")
    assign_no = data.get("assign_no")
    student_email = data.get("studentEmail")
    score = data.get("score")
    feedback = data.get("feedback", "")
    
    if not course_id or assign_no is None or not student_email or score is None:
        return jsonify({"message": "参数不完整"}), 400
    
    # 解析课程ID
    if isinstance(course_id, str):
        parsed_id = parse_course_id(course_id)
    else:
        parsed_id = str(course_id)
        
    if parsed_id is None:
        return jsonify({"message": "课程ID无效"}), 400
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT teacher_email FROM course WHERE course_id=%s", (parsed_id,))
            c = cur.fetchone()
            if not c or c["teacher_email"] != teacher_email:
                return jsonify({"message": "无权限"}), 403
            # 验证学生是否在课程中（使用student_course表）
            try:
                cur.execute("SELECT 1 FROM student_course WHERE useremail=%s AND course_id=%s", (student_email, parsed_id))
                if not cur.fetchone():
                    return jsonify({"message": "学生不在该课程中"}), 404
            except Exception:
                return jsonify({"message": "学生不在该课程中"}), 404
            
            # 检查homework表中是否已有记录
            cur.execute("SELECT 1 FROM homework WHERE course_id=%s AND assign_no=%s AND student_email=%s",
                        (parsed_id, assign_no, student_email))
            exists = cur.fetchone()
            
            if exists:
                # 更新现有记录
                cur.execute("UPDATE homework SET score=%s, comment=%s WHERE course_id=%s AND assign_no=%s AND student_email=%s",
                            (score, feedback, parsed_id, assign_no, student_email))
            else:
                # 插入新记录（学生提交了作业但数据库中没有记录）
                cur.execute(
                    "INSERT INTO homework (course_id, assign_no, student_email, score, comment) VALUES (%s,%s,%s,%s,%s)",
                    (parsed_id, assign_no, student_email, score, feedback)
                )
        conn.commit()
        return jsonify({"message": "评分已保存", "status": "success"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"提交成绩失败: {e}"}), 500
    finally:
        conn.close()


@student_required
def submit_assignment_api():
    """学生提交作业接口
    
    请求体格式:
    {
        "course_id": "rg_01" 或数字,
        "assign_no": 1,
        "content": "作业内容"
    }
    """
    student_email = g.user["email"]
    data = request.get_json(silent=True) or {}
    
    course_id = data.get("course_id")
    assign_no = data.get("assign_no")
    content = data.get("content")
    
    if not course_id or assign_no is None or content is None:
        return jsonify({"message": "缺少必要参数"}), 400
    
    # 解析课程ID
    if isinstance(course_id, str):
        parsed_id = parse_course_id(course_id)
    else:
        parsed_id = str(course_id)
        
    if parsed_id is None:
        return jsonify({"message": "课程ID无效"}), 400
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 验证学生参与课程(使用student_course表)
            cur.execute("""
                        SELECT 1
                        FROM student_course
                        WHERE useremail = %s
                          AND course_id = %s
                        """, (student_email, parsed_id))
            if not cur.fetchone():
                return jsonify({"message": "无权提交此作业"}), 403

            # 检查是否已经提交过（通过文件系统检查）
            base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "courses", "data")
            homework_dir = os.path.join(base_dir, parsed_id, "homework", str(assign_no))
            ensure_dir(homework_dir)
            
            # 构建学生作业文件名
            filename = student_email.replace('@', '_').replace('.', '_') + '.txt'
            file_path = os.path.join(homework_dir, filename)
            
            # 检查是否已经提交过
            if os.path.exists(file_path):
                return jsonify({"message": "请勿重复提交"}), 400
            
            # 保存作业内容到文件系统
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                return jsonify({"message": f"保存作业失败: {e}"}), 500
            
            # 如果提交附件，已通过 /uploadfile 接口上传文件，文件标识在 content
            if isinstance(content, str) and content.startswith("f_"):
                file_id = content
                upload_dir = os.path.join(base_dir, "uploads")
                found_file = next((name for name in os.listdir(upload_dir) if name.startswith(file_id)), None)
                if found_file:
                    file_ext = found_file.split('.', 1)[1] if '.' in found_file else ""
                    dest_name = student_email.replace('@', '_').replace('.', '_') + ('.' + file_ext if file_ext else '')
                    try:
                        import shutil
                        shutil.copy(os.path.join(upload_dir, found_file), os.path.join(homework_dir, dest_name))
                    except Exception as e:
                        current_app.logger.error(f"Failed to copy file to assignment folder: {e}")
            
            now = datetime.datetime.now()
        conn.commit()  # 虽然没有数据库操作，但保持事务一致性
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
    import os
    body = request.get_json(silent=True) or {}
    course_id = body.get("course_id")
    assign_no = body.get("assign_no")

    if not course_id or assign_no is None:
        return jsonify({"message": "参数缺失"}), 400
    try:
        assign_no = int(assign_no)
    except ValueError:
        return jsonify({"message": "assign_no 必须为整数"}), 400

    norm_cid = normalize_course_id(course_id)
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

            # 从文件系统统计已提交人数并获取提交的学生邮箱列表
            # 使用实际存储路径格式，course_id 在文件系统中通常是去掉 course_ 前缀的
            actual_course_id = course_id
            if course_id.startswith("course_"):
                actual_course_id = course_id.replace("course_", "")
            
            homework_dir = f"courses/data/{actual_course_id}/homework/{assign_no}"
            submitted = 0
            submitted_students = set()  # 存储已提交的学生邮箱
            
            if os.path.exists(homework_dir):
                for filename in os.listdir(homework_dir):
                    # 跳过非学生提交文件（如 question.txt, answer.txt）
                    if filename.endswith('.txt') and '@' not in filename and '_' in filename:
                        # 从文件名恢复学生邮箱
                        # 例如 qiaoyanbo408_gmail_com.txt -> qiaoyanbo408@gmail.com
                        # 例如 2911247775_qq_com.txt -> 2911247775@qq.com
                        base_name = filename.replace('.txt', '')
                        parts = base_name.split('_')
                        if len(parts) >= 3:
                            # 重新构建邮箱格式：最后两部分作为域名，前面的作为用户名
                            email_local = '_'.join(parts[:-2])
                            email_domain = '.'.join(parts[-2:])
                            student_email = f"{email_local}@{email_domain}"
                            submitted_students.add(student_email)
                            submitted += 1

            # 从统一的 homework 表获取已评分的学生邮箱列表
            graded_students = set()
            
            try:
                cur.execute(
                    "SELECT student_email FROM homework WHERE course_id=%s AND assign_no=%s AND score IS NOT NULL",
                    (actual_course_id, assign_no)
                )
                for row in cur.fetchall():
                    graded_students.add(row["student_email"])
            except Exception as e:
                # 如果查询失败，记录错误但继续执行
                print(f"查询homework表失败: {e}")
                pass

            # 计算待批改数量：已提交但未评分的学生数量
            ungraded_students = submitted_students - graded_students
            ungraded = len(ungraded_students)

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

    graded = 0
    skipped = 0

    # 构建作业答案目录路径
    # 当前 assignment.py 所在目录
    current_dir = os.path.dirname(__file__)

    # 上级目录，即 se-backend/
    project_root = os.path.abspath(os.path.join(current_dir, ".."))

    # 构建目标文件路径：courses/data/<course_id>/homework/<assign_no>/answer.txt
    base_dir = os.path.join(
        project_root, "courses", "data", course_id, "homework", str(assign_no)
    )

    homework_dir = course_id + "/" + "homework" + "/" + str(assign_no)

    # 确保目录存在
    if not os.path.isdir(base_dir):
        return jsonify({"message": "作业目录不存在"}), 404

    graded = 0
    skipped = 0

    # 遍历该目录下的所有 txt 文件，忽略 answer.txt 和 question.txt
    for fname in os.listdir(base_dir):
        if not fname.endswith(".txt"):
            continue
        if fname in ["answer.txt", "question.txt"]:
            continue

        student_path = os.path.join(base_dir, fname)

        # 假设评分信息为：生成 fname+".score.json"
        score_path = student_path.replace(".txt", ".score.json")

        # 如果已评分则跳过
        if os.path.exists(score_path):
            try:
                with open(score_path, "r", encoding="utf-8") as f:
                    score_data = json.load(f)
                if "score" in score_data:
                    skipped += 1
                    continue
            except:
                pass

        # 写入评分
        process_grading_task(homework_dir)

    return jsonify({"graded": graded, "skipped": skipped}), 200


@student_required
def get_student_assignment_detail_api(assignment_id):
    """学生通过REST风格URL获取作业详情和自己的提交
    
    URL格式: /api/student/assignment/{assignment_id}
    assignment_id格式: {course_id}_hw_{assign_no}，例如: rg_01_hw_1
    """
    student_email = g.user["email"]
    
    # 解析 assignment_id
    try:
        parts = assignment_id.split('_hw_')
        if len(parts) != 2:
            return jsonify({"message": "作业ID格式无效"}), 400
        course_id = parts[0]
        assign_no = int(parts[1])
    except (ValueError, IndexError):
        return jsonify({"message": "作业ID格式无效"}), 400
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 验证学生参与课程
            cur.execute("""
                        SELECT 1
                        FROM student_course
                        WHERE useremail = %s
                          AND course_id = %s
                        """, (student_email, course_id))
            if not cur.fetchone():
                return jsonify({"message": "无权访问该作业"}), 403

            # 查询作业基本信息
            cur.execute("SELECT title, description, due_date FROM assignment WHERE course_id=%s AND assign_no=%s",
                        (course_id, assign_no))
            meta = cur.fetchone()
            if not meta:
                return jsonify({"message": "作业不存在"}), 404
            
            assignment_info = {
                "title": meta["title"],
                "description": meta["description"] or "",
                "dueDate": meta["due_date"].strftime("%Y-%m-%d") if meta["due_date"] else None
            }
            
            # 检查文件系统中的提交状态
            base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "courses", "data")
            homework_dir = os.path.join(base_dir, course_id, "homework", str(assign_no))
            filename = sanitize_email_for_filename(student_email) + '.txt'
            file_path = os.path.join(homework_dir, filename)
            
            submission_info = None
            if os.path.exists(file_path):
                # 读取提交内容
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except Exception:
                    content = "无法读取提交内容"
                
                # 获取文件修改时间作为提交时间
                import time
                submit_time = time.ctime(os.path.getmtime(file_path))
                
                # 查询批改信息
                cur.execute(
                    "SELECT score, comment FROM homework WHERE course_id=%s AND assign_no=%s AND student_email=%s",
                    (course_id, assign_no, student_email))
                grade_info = cur.fetchone()
                
                submission_info = {
                    "content": content,
                    "submitTime": submit_time,
                    "score": grade_info["score"] if grade_info else None,
                    "feedback": grade_info["comment"] if grade_info else ""
                }
            
            return jsonify({
                "assignment": assignment_info, 
                "submission": submission_info
            }), 200
    finally:
        conn.close()


@student_required
def submit_assignment_rest_api(assignment_id):
    """学生通过REST风格URL提交作业
    
    URL格式: /api/student/assignment/{assignment_id}/submit
    assignment_id格式: {course_id}_hw_{assign_no}，例如: rg_01_hw_1
    
    请求体格式:
    {
        "content": "作业内容"
    }
    """
    student_email = g.user["email"]
    data = request.get_json(silent=True) or {}
    
    # 解析 assignment_id
    try:
        parts = assignment_id.split('_hw_')
        if len(parts) != 2:
            return jsonify({"message": "作业ID格式无效"}), 400
        course_id = parts[0]
        assign_no = int(parts[1])
    except (ValueError, IndexError):
        return jsonify({"message": "作业ID格式无效"}), 400
    
    content = data.get("content")
    if content is None:
        return jsonify({"message": "缺少作业内容"}), 400
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 验证学生参与课程
            cur.execute("""
                        SELECT 1
                        FROM student_course
                        WHERE useremail = %s
                          AND course_id = %s
                        """, (student_email, course_id))
            if not cur.fetchone():
                return jsonify({"message": "无权提交此作业"}), 403

            # 检查是否已经提交过（通过文件系统检查）
            base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "courses", "data")
            homework_dir = os.path.join(base_dir, course_id, "homework", str(assign_no))
            ensure_dir(homework_dir)
            
            # 构建学生作业文件名
            filename = sanitize_email_for_filename(student_email) + '.txt'
            file_path = os.path.join(homework_dir, filename)
            
            # 检查是否已经提交过
            if os.path.exists(file_path):
                return jsonify({"message": "请勿重复提交"}), 400
            
            # 保存作业内容到文件系统
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                return jsonify({"message": f"保存作业失败: {e}"}), 500
            
            # 如果提交附件，已通过 /uploadfile 接口上传文件，文件标识在 content
            if isinstance(content, str) and content.startswith("f_"):
                file_id = content
                upload_dir = os.path.join(base_dir, "uploads")
                found_file = next((name for name in os.listdir(upload_dir) if name.startswith(file_id)), None)
                if found_file:
                    file_ext = found_file.split('.', 1)[1] if '.' in found_file else ""
                    dest_name = sanitize_email_for_filename(student_email) + ('.' + file_ext if file_ext else '')
                    try:
                        import shutil
                        shutil.copy(os.path.join(upload_dir, found_file), os.path.join(homework_dir, dest_name))
                    except Exception as e:
                        current_app.logger.error(f"Failed to copy file to assignment folder: {e}")
            
            now = datetime.datetime.now()
        conn.commit()  # 虽然没有数据库操作，但保持事务一致性
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

