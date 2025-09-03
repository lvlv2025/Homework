# Flask AI 聊天系统 API 文档

## 目录

- [用户接口](#用户接口)
- [聊天接口](#聊天接口)
- [管理员接口](#管理员接口)

---

## 用户接口

### 获取登录验证码

**URL:** `/api/login/captcha`  
**方法:** `GET`  
**描述:** 获取用户登录验证码（数学题形式），返回图片。

**返回:** Content-Type: `image/png`

---

### 用户注册验证码

**URL:** `/api/register/captcha`  
**方法:** `GET`  
**描述:** 获取用户注册验证码（数学题形式），返回图片。

**返回:** Content-Type: `image/png`

---

### 用户注册

**URL:** `/api/register`  
**方法:** `POST`  
**参数（JSON）:**

| 字段       | 类型     | 必填  | 说明    |
| -------- | ------ | --- | ----- |
| username | string | 是   | 用户名   |
| password | string | 是   | 密码    |
| email    | string | 是   | 邮箱    |
| captcha  | string | 是   | 验证码文本 |

**返回（成功）:**

```json
{
  "success": true,
  "message": "注册成功",
  "user_uuid": "12345678901"
}
```

---

### 用户登录

**URL:** `/api/login`  
**方法:** `POST`  
**参数（JSON）:**

| 字段       | 类型      | 必填  | 说明     |
| -------- | ------- | --- | ------ |
| username | string  | 是   | 用户名    |
| password | string  | 是   | 密码     |
| captcha  | string  | 是   | 验证码文本  |
| remember | boolean | 否   | 是否记住登录 |

**返回（成功）:**

```json
{
  "success": true,
  "message": "登录成功",
  "username": "user1"
}
```

---

### 用户登出

**URL:** `/api/logout`  
**方法:** `POST`  
**描述:** 清除用户登录状态。

**返回示例:**

```json
{
  "success": true,
  "message": "登出成功",
  "uuid": "12345678901"
}
```

---

### 获取用户信息

**URL:** `/api/get_info/user`  
**方法:** `POST`  
**描述:** 查询当前登录用户信息

**返回（成功）:**

```json
{
  "success": true,
  "message": "用户信息查询成功",
  "data": {
    "user_id": "12345678901",
    "username": "user1",
    "email": "user1@example.com"
  }
}
```

---

## 聊天接口

### 获取聊天回复

**URL:** `/api/chat/get_response`  
**方法:** `POST`  
**参数（JSON）:**

| 字段       | 类型     | 必填  | 说明               |
| -------- | ------ | --- | ---------------- |
| text     | string | 是   | 用户发送消息           |
| topic_id | string | 否   | 聊天主题 ID，不传则创建新主题 |

**返回示例:**

```json
{
  "success": true,
  "reply": "AI 回复内容",
  "topic_id": "uuid"
}
```

---

### 开启新话题

**URL:** `/api/chat/update_chat`  
**方法:** `POST`  
**参数（JSON）:**

| 字段  | 类型      | 必填  | 说明      |
| --- | ------- | --- | ------- |
| new | boolean | 是   | 是否开启新话题 |

**返回示例:**

```json
{
  "success": true,
  "message": "新话题已开始",
  "topic_id": "uuid",
  "chat_history": [
    {"role": "system", "content": "You are a helpful assistant"}
  ]
}
```

---

### 获取历史聊天记录

**URL:** `/api/chat/history_response`  
**方法:** `POST`  
**参数（JSON）:**

| 字段        | 类型     | 必填  | 说明      |
| --------- | ------ | --- | ------- |
| user_uuid | string | 是   | 用户 UUID |
| topic_id  | string | 是   | 聊天主题 ID |

**返回示例:**

```json
{
  "reply": [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好，我是 AI"}
  ]
}
```

---

## 管理员接口

### 管理员登录

**URL:** `/api/login/admin`  
**方法:** `POST`  
**参数（JSON）:**

| 字段         | 类型     | 必填  | 说明     |
| ---------- | ------ | --- | ------ |
| Admin_name | string | 是   | 管理员用户名 |
| password   | string | 是   | 密码     |

**返回示例:**

```json
{
  "success": true,
  "message": "管理员登录成功",
  "admin_name": "admin1"
}
```

---

### 创建管理员

**URL:** `/api/creat_info/admin`  
**方法:** `POST`  
**参数（JSON）:**

| 字段       | 类型     | 必填  | 说明     |
| -------- | ------ | --- | ------ |
| username | string | 是   | 管理员用户名 |
| password | string | 是   | 密码     |

**返回示例:**

```json
{
  "success": true,
  "message": "管理员注册成功",
  "admin_name": "admin2"
}
```

---

### 获取管理员信息

**URL:** `/api/get_info/admin`  
**方法:** `POST`  
**参数（JSON）:**

| 字段         | 类型     | 必填  | 说明     |
| ---------- | ------ | --- | ------ |
| Admin_name | string | 是   | 管理员用户名 |

**返回示例:**

```json
{
  "success": true,
  "message": "查询成功",
  "Admin_name": "admin1"
}
```

---

## 错误返回示例

- **未登录或权限不足:** HTTP `401`  
- **参数缺失:** HTTP `400`  
- **查询失败/服务器错误:** HTTP `500`  

## 备注

- 所有接口均使用 JSON 数据交互。  
- 用户登录状态通过 session 管理，支持 remember 延长 session 有效期。  
- 所有聊天记录均保存在数据库 ChatHistory 表。  
- 日志记录在 logs/app.log，方便调试接口调用和异常信息。
