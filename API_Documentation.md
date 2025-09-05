
## 查看交互式文档
除本静态文档外，还可通过以下方式访问 Swagger 交互式文档：
1. 启动 Flask 应用：
   ```powershell
   & D:/post/Homework-main/Homework-main/.venv/Scripts/python.exe d:/post/Homework-main/Homework-main/app.py
   ```
2. 打开浏览器访问：`http://localhost:5000/api/docs/`
3. 支持在线测试所有接口，自动生成请求示例和参数说明

``````markdown
# 聊天系统 API 文档（v1.0）

## 目录
- [版本信息](#版本信息)
- [通用说明](#通用说明)
- [认证模块](#认证模块auth)
- [聊天模块](#聊天模块chat)
- [用户模块](#用户模块users)
- [管理员模块](#管理员模块admin)
- [附录：状态码说明](#附录状态码说明)


## 版本信息
| 项目                | 说明                                  |
|---------------------|---------------------------------------|
| 文档版本            | v1.0                                  |
| 接口基础路径        | `http://localhost:5000`               |
| 最后更新时间        | 2025-09-05                            |
| 认证方式            | JWT Token（请求头 `Authorization: Bearer <token>`） |
| 技术栈              | Flask + Flask-RESTX + SQLAlchemy      |
| 适用场景            | 前后端开发对接 / 接口测试 / 团队协作参考 |


## 通用说明

### 1.1 响应格式规范
所有接口返回统一 JSON 格式，便于前端统一解析：

#### 成功响应（状态码 200）
```json
{
  "success": true,
  "message": "操作成功的提示信息",
  "data": { ... }  // 可选，业务数据（如列表、对象）
}
```

#### 失败响应（状态码 4xx/5xx）
```json
{
  "success": false,
  "message": "操作失败的具体原因",
  "data": null
}
```


### 1.2 认证机制
| 项目                | 说明                                  |
|---------------------|---------------------------------------|
| 认证范围            | 除注册/登录/验证码接口外，所有接口均需认证 |
| Token 传递方式      | 请求头携带 `Authorization: Bearer <token>` |
| Token 有效期        | 1小时（自生成时起）                    |
| 无效 Token 处理     | 返回 401 状态码，提示 "Token无效或已过期" |
| 权限不足处理        | 返回 403 状态码，提示 "无操作权限"      |


## 认证模块（Auth）

### 2.1 用户登录
- **接口路径**：`POST /api/auth/login`
- **功能描述**：用户通过账号密码验证，获取访问系统的 Token
- **请求体（JSON）**：

| 参数名   | 类型   | 必选 | 约束条件                  | 示例值               |
|----------|--------|------|---------------------------|----------------------|
| username | string | 是   | 3-20位字符，支持字母/数字 | "test_user"          |
| password | string | 是   | 至少6位，建议包含大小写+数字 | "Test@123456"        |
| captcha  | string | 是   | 需与验证码图片结果一致    | "8+5=13"             |

- **成功响应**：
```json
{
  "success": true,
  "message": "登录成功",
  "username": "test_user",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

- **失败响应**：
  - 验证码错误：`{"success": false, "message": "验证码错误"}`
  - 账号密码错误：`{"success": false, "message": "用户名或密码错误"}`
  - 验证码过期：`{"success": false, "message": "验证码已过期，请刷新"}`


### 2.2 用户注册
- **接口路径**：`POST /api/auth/register`
- **功能描述**：新用户创建账号，用户名和邮箱需唯一
- **请求体（JSON）**：

| 参数名   | 类型   | 必选 | 约束条件                  | 示例值               |
|----------|--------|------|---------------------------|----------------------|
| username | string | 是   | 3-20位字符，未被占用      | "new_user"           |
| password | string | 是   | 至少6位，建议包含大小写+数字 | "New@654321"         |
| email    | string | 是   | 格式正确（含@），未被占用 | "user@example.com"   |
| captcha  | string | 是   | 需与注册验证码图片结果一致 | "3*6=18"             |

- **成功响应**：
```json
{
  "success": true,
  "message": "注册成功",
  "user_uuid": "a1b2c3d4-5678-90ef-ghij-klmnopqrstuv"
}
```

- **失败响应**：
  - 用户名已存在：`{"success": false, "message": "用户名已存在"}`
  - 邮箱已存在：`{"success": false, "message": "邮箱已存在"}`
  - 密码格式错误：`{"success": false, "message": "密码长度不能少于6位"}`


### 2.3 获取登录验证码
- **接口路径**：`GET /api/auth/login/captcha`
- **功能描述**：获取登录页面的验证码图片（数学计算型，防止机器人操作）
- **请求参数**：无
- **响应类型**：PNG 图片流（前端可直接用 `<img>` 标签渲染）
- **有效期**：5分钟（超时需重新获取）


### 2.4 获取注册验证码
- **接口路径**：`GET /api/auth/register/captcha`
- **功能描述**：获取注册页面的验证码图片（与登录验证码独立，不可混用）
- **请求参数**：无
- **响应类型**：PNG 图片流
- **有效期**：5分钟


## 聊天模块（Chat）

### 3.1 发送聊天消息（获取 AI 回复）
- **接口路径**：`POST /api/chat`
- **功能描述**：用户发送提问内容，获取 AI 回复并保存对话记录
- **权限要求**：已登录用户
- **请求头**：`Authorization: Bearer <token>`
- **请求体（JSON）**：

| 参数名   | 类型   | 必选 | 约束条件                  | 示例值               |
|----------|--------|------|---------------------------|----------------------|
| text     | string | 是   | 非空，长度≤1000字         | "如何实现分页查询？" |
| topic_id | string | 否   | UUID格式（新对话可不传）  | "3a07998d-757f-49a6-98d6-77e4b5b33d96" |

- **成功响应**：
```json
{
  "success": true,
  "reply": "实现分页查询需先获取总数据量，再通过 LIMIT 和 OFFSET 关键字控制查询范围...",
  "topic_id": "3a07998d-757f-49a6-98d6-77e4b5b33d96"
}
```

- **失败响应**：
  - 内容为空：`{"success": false, "message": "提问内容不能为空"}`
  - 系统错误：`{"success": false, "message": "服务器处理失败，请稍后重试"}`


### 3.2 分页查询聊天历史（主题列表）
- **接口路径**：`GET /api/chat/history`
- **功能描述**：分页查询用户的所有聊天主题（每个主题展示首条对话预览）
- **权限要求**：已登录用户
- **请求头**：`Authorization: Bearer <token>`
- **请求参数（Query）**：

| 参数名 | 类型 | 必选 | 约束条件        | 默认值 | 说明                 |
|--------|------|------|-----------------|--------|----------------------|
| page   | int  | 否   | ≥1              | 1      | 页码（从1开始）      |
| size   | int  | 否   | 1≤size≤50       | 10     | 每页展示的主题数量   |

- **成功响应**：
```json
{
  "success": true,
  "message": "分页查询成功",
  "data": {
    "history": [
      {
        "topic_id": "3a07998d-757f-49a6-98d6-77e4b5b33d96",
        "first_chat_time": "2025-09-05 15:16:38",
        "user_question": {"role": "user", "content": "如何实现分页查询？"},
        "assistant_reply": {"role": "assistant", "content": "实现分页查询需先获取总数据量..."}
      }
    ],
    "pagination": {
      "total_items": 3,    // 总主题数量
      "total_pages": 1,    // 总页数
      "current_page": 1,   // 当前页码
      "page_size": 10      // 每页条数
    }
  }
}
```

- **无数据响应**：
```json
{
  "success": true,
  "message": "暂无聊天历史",
  "data": {
    "history": [],
    "pagination": {
      "total_items": 0,
      "total_pages": 0,
      "current_page": 1,
      "page_size": 10
    }
  }
}
```


### 3.3 查询特定主题的完整聊天记录
- **接口路径**：`POST /api/chat/specific_history`
- **功能描述**：查询某个聊天主题下的所有对话内容（按时间顺序排列）
- **权限要求**：已登录用户（仅能查询自己的主题）
- **请求头**：`Authorization: Bearer <token>`
- **请求体（JSON）**：

| 参数名   | 类型   | 必选 | 约束条件                  | 示例值               |
|----------|--------|------|---------------------------|----------------------|
| topic_id | string | 是   | 必须是当前用户的有效主题ID | "3a07998d-757f-49a6-98d6-77e4b5b33d96" |

- **成功响应**：
```json
{
  "reply": [
    {"role": "user", "content": "如何实现分页查询？"},
    {"role": "assistant", "content": "实现分页查询需先获取总数据量..."},
    {"role": "user", "content": "SQL语句怎么写？"},
    {"role": "assistant", "content": "SELECT * FROM table LIMIT 10 OFFSET 0..."}
  ]
}
```

- **失败响应**：
  - 主题不存在：`{"success": false, "message": "未找到该聊天主题"}`
  - 无权限：`{"success": false, "message": "无权访问该聊天主题"}`


### 3.4 删除指定聊天主题
- **接口路径**：`DELETE /api/chat/<id>`（`<id>` 为 `topic_id`）
- **功能描述**：删除指定聊天主题下的所有对话记录（不可恢复）
- **权限要求**：已登录用户（仅能删除自己的主题）
- **请求头**：`Authorization: Bearer <token>`
- **路径参数**：

| 参数名 | 类型   | 约束条件                  | 示例值               |
|--------|--------|---------------------------|----------------------|
| id     | string | 必须是当前用户的有效主题ID | "3a07998d-757f-49a6-98d6-77e4b5b33d96" |

- **成功响应**：
```json
{
  "success": true,
  "message": "成功删除 2 条聊天记录",
  "deleted_topic_id": "3a07998d-757f-49a6-98d6-77e4b5b33d96"
}
```

- **失败响应**：
  - 主题不存在：`{"success": false, "message": "聊天记录不存在或不属于当前用户"}`


### 3.5 开启新聊天主题
- **接口路径**：`POST /api/chat/update_chat`
- **功能描述**：创建新的聊天主题（生成新 `topic_id`，清空上下文）
- **权限要求**：已登录用户
- **请求头**：`Authorization: Bearer <token>`
- **请求体（JSON）**：

| 参数名 | 类型 | 必选 | 说明           | 示例值 |
|--------|------|------|----------------|--------|
| new    | bool | 是   | 固定传 true    | true   |

- **成功响应**：
```json
{
  "success": true,
  "message": "新话题已开始",
  "topic_id": "new-topic-id-123456",
  "chat_history": [{"role": "system", "content": "You are a helpful assistant"}]
}
```


## 用户模块（Users）

### 4.1 获取当前用户信息
- **接口路径**：`POST /api/users/me`
- **功能描述**：查询当前登录用户的基本信息
- **权限要求**：已登录用户
- **请求头**：`Authorization: Bearer <token>`
- **请求参数**：无

- **成功响应**：
```json
{
  "success": true,
  "message": "用户信息查询成功",
  "data": {
    "user_id": "a123-4567-bcde-8901-abcdef123456",
    "username": "test_user",
    "email": "test@example.com"
  }
}
```

- **失败响应**：
  - 用户不存在：`{"success": false, "message": "用户不存在（可能已被删除）"}`


## 管理员模块（Admin）

### 5.1 管理员登录
- **接口路径**：`POST /api/admin/login`
- **功能描述**：管理员账号登录，获取管理员权限 Token
- **请求体（JSON）**：

| 参数名     | 类型   | 必选 | 说明           | 示例值        |
|------------|--------|------|----------------|---------------|
| admin_name | string | 是   | 管理员用户名   | "admin_root"  |
| password   | string | 是   | 管理员密码     | "Admin@123456"|

- **成功响应**：
```json
{
  "success": true,
  "message": "管理员登录成功",
  "admin_name": "admin_root",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

- **失败响应**：
  - 账号密码错误：`{"success": false, "message": "管理员名或密码错误"}`


### 5.2 创建新管理员
- **接口路径**：`POST /api/admin/creat_info/admin`
- **功能描述**：创建新的管理员账号（仅超级管理员可操作）
- **权限要求**：已登录的管理员
- **请求头**：`Authorization: Bearer <admin_token>`
- **请求体（JSON）**：

| 参数名     | 类型   | 必选 | 约束条件        | 示例值        |
|------------|--------|------|-----------------|---------------|
| admin_name | string | 是   | 3-20位，未被占用 | "admin_new"   |
| password   | string | 是   | 至少6位         | "NewAdmin@123"|

- **成功响应**：
```json
{
  "success": true,
  "message": "管理员注册成功",
  "admin_name": "admin_new"
}
```

- **失败响应**：
  - 权限不足：`{"success": false, "message": "无创建管理员权限"}`
  - 用户名已存在：`{"success": false, "message": "管理员名已存在"}`


### 5.3 获取管理员信息
- **接口路径**：`POST /api/admin/get_info/admin`
- **功能描述**：查询当前登录管理员的基本信息
- **权限要求**：已登录的管理员
- **请求头**：`Authorization: Bearer <admin_token>`
- **请求参数**：无

- **成功响应**：
```json
{
  "success": true,
  "message": "查询成功",
  "Admin_name": "admin_root"
}
```


## 附录：状态码说明
| 状态码 | 说明                          | 典型场景                          |
|--------|-------------------------------|-----------------------------------|
| 200    | 请求成功                      | 登录成功 / 数据查询成功           |
| 400    | 请求参数错误                  | 验证码错误 / 缺少必填参数         |
| 401    | 未认证或Token无效             | 未携带Token / Token过期          |
| 403    | 权限不足                      | 普通用户访问管理员接口            |
| 404    | 资源不存在                    | 查询不存在的聊天主题              |
| 500    | 服务器内部错误                | 数据库连接失败 / 代码异常         |

