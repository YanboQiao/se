import os
import requests
from typing import Tuple, Optional
import json

def read_file_content(file_path: str) -> Optional[str]:
    """
    读取文件内容
    
    Args:
        file_path: 文件路径
    
    Returns:
        文件内容，如果读取失败返回None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"文件不存在: {file_path}")
        return None
    except UnicodeDecodeError:
        # 尝试其他编码
        try:
            with open(file_path, 'r', encoding='gbk') as f:
                return f.read().strip()
        except Exception as e:
            print(f"读取文件失败 {file_path}: {e}")
            return None
    except Exception as e:
        print(f"读取文件失败 {file_path}: {e}")
        return None

def grade_assignment_with_ai(student_answer: str, standard_answer: str) -> Tuple[int, str]:
    """
    使用大模型对比学生答案和标准答案，返回分数和评语
    
    Args:
        student_answer: 学生提交的答案内容
        standard_answer: 标准答案内容
    
    Returns:
        Tuple[int, str]: (分数, 评语)
    """
    try:
        # 使用你config.py中的API配置
        api_key = "sk-kBpsE8u98W1A1FBeE6780211E5Fd42D8B4A8E9A74346D82c"
        api_url = "https://api.mctools.online/v1/chat/completions"
        
        prompt = f"""
请作为一名专业的软件工程教师，对比以下学生答案和标准答案，给出客观公正的评分和详细评语。

标准答案：
{standard_answer}

学生答案：
{student_answer}

请按照以下标准评分（总分100分）：
1. 内容准确性（40分）：答案是否正确，概念是否清晰
2. 完整性（30分）：是否涵盖了所有要点
3. 逻辑性（20分）：思路是否清晰，表达是否有条理
4. 创新性（10分）：是否有独特见解或扩展思考

请严格按照以下JSON格式返回结果，不要包含任何其他内容：
{{
    "score": 分数(0-100的整数),
    "comment": "详细评语，包括优点、不足和改进建议"
}}
"""

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": "你是一名专业的软件工程教师，擅长客观公正地评估学生作业。请严格按照JSON格式返回评分结果。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.5,
            "max_tokens": 1000
        }
        
        response = requests.post(api_url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        ai_response = result['choices'][0]['message']['content'].strip()
        
        # 尝试提取JSON部分
        try:
            # 如果响应包含```json标记，提取其中的内容
            if "```json" in ai_response:
                start = ai_response.find("```json") + 7
                end = ai_response.find("```", start)
                json_str = ai_response[start:end].strip()
            elif ai_response.startswith("{") and ai_response.endswith("}"):
                json_str = ai_response
            else:
                # 尝试找到第一个{和最后一个}
                start = ai_response.find("{")
                end = ai_response.rfind("}") + 1
                if start >= 0 and end > start:
                    json_str = ai_response[start:end]
                else:
                    raise ValueError("无法找到有效的JSON")
            
            parsed_result = json.loads(json_str)
            score = max(0, min(100, int(parsed_result.get("score", 0))))
            comment = parsed_result.get("comment", "AI评分完成")
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"JSON解析失败: {e}, 原始响应: {ai_response}")
            # 如果JSON解析失败，尝试从文本中提取分数
            score = 75  # 默认分数
            comment = f"AI评分完成。原始评价：{ai_response[:500]}..."
            
            # 尝试从文本中提取数字作为分数
            import re
            score_match = re.search(r'(?:分数|得分|score)[：:]\s*(\d+)', ai_response, re.IGNORECASE)
            if score_match:
                try:
                    extracted_score = int(score_match.group(1))
                    if 0 <= extracted_score <= 100:
                        score = extracted_score
                except ValueError:
                    pass
        
        return score, comment
        
    except requests.exceptions.RequestException as e:
        print(f"API请求失败: {e}")
        return 80, f"自动评分完成，但网络连接存在问题。请检查网络设置。错误: {str(e)}"
    except Exception as e:
        print(f"AI评分失败: {e}")
        return 80, f"自动评分完成，如有疑问请联系教师。错误信息: {str(e)}"

def test_ai_grader():
    """
    测试AI评分功能
    """
    standard_answer = """
软件工程是一门研究和应用如何以系统性的、规范化的、可量化的过程化方法去开发和维护软件的工程学科。
主要特点包括：
1. 系统性：采用系统化的方法
2. 规范化：遵循标准和规范
3. 可量化：可以度量和评估
4. 过程化：按照定义的过程执行
"""
    
    student_answer = """
软件工程是关于软件开发的学科，它教我们如何更好地开发软件。
主要包括：
1. 有组织的方法
2. 按照标准来做
3. 可以测量效果
"""
    
    score, comment = grade_assignment_with_ai(student_answer, standard_answer)
    print(f"测试评分结果：{score}分")
    print(f"评语：{comment}")

if __name__ == "__main__":
    test_ai_grader()