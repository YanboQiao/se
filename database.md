# 智能软件工程助手网站 – 数据库设计文档

## 1\. 数据库结构设计

智能作业助手系统使用关系型数据库来存储主要业务数据。根据需求分析确定的实体和关系，设计了如下主要数据表：

### 1.1. User (用户) 表

存储系统用户的基本信息。

* **主要字段**:  
  * `useremail` (主键)  
  * `username` (姓名)  
  * `password` (密码)  
  * `token` (32位随机字符串)  
* **说明**:  
  * `useremail` 是主键，`username` 不是（后端同学一定注意这一点）。  
  * `useremail`\+`token` 作为鉴权组合，如果匹配则正常返回数据。  
  * 分别建立了 `stutent` 和 `teacher` 表，根据前端传回来的不同的 `role` 进行区分。

### 1.2. Course (课程) 表

存储课程的基本信息。

* **主要字段**:  
  * `course_id` (主键)  
  * `course_name` (课程名称)  
  * `coursedesc` (课程描述)  
  * `teacher_email` (教师邮箱)  
  * `start_time` (课程开始时间戳, 格式为年月日时分秒，例: `2025-02-01 00:00:00`)  
  * `end_time` (课程结束时间时间戳, 相同格式)  
  * `homeworks` (留了几次作业, int整数, 默认为0)

### 1.3. 打分表

* **表名**: `{course_id}_{homework_id}` (使用字段拼接形成新的表名)  
  * **举例**: `rg_01_1` (courseid为 ‘rg\_01’ 这门课的第一次作业的评分列表)  
* **主要字段**:  
  * `useremail` (学生邮箱)  
  * `score` (对应学生在这门课对应作业取得的成绩，使用int)

### 1.4. 学生课程信息表

* **表名**: `{useremail}_course` (使用学生邮箱和 ‘\_course’ 拼接形成新的表名)  
  * **举例**: `qiaoyanbo408_gmail_com_course`  
* **主要字段**:  
  * `course_id` (只有一列，用于存放该学生所有参加的课程的课程id)

### 1.5. 作业存储表

**课程作业维护表 {course\_id)\_homeworks**  
**举例：rg\_01\_homeworks**

| homework\_id作业编号 | homework\_desc作业描述 | deadline截止日期 | 备注 |
| ----- | ----- | ----- | ----- |
| 1 | 基础编程练习 | 2025-03-15 23:59:59 | 熟悉编程环境 |
| 2 | 数据结构实现 | 2025-03-22 23:59:59 | 实现链表和树结构 |
| ... | ... | ... | ... |

**说明：**

* **作业编号：** 按照课程的作业顺序编号，例如"作业1-base"、"作业2"等。  
* **作业描述：** 简要描述作业的内容和要求。  
* **截止日期：** 明确的作业提交截止时间，格式为“年月日时分秒”，如“2025-03-15 23:59:59”。  
* **教师上传的文件：** 指向教师发布的作业文件的路径，例如 "file/{course\_id}/homework\_01/question.md"。  
* **教师上传的标准答案：** 指向教师提供的标准答案文件的路径，例如 "file/{course\_id}/homework\_01/answer.md"。  
* **备注：** 可以添加一些额外的说明或注意事项，例如作业难度、重点等。

**补充：**

* \`{course\_id}\` 需要替换成实际的课程ID，如 "rg\_01"。  
* 随着课程的进行，您可以继续添加新的作业行。  
* 表格中的路径格式遵循文档中 "2.1 作业文件存储" 的定义。  
* 此表格可以在电子表格软件（如 Excel、Google Sheets）中创建和维护，便于管理和更新。

希望这个表格对您有所帮助！如有其他需求，请随时告诉我。

## 2\. 文件及数据存储结构

对于每一个用户，需要创建文件夹。文件夹结构进行如下设计：

### 2.1. 作业文件存储

* **路径格式**: `file/{course_id}/{homework_id}/homework/`  
* `教师上传的文件放在`: `file/{course_id}/{homework_id}/`  
* **示例**:  
  * `file/rg_01/homework_01/homework/qiaoyanbo408_gmail_com.pdf` (学生邮箱为 `qiaoyanbo408@gmail.com` 所上传提交的作业的路径)  
  * `file/rg_01/homework_01/question.md` (教师上传的作业)  
  * `file/rg_01/homework_01/answer.md` (教师上传的标准答案)  
  * `file/rg_01/homework_01/feedback/qiaoyanbo408_gmail_com_py.pdf` (学生邮箱为 `qiaoyanbo408@gmail.com` 所上传提交的作业的评语的路径)

### 2.2. 对话历史存储

* **学生对话历史**:  
  * 路径格式: `data/student/{useremail}/chat_{id}.md`  
  * 示例: `data/student/qiaoyanbo408_gmail_com/chat_1.md` (`qiaoyanbo408@gmail.com` 这个学生的第一次对话历史)  
* **教师对话历史**:  
  * 路径格式: `data/teacher/{useremail}/chat_{id}.md`  
  * 示例: `data/teacher/joeyanbo608_gmail_com/chat_2.md` (`joeyanbo608@gmail.com` 这个教师的第二次的对话历史)
