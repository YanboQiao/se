"""
Assignment package initialization.
This module handles course assignments, student enrollments, and teacher dashboard functionality.
"""

# 导出主要API函数，使其可以从外部被导入
from .assignment import (
    # 应用初始化
    init_app,
    
    # 仪表盘相关API
    student_dashboard_api,
    teacher_dashboard_api,
    
    # 课程相关API
    get_student_course_api,
    get_teacher_course_api,
    create_course_api,
    
    # 学生管理API
    get_course_students_api,  # 新增：获取课程学生列表
    enroll_course_api,
    
    # 作业相关API
    create_assignment_api,
    get_student_assignment_api,
    get_teacher_assignment_api,
    submit_assignment_api,
    grade_submission_api,
    
    # 文件上传API
    upload_file_api,
    get_file_api
)

# 版本信息
__version__ = '1.0.0'

