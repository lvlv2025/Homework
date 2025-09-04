
# Flask Chat & User Management API

## 项目概述
该项目是一个基于 Flask 的聊天与用户管理系统，功能包括：

- 用户注册、登录（支持验证码验证）
- JWT 验证及权限控制（用户/管理员）
- 聊天记录存储与查询
- 管理员信息管理
- 日志记录和调试支持

## 项目结构

```text
project/
│
├─ app.py                 # Flask 主应用入口
├─ config.yaml            # 数据库和应用配置
├─ db_model.py            # SQLAlchemy 数据库模型定义
├─ jwt_setting.py         # JWT 生成与验证
├─ creat_id.py            # 用户 UUID 与 topic_id 生成
├─ ai_chat.py             # AI 聊天接口
├─ captcha.py             # 验证码生成
├─ logs/                  # 日志目录
└─ requirements.txt       # Python 依赖
```

## 配置文件 `config.yaml`

```yaml
database:
  type: mysql
  host: localhost
  port: 3306
  user: root
  password: 123456
  database_name: chat_db
  charset: utf8mb4
```

## 主要依赖

```text
Flask
Flask-CORS
SQLAlchemy
PyJWT
Werkzeug
Pillow
PyYAML
```

## 主要功能接口

### 1. 用户注册

**接口**: `POST /api/auth/register`

**请求示例**:

```json
{
  "username": "user1",
  "password": "123456",
  "email": "user1@example.com",
  "captcha": "1234"
}
```

**返回示例**:

```json
{
  "success": true,
  "message": "注册成功",
  "user_uuid": "uuid"
}
```

### 2. 用户登录

**接口**: `POST /api/auth/login`

**请求示例**:

```json
{
  "username": "user1",
  "password": "123456",
  "captcha": "1234"
}
```

**返回示例**:

```json
{
  "success": true,
  "message": "登录成功",
  "username": "user1",
  "token": "JWT_TOKEN"
}
```

### 3. 获取登录验证码

**接口**: `GET /api/login/captcha`

**返回**: PNG 图片验证码

### 4. 聊天接口

**接口**: `POST /api/chat/`

**请求示例**:

```json
{
  "question": "你好",
  "topic_id": null
}
```

**返回示例**:

```json
{
  "success": true,
  "reply": "你好，我是你的助手",
  "topic_id": "topic_uuid"
}
```

### 5. 开启新话题

**接口**: `POST /api/chat/update_chat`

**请求示例**:

```json
{
  "new": true
}
```

**返回示例**:

```json
{
  "success": true,
  "message": "新话题已开始",
  "topic_id": "new_topic_id",
  "chat_history": [
    {"role": "system", "content": "You are a helpful assistant"}
  ]
}
```

### 6. 查询历史聊天

**接口**: `GET /api/chat/history`

**返回示例**:

```json
{
  "history": [
    {
      "topic_id": "topic_uuid",
      "user_question": {"role": "user", "content": "你好"},
      "assistant_reply": {"role": "assistant", "content": "你好，我是你的助手"}
    }
  ]
}
```

### 7. 查询指定聊天

**接口**: `POST /api/chat/specific_history`

**请求示例**:

```json
{
  "topic_id": "topic_uuid"
}
```

**返回示例**:

```json
{
  "reply": [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好，我是你的助手"}
  ]
}
```

### 8. 查询当前用户信息

**接口**: `POST /api/users/me`

**返回示例**:

```json
{
  "success": true,
  "message": "用户信息查询成功",
  "data": {
    "user_id": "user_uuid",
    "username": "user1",
    "email": "user1@example.com"
  }
}
```

### 9. 管理员登录

**接口**: `POST /api/login/admin`

**返回示例**:

```json
{
  "success": true,
  "message": "管理员登录成功",
  "admin_name": "admin",
  "token": "JWT_TOKEN"
}
```

### 10. 创建管理员

**接口**: `POST /api/creat_info/admin`

**返回示例**:

```json
{
  "success": true,
  "message": "管理员注册成功",
  "admin_name": "admin"
}
```

### 11. 查询管理员信息

**接口**: `POST /api/get_info/admin`

**返回示例**:

```json
{
  "success": true,
  "message": "查询成功",
  "Admin_name": "admin"
}
```

## 日志管理

- 日志存放在 `logs/app.log`
- 最大 5MB，保留 5 个备份
- 控制台与文件同时输出调试信息

## 启动应用

```bash
python app.py
```

- 运行在 `0.0.0.0:5000`
- 调试模式开启
- 启动时会打印所有注册路由
