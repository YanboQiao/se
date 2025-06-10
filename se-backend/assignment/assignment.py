"""
重构后的主模块文件
导入和协调所有子模块的功能
"""
from flask import Flask

# 导入各个子模块
from .dashboard import student_dashboard_api, teacher_dashboard_api
from .course import (
    get_student_course_api, get_teacher_course_api, 
    create_course_api, enroll_course_api
)
from .assignment_ops import (
    create_assignment_api, get_student_assignment_api, get_teacher_assignment_api,
    grade_submission_api, submit_assignment_api, 
    teacher_assignment_summary_api, auto_grade_assignment_api,
    get_student_assignment_detail_api, submit_assignment_rest_api
)
from .file_ops import upload_file_api, get_file_api
from .student_management import get_course_students_api, search_students_api, batch_enroll_students_api

# 为了向后兼容，保留这些函数的引用
# 这样其他代码仍然可以从 assignment.assignment 导入这些函数


def init_app(app: Flask):
    """初始化应用路由
    
    注册所有API路由到Flask应用
    这个函数保持与原来相同的接口，确保向后兼容
    """
    # 仪表盘API
    app.add_url_rule("/api/student/dashboard", endpoint="student_dashboard", 
                     view_func=student_dashboard_api, methods=["GET"])
    app.add_url_rule("/api/teacher/dashboard", endpoint="teacher_dashboard", 
                     view_func=teacher_dashboard_api, methods=["GET"])
    
    # 课程API
    app.add_url_rule("/api/student/course/<course_id>", endpoint="student_course_info", 
                     view_func=get_student_course_api, methods=["GET"])
    app.add_url_rule("/api/teacher/course/<course_id>", endpoint="teacher_course_info", 
                     view_func=get_teacher_course_api, methods=["GET"])
    app.add_url_rule("/api/teacher/courses", endpoint="create_course", 
                     view_func=create_course_api, methods=["POST"])
    app.add_url_rule("/api/student/course/<course_id>/enroll", endpoint="enroll_course", 
                     view_func=enroll_course_api, methods=["POST"])
    
    # 作业API
    app.add_url_rule("/api/teacher/assignment/create", endpoint="create_assignment", 
                     view_func=create_assignment_api, methods=["POST"])
    app.add_url_rule("/api/student/assignment/info", endpoint="student_assignment_info", 
                     view_func=get_student_assignment_api, methods=["POST"])
    app.add_url_rule("/api/student/assignment/<assignment_id>", endpoint="student_assignment_detail", 
                     view_func=get_student_assignment_detail_api, methods=["GET"])
    app.add_url_rule("/api/teacher/assignment/info", endpoint="teacher_assignment_info", 
                     view_func=get_teacher_assignment_api, methods=["POST"])
    app.add_url_rule("/api/teacher/assignment/grade", endpoint="grade_assignment", 
                     view_func=grade_submission_api, methods=["POST"])
    app.add_url_rule("/api/student/assignment/submit", endpoint="submit_assignment", 
                     view_func=submit_assignment_api, methods=["POST"])
    # 新增的REST风格提交端点
    app.add_url_rule("/api/student/assignment/<assignment_id>/submit", endpoint="submit_assignment_rest", 
                     view_func=submit_assignment_rest_api, methods=["POST"])
    
    # 作业统计和自动批改API
    app.add_url_rule("/api/teacher/assignment/summary", endpoint="assignment_summary",
                     view_func=teacher_assignment_summary_api, methods=["POST"])
    app.add_url_rule("/api/teacher/assignment/auto-grade", endpoint="auto_grade",
                     view_func=auto_grade_assignment_api, methods=["POST"])
    
    # 文件API
    app.add_url_rule("/api/v1/uploadfile", endpoint="upload_file", 
                     view_func=upload_file_api, methods=["POST"])
    app.add_url_rule("/api/v1/files/<file_id>", endpoint="get_file", 
                     view_func=get_file_api, methods=["GET"])
    
    # 学生管理API
    app.add_url_rule("/api/teacher/course/<course_id>/students", endpoint="course_students", 
                     view_func=get_course_students_api, methods=["GET"])
    app.add_url_rule("/api/teacher/search-students", endpoint="search_students", 
                     view_func=search_students_api, methods=["GET"])
    app.add_url_rule("/api/teacher/batch-enroll", endpoint="batch_enroll_students", 
                     view_func=batch_enroll_students_api, methods=["POST"])
    
    # 创建课程API (修复路径)
    app.add_url_rule("/api/teacher/course/create", endpoint="create_course_new", 
                     view_func=create_course_api, methods=["POST"])

