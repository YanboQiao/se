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


def normalize_course_id(cid: str) -> str:
    """始终返回带前缀的 course_xxx 形式"""
    return cid if cid.startswith("course_") else f"course_{cid}"


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
