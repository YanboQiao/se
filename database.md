教师学生表如下 分别放在student teacher两张表下

| useremail             | username | password | token |
|-----------------------|----------|----------|-------|
| joeyanbo608@gmail.com | 杨仁树      | 114514   | xxxx  |

以下是 **课程（`course`）实体** 的 Markdown 规格表，便于后端同学直接对照数据库

> 约束说明里若出现 “→ 表.字段” 表示外键指向；如无特别说明可按 MySQL 8.0 默认引擎（InnoDB）创建。

| 字段名             | 数据类型            | 约束 / 默认值                                    | 说明                                                                                                                                                          |
| --------------- | --------------- |---------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `course_id`     | BIGINT UNSIGNED | **PK**, AUTO\_INCREMENT                     | 课程唯一标识                                                                                                                                                      |
| `course_name`   | VARCHAR(128)    | NOT NULL                                    | 课程名称                                                                                                                                                        |
| `course_desc`   | TEXT            | —                                           | 课程简介                                                                                                                                                        |
| `teacher_email` | VARCHAR(320)    | **FK** → `teacher.teacher_email`, NOT NULL  | 授课教师邮箱                                                                                                                                                      |
| `start_time`    | DATETIME        | NOT NULL                                    | 开课时间                                                                                                                                                        |
| `end_time`      | DATETIME        | NOT NULL                                    | 结课时间                                                                                                                                                        |
| `stuList`       | — (逻辑列)         | —                                           | **指向外部表** `{courseid}_students`：存储本课程全部学生的 `useremail` 列表                                                                                                   |
| `homeworkList`  | VARCHAR(512)    | —                                           | **指向一级文件夹路径**。该文件夹下按 `1/ 2/ 3/ …` 递增编号，每个子文件夹包含：<br>  • `homeworkRequirement` (作业要求)<br>  • `homeworkAnswer` (标准答案)<br>  • 各学生提交文件，命名规则 `{useremail}.{扩展名}` |
| `courseware`    | VARCHAR(512)    | —                                           | 课件根目录或关联表路径                                                                                                                                                 |

**备注**

* `stuList`、`homeworkList`、`courseware` 皆为**引用型字段**：

  * `stuList` 不实际存在，创建课堂是自动创建一个表格，比如创建了一个课程，course_id为"rg_1"，那么自动创建一个表格，表名叫做"rg_1_students"，依次存放学生的"useremail"。
  * `homeworkList` 类似于stuList，不实际存在，创建课堂是自动创建一个文件夹，比如创建了一个课程，course_id为"rg_1"，那么自动创建一个文件夹，文件夹叫做"rg_1"，依次存放对应作业的id号，每一次创建作业自动创建新文件夹，比如：目前已有hm1，那么会自动创建文件夹hm2，前端显示作业1，作业2（使用字段拼接）。每一个文件夹需要包含以下内容：homeworkRequirements(作业要求) homeworkAnswer(作业答案)，以及每个学生用usermail+username命名的作业(u202242223_qiaoyanbo.{文件后缀})
  * `courseware` 同理指向课件专属目录
  *  `程仕洋`需要建立下面的文件系统：data/{course_id}/homeworkList data/{course_id}/courseware data/{course_id}/homeworkList/{作业序号}
  * `李天意/李军` 需要与`程仕洋`配合，完成{courseId}_stuList这个表格的建立和维护，并为每一个学生创建一个表格{useremail}_courseList，维护这个学生参加的所有课程

### courseList
每一个学生一张表，便于拉取该学生的所有参加的课程
表的命名规范：{useremail}_courseList 举例:joeyanbo608@gmail.com_courseList

| course_id |
|-----------|
| rg_1      |
| rg_2      |


### `homework`   — 记录课程下每一次布置的作业元数据
表的命名规范：{course_id}_hw_{homework_no} 举例：rg_1_hw_1

| studentemail          | score | comment |
|-----------------------|-------|--------|
| joeyanbo608@gmail.com | 89    | 全对辣    |

---

