"""
Assignment package initialization.
This module handles course assignments, student enrollments, and teacher dashboard functionality.
"""

# 从重构后的主模块导入应用初始化函数
from .assignment import init_app

# 从各个专门模块导入API函数以保持向后兼容性
from .dashboard import student_dashboard_api, teacher_dashboard_api
from .course import (
    get_student_course_api, get_teacher_course_api, 
    create_course_api, enroll_course_api
)
from .assignment_ops import (
    create_assignment_api, get_student_assignment_api, get_teacher_assignment_api,
    grade_submission_api, submit_assignment_api, 
    teacher_assignment_summary_api, auto_grade_assignment_api
)
from .file_ops import upload_file_api, get_file_api
from .student_management import get_course_students_api

# 导出所有API函数，保持与原来相同的接口
__all__ = [
    # 应用初始化
    'init_app',
    
    # 仪表盘相关API
    'student_dashboard_api',
    'teacher_dashboard_api',
    
    # 课程相关API
    'get_student_course_api',
    'get_teacher_course_api',
    'create_course_api',
    'enroll_course_api',
    
    # 作业相关API
    'create_assignment_api',
    'get_student_assignment_api',
    'get_teacher_assignment_api',
    'submit_assignment_api',
    'grade_submission_api',
    'teacher_assignment_summary_api',
    'auto_grade_assignment_api',
    
    # 文件操作API
    'upload_file_api',
    'get_file_api',
    
    # 学生管理API
    'get_course_students_api'
]

# 版本信息
__version__ = '1.0.0'

