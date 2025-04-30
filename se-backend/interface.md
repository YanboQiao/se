## 1. 上传文件（Upload File）

| 项目 | 说明                   |
| ---- |----------------------|
| **接口名称** | `UploadFile`         |
| **请求方法** | `POST`               |
| **URL** | `/api/v1/uploadfile` |
| **请求类型** | `multipart/form-data` |


### 1.1 请求体（multipart）

| Part 名称      | 类型 | 必填 | 说明                                                                     |
|--------------|------|------|------------------------------------------------------------------------|
| `file`       | `binary` | 是 | 待上传的文件（二进制流）。支持 `.docx`、`.pdf`、`.zip`、`.png` 等。最大 20 MB（示例，实际限制视部署而定）。 |
| `fileType`   | `string` | 是 | 文件业务类型。暂定1对应作业 2对应答案 3对应其他附件。                                          |
| `userId`     | `string` | 是 | 记录上传者的用户名（唯一标识号），然后存储到对应的文件夹                                           |
| `uploaderId` | `string` | 是 | 当前登录用户 ID（后端亦可从 Token 中解析）。                                            |
| `userGroup`  | `number` | 是 | 用户组标识：<br>- `1`: 学生(student)<br>- `2`: 教师(teacher)                     |
| `uploadTime` | `string` | 是 | 上传时间，采用毫秒时间戳。                                                          |


### 1.2 成功响应体（HTTP 200）

```jsonc
{
    "code": 0,
    "message": "Upload success",
    "data": {
        "fileId": "f_4d5f41b2b8",
        "fileName": "homework1.pdf",
        "fileUrl": "https://cdn.example.com/f_4d5f41b2b8",
        "contentType": "application/pdf",
        "size": 1532478,
        "uploadedAt": "2025-05-12T14:23:45Z"
    }
}
```

### 1.3 失败响应体（示例）

```jsonc
{
  "code": 41301,
  "message": "File too large (max 20 MB)",
  "data": null
}
```

---

## 2. 获取文件下载链接（Get File URL）

| 项目 | 说明 |
| ---- | ---- |
| **接口名称** | `GetFileUrl` |
| **请求方法** | `GET` |
| **URL** | `/api/v1/files/{fileId}` |
| **URL 参数** | `fileId`：上传后返回的文件唯一标识 |

### 2.1 请求参数

| 参数 | 类型 | 必填 | 位置 | 说明 |
|------|------|------|------|------|
| `fileId` | `string` | 是 | path | 文件唯一标识 |
| `userId` | `string` | 是 | query | 请求用户ID |
| `userGroup` | `number` | 是 | query | 用户组标识：<br>- `1`: 学生(student)<br>- `2`: 教师(teacher) |
| `requestTime` | `string` | 否 | query | 请求时间戳（毫秒），用于防止重放攻击 |

### 2.2 成功响应体（HTTP 200）

```jsonc
{
  "code": 0,
  "message": "OK",
  "data": {
    "fileId": "f_4d5f41b2b8",
    "fileName": "homework1.pdf",
    "downloadUrl": "https://cdn.example.com/f_4d5f41b2b8?token=abc123&exp=1715550000",
    "expireAt": "2025-05-12T15:23:45Z"
  }
}
```

> *说明*：  
> - 默认返回 **带时效的签名 URL**（如 S3 Presigned URL），前端直接下载即可。  
> - 若需直接流式返回文件，可在请求头加 `Accept: application/octet-stream`，后端按需实现。

---

## 3. 删除文件（Delete File）

| 项目 | 说明 |
| ---- | ---- |
| **接口名称** | `DeleteFile` |
| **请求方法** | `DELETE` |
| **URL** | `/api/v1/files/{fileId}` |

### 3.1 成功响应体（HTTP 200）

```jsonc
{
  "code": 0,
  "message": "File deleted",
  "data": {
    "fileId": "f_4d5f41b2b8",
    "deleted": true
  }
}
```

> *权限*：仅文件上传者本人、对应课程教师或管理员可删除。AI 批改完成且教师已确认后的学生作业附件 **不可删除**，后端需做校验。

---



