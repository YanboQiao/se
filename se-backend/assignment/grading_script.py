import os
import json
from pathlib import Path
import argparse
import mysql.connector # 新增：用于连接 MySQL
from openai import OpenAI

# --- 配置 ---
MOCK_AI = False  # True 会模拟 AI 返回，False 会尝试调用真实 API
os.environ["OPENAI_API_KEY"] = "sk-kBpsE8u98W1A1FBeE6780211E5Fd42D8B4A8E9A74346D82c" # 如果使用真实 OpenAI API

DB_CONFIG_FILE = "db_config.json" # 新增：MySQL配置文件名

def load_db_config(config_file=DB_CONFIG_FILE):
    """加载数据库配置文件"""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        print(f"✅ 数据库配置文件 '{config_file}' 加载成功。")
        return config
    except FileNotFoundError:
        print(f"❌ 错误: 数据库配置文件 '{config_file}' 未找到。请确保文件存在于脚本同目录下。")
        raise
    except json.JSONDecodeError:
        print(f"❌ 错误: 数据库配置文件 '{config_file}' 格式不正确。")
        raise
    except Exception as e:
        print(f"❌ 加载数据库配置时发生未知错误: {e}")
        raise

def save_grade_to_db(db_conn, course_id, assign_no, student_email, score, comment):
    """将单条批改记录保存到MySQL数据库。"""
    try:
        cursor = db_conn.cursor()
        # MySQL 使用 REPLACE INTO (如果主键或唯一键冲突，则先删除旧行再插入新行)
        # 或者 INSERT ... ON DUPLICATE KEY UPDATE ...
        # 这里使用 REPLACE INTO 比较简单，效果类似 SQLite 的 INSERT OR REPLACE
        sql = """
        REPLACE INTO homework (course_id, assign_no, student_email, score, comment)
        VALUES (%s, %s, %s, %s, %s)
        """
        values = (course_id, assign_no, student_email, score, comment)
        cursor.execute(sql, values) # 注意 MySQL connector 使用 %s 作为占位符
        db_conn.commit()
    except mysql.connector.Error as e:
        print(f"❌ MySQL数据库错误 (save_grade_to_db for {student_email}): {e}")
    except Exception as e:
        print(f"❌ 保存成绩到数据库时发生非数据库错误 ({student_email}): {e}")


def transform_filename_to_email(filename_stem: str) -> str:
    """
    将文件名（不含扩展名）转换为学生邮箱格式。
    例如: "2911247775_qq_com" -> "2911247775@qq.com"
    规则：第一个"_"替换为"@", 第二个"_"替换为"."
    """
    parts = []
    first_underscore_idx = filename_stem.find('_')

    if first_underscore_idx == -1:
        # 如果没有下划线，可能不是预期的格式，直接返回或按错误处理
        print(f"⚠️ 警告：文件名 '{filename_stem}' 不含下划线，无法按预期转换为邮箱。")
        return filename_stem

    part1 = filename_stem[:first_underscore_idx]
    remaining_after_first = filename_stem[first_underscore_idx + 1:]

    second_underscore_idx = remaining_after_first.find('_')

    if second_underscore_idx == -1:
        # 如果只有一个下划线
        print(f"⚠️ 警告：文件名 '{filename_stem}' 只含一个下划线，转换结果可能不完整。")
        return f"{part1}@{remaining_after_first}"

    part2 = remaining_after_first[:second_underscore_idx]
    part3 = remaining_after_first[second_underscore_idx + 1:]

    return f"{part1}@{part2}.{part3}"


