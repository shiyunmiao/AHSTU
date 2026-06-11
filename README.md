# 校园留言墙 — 技术文档

> 基于 Flask + PostgreSQL 的全栈 Web 应用  
> 部署平台：Railway | 代码仓库：[shiyunmiao/AHSTU](https://github.com/shiyunmiao/AHSTU)

---

## 目录

1. [项目概述](#1-项目概述)
2. [技术栈](#2-技术栈)
3. [项目结构](#3-项目结构)
4. [数据库设计](#4-数据库设计)
5. [核心功能实现](#5-核心功能实现)
6. [部署指南](#6-部署指南)
7. [API 接口](#7-api-接口)
8. [常见问题](#8-常见问题)

---

## 1. 项目概述

校园留言墙是一个面向在校学生的轻量级社交平台，支持留言发布、互动回复、点赞等功能。采用单体架构设计，便于快速部署和维护。

### 核心功能

- 用户注册/登录（学号认证）
- 留言发布（支持标题、正文、图片三选一）
- 嵌套回复（对回复进行回复）
- 点赞互动（AJAX 无刷新）
- 全文搜索（标题 + 正文）
- 管理员后台（置顶、删除）
- 头像上传
- 夜间模式

---

## 2. 技术栈

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 前端 | HTML5 / CSS3 / JavaScript | — | 页面结构与交互 |
| 模板引擎 | Jinja2 | 内置 | 服务端渲染 HTML |
| 后端框架 | Flask | 3.0.0 | Web 框架与路由 |
| ORM | Flask-SQLAlchemy | 3.1.1 | 数据库操作 |
| 登录管理 | Flask-Login | 0.6.3 | 用户会话 |
| 数据库驱动 | pg8000 | 1.31.2 | PostgreSQL 连接 |
| 密码加密 | Werkzeug | — | scrypt 哈希 |
| WSGI 服务器 | Gunicorn | 21.2.0 | 生产环境部署 |
| 云平台 | Railway | — | 应用托管 |
| 数据库 | PostgreSQL | — | 数据持久化 |

---

## 3. 项目结构

```
message_board/
├── app.py                  # Flask 主程序（路由 + 业务逻辑）
├── models.py               # 数据库模型定义
├── config.py               # 应用配置（数据库连接等）
├── requirements.txt        # Python 依赖清单
├── Procfile                # Railway 部署配置
├── .env.example            # 环境变量模板
├── .gitignore
├── static/
│   ├── style.css           # 全局样式表
│   └── compress.js         # 前端图片压缩脚本
├── templates/
│   ├── base.html           # 母版页（导航栏 + 夜间模式）
│   ├── index.html          # 首页（留言列表）
│   ├── publish.html        # 发布留言页
│   ├── message.html        # 留言详情 + 嵌套回复
│   ├── login.html          # 登录页
│   ├── register.html       # 注册页（含验证码）
│   ├── profile.html        # 个人信息编辑（头像）
│   ├── change_password.html # 修改密码
│   ├── user.html           # 个人主页
│   ├── search.html         # 搜索页
│   └── admin.html          # 管理后台
└── uploads/
    └── .gitkeep            # 上传目录占位
```

---

## 4. 数据库设计

### 4.1 ER 图

```
┌──────────┐       ┌────────────┐       ┌──────────┐
│  users   │──1:N──│  messages  │──1:N──│ replies  │
└──────────┘       └────────────┘       └──────────┘
     │                   │              ┌──────────┐
     │                   └──────1:N──────│  likes   │
     └──────────1:N──────────────────────┘──────────┘
```

### 4.2 表结构

#### users（用户表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 用户 ID |
| student_id | VARCHAR(20) | UNIQUE, NOT NULL | 学号 |
| username | VARCHAR(50) | UNIQUE, NOT NULL | 用户名（登录用） |
| email | VARCHAR(100) | NULLABLE | 邮箱 |
| password_hash | VARCHAR(255) | NOT NULL | 密码哈希（scrypt） |
| nickname | VARCHAR(50) | DEFAULT '' | 显示昵称 |
| avatar_url | TEXT | DEFAULT '' | 头像（支持 base64） |
| created_at | TIMESTAMP | DEFAULT NOW() | 注册时间 |
| is_admin | BOOLEAN | DEFAULT FALSE | 是否管理员 |

#### messages（留言表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 留言 ID |
| user_id | INTEGER | FK → users.id | 发布者 |
| title | VARCHAR(200) | DEFAULT '' | 标题 |
| content | TEXT | NOT NULL | 正文 |
| image_url | TEXT | DEFAULT '' | 图片（URL 或 base64） |
| created_at | TIMESTAMP | DEFAULT NOW() | 发布时间 |
| updated_at | TIMESTAMP | ON UPDATE NOW() | 更新时间 |
| is_pinned | BOOLEAN | DEFAULT FALSE | 是否置顶 |

#### replies（回复表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 回复 ID |
| message_id | INTEGER | FK → messages.id | 所属留言 |
| user_id | INTEGER | FK → users.id | 回复者 |
| parent_id | INTEGER | FK → replies.id, NULLABLE | 父回复（嵌套支持） |
| content | TEXT | NOT NULL | 回复内容 |
| created_at | TIMESTAMP | DEFAULT NOW() | 回复时间 |

#### likes（点赞表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 点赞 ID |
| user_id | INTEGER | FK → users.id | 点赞者 |
| message_id | INTEGER | FK → messages.id | 被赞留言 |
| created_at | TIMESTAMP | DEFAULT NOW() | 点赞时间 |
| — | — | UNIQUE(user_id, message_id) | 一人只能点一次 |

### 4.3 ORM 关系

```python
# models.py 中的关联定义
class User:
    messages = relationship('Message')   # 用户 → 留言
    likes = relationship('Like')         # 用户 → 点赞
    replies = relationship('Reply')      # 用户 → 回复

class Message:
    author = relationship('User')        # 留言 → 作者
    replies = relationship('Reply')      # 留言 → 回复（级联删除）
    likes = relationship('Like')         # 留言 → 点赞（级联删除）

class Reply:
    author = relationship('User')        # 回复 → 作者
    parent = relationship('Reply')       # 回复 → 父回复（自引用）
    children = relationship('Reply')     # 回复 → 子回复
```

---

## 5. 核心功能实现

### 5.1 图片存储方案

采用 **base64 编码** 将图片直接存入数据库，而非文件系统：

```
用户上传 → 前端压缩(compress.js) → 后端读取二进制 → base64编码
→ 存入 image_url 字段 → 前端 <img src="data:image/...;base64,...">
```

**优点**：不依赖服务器文件系统，部署重启不丢失  
**缺点**：增加数据库体积，单张建议不超过 500KB

### 5.2 嵌套回复

通过自引用外键实现：

```python
parent_id = db.Column(db.Integer, db.ForeignKey('replies.id'), nullable=True)
children = db.relationship('Reply', backref='parent', remote_side=[id])
```

前端渲染时，只显示顶级回复（`parent_id IS NULL`），子回复缩进展示。

### 5.3 验证码

基于 Session 的数学验证码：

```python
# 生成（GET 请求）
num1, num2 = random.randint(1, 20), random.randint(1, 10)
session['captcha_answer'] = num1 + num2

# 校验（POST 请求）
int(captcha_input) == session.get('captcha_answer')
```

### 5.4 发布防抖

前端 JavaScript 实现 5 秒冷却：

```javascript
let cooldown = false;
form.addEventListener('submit', function(e) {
    if (cooldown) { e.preventDefault(); return; }
    cooldown = true;
    btn.disabled = true;
    // 5 秒倒计时后恢复
});
```

### 5.5 点赞（AJAX）

```javascript
fetch('/like/' + messageId, { method: 'POST' })
    .then(r => r.json())
    .then(data => {
        // 更新爱心图标和计数，不刷新页面
    });
```

### 5.6 环境感知配置

```python
# 部署时自动读取 Railway 注入的环境变量
# 本地开发时自动回退到 localhost
raw_url = (
    os.environ.get('DATABASE_PUBLIC_URL')   # Railway 外部地址
    or os.environ.get('DATABASE_URL')       # Railway 内部地址
    or 'postgresql+pg8000://postgres:admin@localhost/message_board'  # 本地
)
```

---

## 6. 部署指南

### 6.1 本地开发

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 确保本地 PostgreSQL 运行，数据库名 message_board

# 3. 启动
python app.py

# 4. 访问 http://localhost:5000
```

### 6.2 Railway 部署

1. Fork / Push 代码到 GitHub
2. 登录 [Railway](https://railway.com) → New Project → Deploy from GitHub
3. 添加 PostgreSQL 数据库（自动注入环境变量）
4. 无需手动配置，`config.py` 自动读取

### 6.3 环境变量

| 变量 | 必需 | 说明 |
|------|------|------|
| `DATABASE_URL` | 部署时自动注入 | PostgreSQL 连接地址 |
| `SECRET_KEY` | 推荐 | Flask 密钥（默认有开发用值） |

---

## 7. API 接口

| 方法 | 路由 | 说明 | 登录 |
|------|------|------|------|
| GET | `/` | 首页留言列表 | 否 |
| GET | `/publish` | 发布页面 | 否 |
| POST | `/publish` | 提交留言 | 是 |
| GET | `/message/<id>` | 留言详情 | 否 |
| POST | `/message/<id>` | 提交回复 | 是 |
| POST | `/message/<id>/delete` | 删除留言 | 是(作者/管理员) |
| POST | `/reply/<id>/delete` | 删除回复 | 是(作者/管理员) |
| POST | `/like/<id>` | 点赞/取消（JSON） | 是 |
| GET | `/search` | 搜索留言/用户 | 否 |
| GET | `/register` | 注册页 | 否 |
| POST | `/register` | 提交注册 | 否 |
| GET | `/login` | 登录页 | 否 |
| POST | `/login` | 提交登录 | 否 |
| GET | `/logout` | 退出 | 是 |
| GET | `/profile` | 个人信息页 | 是 |
| POST | `/profile` | 更新信息/头像 | 是 |
| GET | `/user/<id>` | 用户主页 | 否 |
| GET | `/admin` | 管理后台 | 是(管理员) |
| POST | `/admin/pin/<id>` | 置顶/取消（JSON） | 是(管理员) |

---

## 8. 常见问题

### Q: 图片上传后消失？
改用 base64 存储后已解决，图片直接存数据库，不依赖文件系统。

### Q: Railway 部署后连不上数据库？
检查 `config.py` 的数据库 URL 格式，Railway 使用 `postgresql://` 前缀，需转为 `postgresql+pg8000://`。

### Q: 如何创建管理员？
首次启动时自动创建：`admin / admin123`

### Q: 如何迁移数据？
提供了一键迁移脚本，支持 Railway → 本地 PostgreSQL 的数据导出导入。

---

## 许可证

MIT License
