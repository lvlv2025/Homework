# 📌 API 接口文档

## 用户认证模块

### 1. 登录

**接口地址：** `/api/login`  
**请求方法：** `POST`  
**请求参数（JSON）：**
| 字段名       | 类型    | 是否必填 | 说明               |
| username    | string | 必填  | 用户名             |
| password    | string | 必填| 密码（明文，后端校验）|
| captcha     | string | 必填| 验证码              |
| remember    | bool   | 非必填 | 是否保持登录（默认 false） |

**返回示例：**

```json
// 成功
{
  "success": true,
  "message": "登录成功",
  "username": "test_user"
}

// 失败
{
  "success": false,
  "message": "用户名或密码错误"
}
```

---

### 2. 注册

**接口地址：** `/api/register`  
**请求方法：** `POST`  
**请求参数（JSON）：**
| 字段名       | 类型    | 是否必填 | 说明           |
| username    | string | 必填 | 用户名         |
| password    | string | 必填 | 密码           |
| email       | string | 必填  | 邮箱           |
| captcha     | string | 必填  | 验证码         |

**返回示例：**

```json
// 成功
{
  "success": true,
  "message": "注册成功",
  "user_uuid": "12345678901"
}

// 失败
{
  "success": false,
  "message": "验证码错误"
}
```

---

### 3. 获取登录验证码

**接口地址：** `/api/login/captcha`
**请求方法：** `GET`
**返回：** 验证码 PNG 图片（`image/png`）

---

### 4. 获取注册验证码

**接口地址：** `/api/register/captcha`
**请求方法：** `GET`
**返回：** 验证码 PNG 图片（`image/png`）

---

### 5. 退出登录

**接口地址：** `/api/logout`
**请求方法：** `GET`
**返回：** 清除 session，返回登出的用户的UUID
**返回示例：**

```json
// 成功
{
  "success": true,
  "message": "登出成功",
  "user_uuid": "12345678901"
}

// 失败
{
  "success": false,
  "message": "登出失败"
}
```

---

## 聊天模块

### 6. 获取 AI 回复

**接口地址：** `/api/chat/get_response`  
**请求方法：** `POST`  
**需要登录：** 必需  

**请求参数（JSON）：**
| 字段名    | 类型   | 必填 | 说明                    |
| text     | string| 必填   | 用户发送的消息           |
| topic_id | string| 第一次不用   | 会话 ID（首次不传则后端生成） |

**返回示例：**

```json
{
  "success": true,
  "reply": "这是AI的回答",
  "topic_id": "12345678"
}
```

---

### 7. 开启新话题

**接口地址：** `/api/chat/update_chat`  
**请求方法：** `POST`  
**需要登录：** 必需  

**请求参数（JSON）：**
| 字段名 | 类型 | 必填 | 说明         |
| new   | bool | 必填   | 是否开启新话题 |

**返回示例：**

```json
{
  "success": true,
  "message": "新话题已开始",
  "topic_id": "98765432"
}
```

---

### 8. 获取历史对话 + 回复

**接口地址：** `/api/chat/history_response`  
**请求方法：** `POST`  
**需要登录：** 必需  

**请求参数（JSON）：**
| 字段名 | 类型   | 必填 | 说明       |
| text  | string | 必填   | 用户输入消息 |
| topic_id  | string | 必填   | 用户历史对话的记录 |

**返回示例：**

```json
{
  "reply": [
    {
      "role": "user",
      "content": "你好"
    },
    {
      "role": "assistant",
      "content": "你好，有什么可以帮你？"
    },
    {
      "role": "user",
      "content": "帮我写一个Python函数"
    },
    {
      "role": "assistant",
      "content": "好的，请问需要实现什么功能？"
    }
  ]
}
```

## 管理员认证模块

### 9.管理员登录

**接口地址：** `/api/login/admin`  
**请求方法：** `POST`  
**需要登录：** 不必需

**请求参数（JSON）：** | 字段名 | 类型 | 必填 | 说明 |
| text | string | 必填 | 用户输入消息 |
| topic_id | string | 必填 | 用户历史对话的记录 |



## 错误码说明

| 状态码 | 含义             |
| --- | -------------- |
| 200 | 请求成功           |
| 400 | 请求参数错误（如验证码错误） |
| 401 | 未登录 / 登录失败     |
| 500 | 服务器内部错误        |