def call_ai_grader(question_content, answer_content, student_submission_content):
    if MOCK_AI:
        import random
        score = random.randint(60, 100)
        comment = f"模拟评语：作业完成度较好，得分 {score}。"
        if any("error" in str(item.get("text", "")).lower() for item in student_submission_content if
               item["type"] == "text"):
            comment = "模拟评语：学生提交的文件似乎存在问题或读取错误。"
            score = 0
        return {"score": score, "comment": comment}
    try:
        # Initialize the OpenAI client
        # The API key is typically read from the OPENAI_API_KEY environment variable by default.
        # If you are using a redirect/proxy, you might need to set the base_url.
        # Example for your redirect:
        client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url="https://api.mctools.online/v1"
        )

        # Construct the messages for the API call
        # The student_submission_content_list is already in the format for multi-modal input if needed.
        # For now, assuming student_submission_content_list contains text items as per previous script logic.
        # We will concatenate student text submissions for this example.
        # For image support, the content list needs to be passed directly if the model supports it (e.g., gpt-4o)

        student_text_parts = []
        # student_image_parts = [] # For future image handling

        for item in student_submission_content:
            if item["type"] == "text":
                student_text_parts.append(item["text"])
            # elif item["type"] == "image_url": # Prepare for image handling
            #     student_image_parts.append(item)

        full_student_submission_text = "\n".join(student_text_parts)

        # Define the prompt for the AI
        # We instruct the AI to return a JSON object with "score" and "comment"
        system_prompt = """
            You are an AI assistant tasked with grading student homework.
            You will be given the "Assignment Question", the "Standard Answer", and the "Student's Submission".
            Your goal is to evaluate the student's submission based on the standard answer and the question.
            Provide a score out of 100 and a brief comment explaining the score.
            Your response MUST be a JSON object with two keys: "score" (integer) and "comment" (string).
            For example: {"score": 85, "comment": "The student correctly identified the main points but missed some details."}
            """

        user_prompt_content = f"""
            --- Assignment Question ---
            {question_content}

            --- Standard Answer ---
            {answer_content}

            --- Student's Submission ---
            {full_student_submission_text}
            """

        # If you want to include images directly with a model like gpt-4o:
        # user_message_content_parts = [
        #     {"type": "text", "text": f"--- Assignment Question ---\n{question_content}"},
        #     {"type": "text", "text": f"--- Standard Answer ---\n{answer_content}"},
        #     {"type": "text", "text": "--- Student's Submission ---"}
        # ]
        # user_message_content_parts.extend(student_submission_content_list) # This would pass text and images

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt_content}  # For text-only models
            # For multi-modal models like gpt-4o, the 'content' for the user role can be a list:
            # {"role": "user", "content": user_message_content_parts}
        ]

        print("🤖 Calling OpenAI API for grading...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Or use "gpt-4o" for better reasoning and multi-modal capabilities
            messages=messages,
            response_format={"type": "json_object"},  # Request JSON output
            temperature=0.2,  # Lower temperature for more deterministic grading
            max_tokens=500  # Adjust as needed for expected comment length
        )

        # Extract the response
        if response.choices and response.choices[0].message and response.choices[0].message.content:
            ai_response_content = response.choices[0].message.content
            print(f"✅ AI Response (raw): {ai_response_content}")
            try:
                # Parse the JSON response
                grading_result = json.loads(ai_response_content)
                if "score" in grading_result and "comment" in grading_result:
                    return {
                        "score": int(grading_result["score"]),
                        "comment": str(grading_result["comment"])
                    }
                else:
                    print("❌ AI response JSON does not contain 'score' or 'comment' keys.")
                    return {"score": -1, "comment": "Error: AI response format incorrect. Missing score/comment."}
            except json.JSONDecodeError:
                print(f"❌ Error decoding AI response JSON: {ai_response_content}")
                return {"score": -1, "comment": f"Error: AI response was not valid JSON. Raw: {ai_response_content}"}
        else:
            print("❌ No valid response content from AI.")
            return {"score": -1, "comment": "Error: No valid response from AI."}

    except Exception as e:
        print(f"❌ An error occurred while calling OpenAI API: {e}")
        return {"score": -1, "comment": f"Error during AI API call: {e}"}


