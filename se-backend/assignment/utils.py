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
    """解析课程ID，支持多种格式，返回原始课程ID字符串"""
    # 如果是 course_xxx 格式，去掉前缀
    if course_id.startswith("course_"):
        return course_id.split("course_")[1]
    # 否则直接返回原始ID
    return course_id
