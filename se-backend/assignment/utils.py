import os
from flask import current_app


def ensure_dir(path):
    """确保目录存在"""
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        current_app.logger.error(f"Failed to create directory {path}: {e}")


def sanitize_email(email):
    """将邮箱转换为文件名安全的格式"""
    return email.replace('@', '_').replace('.', '_')


def check_submission_exists(course_id, assignment_no, student_email):
    """检查学生是否已提交指定作业
    
    Args:
        course_id: 课程ID，如 "rg_01"
        assignment_no: 作业编号，如 1
        student_email: 学生邮箱
        
    Returns:
        bool: 是否已提交
    """
    try:
        base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "courses", "data")
        homework_dir = os.path.join(base_dir, course_id, "homework", str(assignment_no))
        
        if not os.path.exists(homework_dir):
            return False
            
        filename = sanitize_email(student_email) + '.txt'
        file_path = os.path.join(homework_dir, filename)
        
        return os.path.exists(file_path)
    except Exception as e:
        current_app.logger.error(f"Error checking submission: {e}")
        return False


def get_assignment_description(course_id, assignment_no):
    """从文件系统获取作业描述
    
    Args:
        course_id: 课程ID，如 "rg_01"
        assignment_no: 作业编号，如 1
        
    Returns:
        str: 作业描述内容，如果文件不存在返回空字符串
    """
    try:
        base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "courses", "data")
        homework_dir = os.path.join(base_dir, course_id, "homework", str(assignment_no))
        question_file = os.path.join(homework_dir, "question.txt")
        
        if os.path.exists(question_file):
            with open(question_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        return ""
    except Exception as e:
        current_app.logger.error(f"Error reading assignment description: {e}")
        return ""


def get_course_str_id(numeric_id):
    """获取课程字符串ID（添加前缀）"""
    return f"course_{numeric_id}"


def normalize_course_id(cid: str) -> str:
    """始终返回带前缀的 course_xxx 形式"""
    return cid if cid.startswith("course_") else f"course_{cid}"


def parse_course_id(course_id):
    """解析课程ID，支持多种格式，返回原始课程ID字符串"""
    # 如果是 course_xxx 格式，去掉前缀
    if course_id.startswith("course_"):
        return course_id.split("course_")[1]
    # 否则直接返回原始ID
    return course_id


def sanitize_email_for_filename(email):
    """将邮箱地址转换为安全的文件名格式"""
    return email.replace('@', '_').replace('.', '_')