def process_grading_task(homework_path_str: str):
    """主批改流程函数，增加了数据库回填。"""
    base_path = Path("courses/data")  # 项目的根数据路径
    homework_full_path = base_path / homework_path_str  # 作业的完整路径

    # 1. 解析 course_id 和 assign_no (作业编号)
    try:
        path_parts = homework_path_str.split('/')
        if len(path_parts) < 3 or path_parts[-2] != 'homework':
            raise ValueError(
                f"提供的作业路径格式不正确: '{homework_path_str}'。预期格式: 'course_id/homework/assign_no'")
        current_course_id = path_parts[0]
        current_assign_no = path_parts[-1]
    except Exception as e:
        print(f"❌ 错误：无法从路径 '{homework_path_str}' 解析课程ID和作业编号。{e}")
        return

    print(f"批改任务启动: 课程='{current_course_id}', 作业编号='{current_assign_no}'")

    # 定义输入和输出路径
    question_file = homework_full_path / "question.txt"
    answer_file = homework_full_path / "answer.txt"
    output_dir = homework_full_path / "comment"
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ 输出目录 '{output_dir}' 已确保存在。")  # 新增日志，方便确认
    except OSError as e:
        print(f"❌ 创建目录 '{output_dir}' 失败: {e}")

    db_conn = None
    db_config = None # 在 try 块外部先声明
    try:
        db_config = load_db_config()
        db_conn = mysql.connector.connect(**db_config)
    except mysql.connector.Error as e:
        print(f"❌ 严重错误：无法连接到MySQL数据库 (主机: {db_config.get('host') if db_config else '未知'}, 数据库: {db_config.get('database') if db_config else '未知'})。错误: {e}")
        return
    except Exception as e: # 捕获 load_db_config 可能抛出的其他异常
        print(f"❌ 严重错误：数据库配置或连接失败。错误: {e}")
        return

    try:
        question_content = question_file.read_text(encoding='utf-8')
        answer_content = answer_file.read_text(encoding='utf-8')
    except FileNotFoundError as e:
        print(f"❌ 错误：缺少题目或答案文件: {e}")
        if db_conn: db_conn.close()
        return

    for submission_file in homework_full_path.iterdir():
        if submission_file.is_dir() or submission_file.name in ["question.txt",
                                                                "answer.txt"] or submission_file.suffix == '.json':
            continue

        student_id_from_filename = submission_file.stem  # 文件名（不含扩展名）
        student_email = transform_filename_to_email(student_id_from_filename)
        output_file_path = output_dir / f"{student_id_from_filename}.json"  # AI评语的JSON文件名仍用原文件名

        # 幂等性：如果JSON评论文件已存在，则跳过AI批改和数据库写入 (或根据需要调整逻辑)
        if output_file_path.exists():
            print(f"⏭️ 作业 '{submission_file.name}' 的JSON评语已存在，跳过AI批改。")
            # 可选：即使JSON存在，也检查数据库并更新（如果需要）
            # try:
            #     with open(output_file_path, 'r', encoding='utf-8') as f:
            #         existing_result = json.load(f)
            #     save_grade_to_db(db_conn, current_course_id, current_assign_no, student_email,
            #                      existing_result.get('score'), existing_result.get('comment'))
            # except Exception as e:
            #     print(f"读取或保存已存在JSON到数据库时出错 {student_email}: {e}")
            continue

        print(f"⚙️ 正在处理学生 '{student_email}' (文件: {submission_file.name})...")

        student_content_list = []
        try:
            text_content = submission_file.read_text(encoding='utf-8')
            student_content_list.append({"type": "text", "text": text_content})
        except Exception as e:
            print(f"❌ 读取学生提交文件 '{submission_file.name}' 失败: {e}")
            student_content_list.append({"type": "text", "text": f"Error reading file: {e}"})  # 记录错误信息

        ai_result = call_ai_grader(question_content, answer_content, student_content_list)
        score = ai_result.get('score')
        comment = ai_result.get('comment')

        try:
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(ai_result, f, ensure_ascii=False, indent=4)
            print(f"   📄 AI评语已保存为JSON: {output_file_path.name}")
        except Exception as e:
            print(f"❌ 保存AI评语JSON文件失败 ({student_email}): {e}")
            # 即使JSON保存失败，也可能希望将AI结果存入数据库（如果AI调用成功）

        # 回填数据库
        if score is not None and comment is not None:  # 确保有有效评分结果
            save_grade_to_db(db_conn, current_course_id, current_assign_no, student_email, score, comment)
            print(
                f"   💾 -> MySQL数据库 (课程: {current_course_id}, 作业: {current_assign_no}, 学生: {student_email}, 分数: {score})")
        else:
            print(f"   ⚠️ 未获取到有效的AI评分和评语，不写入数据库 ({student_email})")

    if db_conn and db_conn.is_connected():
        db_conn.close()
    print(f"✅ 课程 '{current_course_id}', 作业 '{current_assign_no}' 处理完毕。")


# --- 主程序入口 (与之前版本类似，增加了数据库初始化调用) ---
if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="从指定的作业路径中提取 course_id 和 homework_id，执行批改任务，并将结果存入数据库。"
    )
    parser.add_argument(
        "homework_path",
        type=str,
        help="指向具体作业文件夹的相对路径 (相对于 'gpt_academic/courses/data/')。例如: rg_01/homework/1"
    )
    args = parser.parse_args()

    try:
        # 注意: homework_path 参数现在应该是相对于 base_path 的路径
        # 例如 'rg_01/homework/1'
        # 而不是之前的完整路径 'gpt_academic/courses/data/rg_01/homework/1'
        # 这是因为 process_grading_task 内部会拼接 base_path

        # 简单验证一下输入路径的格式，更复杂的验证在 process_grading_task 内
        if not (Path("gpt_academic/courses/data") / args.homework_path).is_dir():
            raise FileNotFoundError(
                f"推测的完整作业路径 {(Path('gpt_academic/courses/data') / args.homework_path)} 不存在或不是目录。请确保您提供的相对路径正确。")

        print(f"ℹ️ 接收到作业相对路径: {args.homework_path}")

        process_grading_task(args.homework_path)

    except FileNotFoundError as e:
        print(f"❌ 错误: {e}")
    except ValueError as e:  # process_grading_task 可能抛出ValueError
        print(f"❌ 错误: {e}")
    except Exception as e:
        print(f"❌ 执行过程中发生意外错误: {e}")