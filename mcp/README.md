以下文档为 **MCP (Model Compute/Control Platform) API 规范 v1**，供负责协议对接的同学实现。
---

## 0 . 通用约定

| 项目              | 说明                                                                                     |
|-------------------|------------------------------------------------------------------------------------------|
| 基础 URL          | `https://<mcp_host>/api/v1`                                                              |
| 认证方式          | 在 **HTTP Header** 里携带 `Authorization: Bearer <jwt_token>`                            |
| 成功响应 HTTP 码  | `200 OK`（除非特别约定为异步 202）                                                       |
| 通用返回结构      | ```json\n{ \"code\": 0, \"message\": \"ok\", \"data\": { … } }\n```                      |
| 错误码示例        | `40001`(参数缺失) `40002`(鉴权失败) `50001`(内部异常)… —— 见附件《错误码字典.md》         |
| 时间字段          | 全部使用 **ISO-8601**，示例 `2025-04-28T14:23:00Z`                                       |
| 版本升级策略      | 新增字段保持向后兼容；破坏性变更请提升路径版本 `/api/v2/...`                              |

---

## 1 . 对话接口（Chat）

### 1.1 发起 / 续写对话  
> **POST `/chat/completions`**

| 字段            | 类型            | 必填 | 说明                                                                                           |
|-----------------|-----------------|------|------------------------------------------------------------------------------------------------|
| `model`         | string          | Y    | 模型代号，如 `gpt-4o`                                                                          |
| `messages`      | array\<object\> | Y    | 聊天上下文，同 OpenAI 格式。元素包含 `role`(`system|user|assistant`)、`content` 两字段           |
| `conversation_id` | string        | N    | 不传表示新建会话；传则续写历史（MCP 负责持久化）                                               |
| `temperature`   | number          | N    | 0 ~ 2，默认 1                                                                                  |
| `stream`        | boolean         | N    | 是否流式返回；默认 false                                                                       |

#### 返回（`stream=false`）  
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "conversation_id": "8f83…",
    "choices": [
      {
        "index": 0,
        "message": { "role": "assistant", "content": "…回复文本…" },
        "finish_reason": "stop"
      }
    ],
    "usage": { "prompt_tokens": 123, "completion_tokens": 456, "total_tokens": 579 }
  }
}
```

> **聊天记录本地化**  
> MCP 需把完整往返消息 JSON 追加到 `<storage_root>/chat/{conversation_id}.jsonl`，格式与 [gpt_academic](https://github.com/binary-husky/gpt_academic) 保持一致，便于前端直接回放。

---

### 1.2 获取会话历史  
> **GET `/chat/history/{conversation_id}`**

| 查询串参数 | 类型 | 必填 | 说明                                    |
|------------|------|------|-----------------------------------------|
| `limit`    | int  | N    | 返回最近 N 条（缺省 50，最大 500）      |

**返回**：`data.messages` 为按时间升序的 `messages` 数组。  

---

## 2 . RAG 知识库接口（文件→向量库）

### 2.1 创建知识库并上传文档  
> **POST `/rag/collections`** *（`multipart/form-data`）*

| Part/Field        | 类型                 | 必填 | 说明                                                      |
|-------------------|----------------------|------|-----------------------------------------------------------|
| `name`            | string               | Y    | 集合名称（同教师作业标题）                                |
| `description`     | string               | N    | 备注                                                      |
| `files`           | file[]               | Y    | 支持 `.pdf .docx .md .txt` 等（≤ 50 MB / 单文件）         |
| `embedding_model` | string               | N    | 不传用系统默认                                           |

> **同步模式**：文件量 ≤ 20 MB 时直接返回。  
> **异步模式**：更大文件返回 `202 Accepted`，`Location: /tasks/{task_id}`。

**成功返回（同步）**

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "collection_id": "cls_abc123",
    "file_count": 3,
    "token_usage": 9876
  }
}
```

### 2.2 向知识库提问  
> **POST `/rag/query`**

| 字段               | 类型   | 必填 | 说明                                               |
|--------------------|--------|------|----------------------------------------------------|
| `collection_id`    | string | Y    | 上一步返回                                         |
| `question`         | string | Y    | 用户自然语言问题                                   |
| `student_answer`   | string | N    | （可选）学生原答案，辅助错因分析                    |
| `top_k`            | int    | N    | 返回检索证据条数；默认 3，最大 10                  |

**返回**

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "answer": "…大模型综合解析…",
    "evidence": [
      { "doc_id": "doc1", "page": 4, "snippet": "…" },
      { "doc_id": "doc2", "page": 1, "snippet": "…" }
    ],
    "usage": { "prompt_tokens": 321, "completion_tokens": 210 }
  }
}
```

---

## 3 . 批量 AI 批改接口（可选增强）

> **POST `/grader/batch`**

| 字段               | 类型            | 必填 | 说明                                                                 |
|--------------------|-----------------|------|----------------------------------------------------------------------|
| `collection_id`    | string          | Y    | 参考答案所在 RAG 集合                                                |
| `grading_rubric`   | string          | Y    | 评分细则（markdown）                                                 |
| `submissions`      | array\<object\> | Y    | 每项：`{ "student_id": "2025xxxx", "answer": "…" }`                  |
| `async`            | boolean         | N    | `true` 则返回 `202` 并异步处理（推荐），`false` 阻塞直至全部完成      |

**异步返回** `202 Accepted`

```json
{
  "code": 0,
  "message": "submitted",
  "data": { "task_id": "task_xyz789" }
}
```

结果结构（同步 or 查询任务完毕后取得）

```json
{
  "student_id": "2025xxxx",
  "score": 87,
  "feedback": {
    "strength": [ "要点 A 阐述清晰", "格式规范" ],
    "weakness": [ "忽略步骤 B", "计算误差" ],
    "suggestion": "复习定积分章节第 3 节……"
  }
}
```

---

## 4 . 任务查询接口（长任务 / 异步统一入口）

> **GET `/tasks/{task_id}`**

| 字段          | 类型   | 说明                                   |
|---------------|--------|----------------------------------------|
| `status`      | string | `pending | running | succeeded | failed` |
| `progress`    | int    | 百分比 0-100                           |
| `result`      | any    | 任务完成后与同步返回格式一致           |

---

## 5 . WebSocket 回调（选做，提升实时体验）

*路径* `wss://<mcp_host>/ws/stream`  
握手时以 `Sec-WebSocket-Protocol: bearer,<jwt_token>` 鉴权。  
服务器主动推送：

```json
{ "event": "task_update", "task_id": "task_xyz789", "status": "running", "progress": 42 }
```

---

## 6 . 最佳实践与安全

1. **资源隔离**：同一 `collection_id` 仅对其创建者（教师）及授权学生可见。  
2. **数据留存期**：聊天记录与向量索引默认保存 90 天，可由管理员策略调整。 （不用管，压根用不着这么久）
3. **个人隐私脱敏**：MCP 在调用第三方大模型前，应移除姓名、学号等个人标识。  
4. **速率限制**：建议全局 `10 req/s` + 每用户 `60 req/min`，触发时返回 HTTP `429`。  （gpt瞎bb的，不用管）

---

### 附件

- 压根没有