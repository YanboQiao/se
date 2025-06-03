import datetime
from flask import jsonify, g

from login.auth import student_required, teacher_required
from login.db import get_db_connection
from .utils import get_course_str_id


@student_required
def student_dashboard_api():
    """学生仪表盘：我的课程、待办任务、老师评语（含课程完整信息）"""
    student_email = g.user["email"]
    data_out = {"courses": [], "todos": [], "messages": []}

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    c.course_id,
                    c.course_name,
                    c.course_desc,
                    c.start_time,
                    c.end_time,
                    t.username AS teacher_name
                FROM student_course sc
                JOIN course         c ON sc.course_id   = c.course_id
                LEFT JOIN teacher   t ON c.teacher_email = t.useremail
                WHERE sc.useremail = %s
                """,
                (student_email,),
            )
            for row in cur.fetchall():
                data_out["courses"].append(
                    {
                        "id":          row["course_id"],
                        "name":        row["course_name"],
                        "description": row.get("course_desc") or "",
                        "startDate":   row["start_time"].strftime("%Y-%m-%d") if row.get("start_time") else None,
                        "endDate":     row["end_time"].strftime("%Y-%m-%d")   if row.get("end_time")   else None,
                        "teacher":     row.get("teacher_name") or "",
                    }
                )
            # 待办任务 / 消息 保持空
    finally:
        conn.close()
    return jsonify(data_out), 200


@teacher_required
def teacher_dashboard_api():
    """教师仪表盘：返回我的课程（含统计）、待批改作业、学生消息"""
    teacher_email = g.user["email"]

    data_out = {"courses": [], "gradingList": [], "messages": []}
    now = datetime.datetime.now()

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 拿到教师课程基本信息
            cur.execute(
                """
                SELECT course_id, course_name, course_desc, start_time, end_time
                FROM course
                WHERE teacher_email=%s
                """,
                (teacher_email,),
            )
            courses = cur.fetchall()
            course_ids = [c["course_id"] for c in courses]

            # 组装课程统计信息
            for c in courses:
                cid = c["course_id"]
                course_str = get_course_str_id(cid)

                # 选课人数
                cur.execute(
                    "SELECT COUNT(*) AS cnt FROM student_course WHERE course_id=%s",
                    (cid,),
                )
                student_cnt = (cur.fetchone() or {}).get("cnt", 0)

                # 待批改数量（所有作业未评分）
                cur.execute(
                    "SELECT assign_no FROM assignment WHERE course_id=%s",
                    (cid,),
                )
                assigns = [row["assign_no"] for row in cur.fetchall()]
                ungraded_total = 0
                for no in assigns:
                    assignment_table = f"{course_str}_hw_{no}"
                    try:
                        cur.execute(
                            f"SELECT COUNT(*) AS cnt FROM `{assignment_table}` WHERE score IS NULL"
                        )
                        ungraded_total += (cur.fetchone() or {}).get("cnt", 0)
                    except Exception:
                        # 表不存在等异常，忽略
                        continue

                status_txt = (
                    "已结束"
                    if c["end_time"] and c["end_time"] < now
                    else "进行中"
                )

                data_out["courses"].append(
                    {
                        "id": cid,
                        "name": c["course_name"],
                        "description": c.get("course_desc") or "",
                        "startDate": c["start_time"].strftime("%Y-%m-%d")
                        if c.get("start_time")
                        else None,
                        "endDate": c["end_time"].strftime("%Y-%m-%d")
                        if c.get("end_time")
                        else None,
                        "status": status_txt,
                        "studentCount": student_cnt,
                        "ungradedCount": ungraded_total,
                    }
                )

            # 生成待批改作业列表（沿用旧逻辑）
            grading_list = []
            for cid in course_ids:
                course_str = get_course_str_id(cid)
                cur.execute(
                    "SELECT assign_no, title FROM assignment WHERE course_id=%s",
                    (cid,),
                )
                for asm in cur.fetchall():
                    assign_no, title = asm["assign_no"], asm["title"]
                    assignment_table = f"{course_str}_hw_{assign_no}"
                    try:
                        cur.execute(
                            f"SELECT 1 FROM `{assignment_table}` WHERE score IS NULL LIMIT 1"
                        )
                        if cur.fetchone():
                            grading_list.append(
                                {
                                    "id": f"{course_str}_hw_{assign_no}",
                                    "title": title,
                                }
                            )
                    except Exception:
                        continue
            data_out["gradingList"] = grading_list

            # 学生消息功能暂无，实现占位
            data_out["messages"] = []
    finally:
        conn.close()

    return jsonify(data_out), 200
