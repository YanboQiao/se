import datetime
import os
from flask import jsonify, request, send_file

from .utils import ensure_dir


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
    ensure_dir(upload_dir)
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


def get_file_api(file_id):
    """文件下载接口"""
    base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    upload_dir = os.path.join(base_dir, "uploads")
    target_file = next((name for name in os.listdir(upload_dir) if name.startswith(file_id)), None)
    if not target_file:
        return jsonify({"message": "文件不存在"}), 404
    return send_file(os.path.join(upload_dir, target_file), as_attachment=True, download_name=target_file)
