import os
from flask import current_app


def ensure_dir(path):
    """确保目录存在"""
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        current_app.logger.error(f"Failed to create directory {path}: {e}")


def get_course_str_id(numeric_id):
    """获取课程字符串ID（添加前缀）"""
    return f"course_{numeric_id}"


def normalize_course_id(course_id):
    """
    规范化课程ID，确保格式一致
    例如: "rg_01" -> "rg_01", "course_rg_01" -> "rg_01"
    """
    if isinstance(course_id, str):
        # 如果包含 "course_" 前缀，去掉它
        if course_id.startswith("course_"):
            return course_id.replace("course_", "")
        return course_id.strip()
    return str(course_id)


def parse_course_id(course_id):
    """解析课程ID，支持多种格式"""
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
    return num_id