### 统一字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | `int` | 业务状态码；`0` 表示成功，其余为错误码。 |
| `message` | `string` | 对应业务描述信息。 |
| `data` | `object/array/null` | 实际返回数据体。 |
| `fileId` | `string` | 文件唯一标识（UUID 或数据库主键）。 |
| `fileName` | `string` | 原始文件名。 |
| `fileUrl / downloadUrl` | `string` | 文件访问地址；当使用下载接口时通常为带时效签名的 URL。 |
| `contentType` | `string` | 文件 MIME 类型。 |
| `size` | `number` | 文件大小（字节）。 |
| `uploadedAt` | `string` | 上传时间（ISO-8601）。 |
| `expireAt` | `string` | 下载链接过期时间（若返回）。 |


---

## 4. 教师获取自己开设的课程清单（Teacher Get Course List）

| 项目 | 说明 |
| ---- | ---- |
| **接口名称** | `TeacherGetCourseList` |
| **请求方法** | `GET` |
| **URL** | `/api/v1/teacher/courses` |

### 4.1 请求参数

| 参数 | 类型 | 必填 | 位置 | 说明 |
|------|------|------|------|------|
| `teacherId` | `string` | 是 | query | 教师 **本人** ID（可由后端依据 Token 冗余校验） |
| `semester` | `string` | 否 | query | 学期标识，如 `2025-spring`；为空返回全部 |
| `pageSize` | `number` | 否 | query | 每页条数，默认 `20` |
| `pageNum` | `number` | 否 | query | 页码，默认 `1` |

### 4.2 成功响应体（HTTP 200）

```jsonc
{
  "code": 0,
  "message": "OK",
  "data": {
    "total": 10,
    "pageSize": 10,
    "pageNum": 1,
    "courses": [
      {
        "courseId": "course_1234",
        "courseName": "软件工程",
        "courseCode": "SE2025",
        "semester": "2025-spring",
        "studentCount": 86,
        "coverUrl": "https://cdn.example.com/courses/se2025.jpg"
      }
      // ...
    ]
  }
}
```

> **权限控制**：后端需确认 `teacherId` 与登录态匹配，且用户角色为教师。  
> **业务语义**：仅返回该教师“主讲”或“协同授课”的课程，不含助教身份课程。

---

## 5. 学生获取自己已选课程清单（Student Get Course List）

| 项目 | 说明 |
| ---- | ---- |
| **接口名称** | `StudentGetCourseList` |
| **请求方法** | `GET` |
| **URL** | `/api/v1/student/courses` |

### 5.1 请求参数

| 参数 | 类型 | 必填 | 位置 | 说明 |
|------|------|------|------|------|
| `studentId` | `string` | 是 | query | 学生 **本人** ID（后端同样可通过 Token 校验） |
| `semester` | `string` | 否 | query | 学期标识，如 `2025-spring`；为空返回全部 |
| `pageSize` | `number` | 否 | query | 每页条数，默认 `20` |
| `pageNum` | `number` | 否 | query | 页码，默认 `1` |

### 5.2 成功响应体（HTTP 200）

```jsonc
{
  "code": 0,
  "message": "OK",
  "data": {
    "total": 8,
    "pageSize": 8,
    "pageNum": 1,
    "courses": [
      {
        "courseId": "course_5678",
        "courseName": "操作系统原理",
        "courseCode": "OS2025",
        "semester": "2025-spring",
        "teacherName": "张三",
        "coverUrl": "https://cdn.example.com/courses/os2025.jpg",
        "progress": 0.45   // 已完成进度，可选
      }
      // ...
    ]
  }
}
```

> **权限控制**：后端需验证 `studentId` 与登录态匹配且角色为学生。  
> **业务语义**：只返回学生已成功选课且未退选的课程；可选字段 `progress` 显示学习进度百分比。

#### 备注

1. **权限控制**：后端基于 JWT 或 Session 区分学生/教师角色，所有文件操作均需校验用户是否有权访问 `relatedId`。 数据库需要记录每一个文件的可访问人员。
2. **文件存储**：建议每一个用户创建一个表格（表名使用用户id），文件存储在对应用户下属的数据库的表中
