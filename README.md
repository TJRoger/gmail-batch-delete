# buy-me-a-coffee
<img src="https://raw.githubusercontent.com/TJRoger/node-dota2-spectator/master/alipay_collect.jpg" width=400px >

# Gmail 邮件批量删除工具

一个功能强大的 Gmail 邮件批量删除工具，支持 Web 界面和多维度过滤。

## 功能特性

- 🌐 **Web 界面** - 友好的图形化界面，无需命令行操作
- 👥 **多用户支持** - 按用户ID分目录存储token，支持多账户管理
- 🔍 **多维度过滤** - 支持主题、发件人、收件人、日期、标签、附件等多种过滤条件
- ⚡ **批量删除** - 使用 Gmail API 批量删除功能，快速高效
- 🔒 **安全授权** - OAuth 2.0 授权，token 按用户隔离存储

## 项目结构

```
.
├── app.py                 # Flask Web 应用主文件
├── delete_gmail.py        # 命令行版本（旧版）
├── templates/            # HTML 模板
│   ├── base.html
│   ├── index.html
│   └── login.html
├── static/               # 静态文件
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── main.js
│       └── index.js
├── users/                # 用户数据目录（自动创建）
│   └── {user_id}/
│       └── token.pickle
├── requirements.txt      # Python 依赖
├── run.sh                # 启动脚本
└── README.md             # 说明文档
```

## 安装步骤

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

或使用指定的 Python 解释器：

```bash
/Users/admin/miniconda3/bin/python3 -m pip install -r requirements.txt
```

### 2. 获取 Google API 凭据

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 启用 **Gmail API**:
   - 在左侧菜单选择 "API 和服务" > "库"
   - 搜索 "Gmail API"
   - 点击启用
4. 创建 OAuth 2.0 凭据:
   - 在左侧菜单选择 "API 和服务" > "凭据"
   - 点击 "创建凭据" > "OAuth 客户端 ID"
   - **选择应用类型为 "Web 应用"**（重要！Web服务需要使用Web应用类型）
   - 添加授权重定向 URI: `http://localhost:5004/oauth2callback`
   - 下载凭据文件
   - 将下载的文件重命名为 `credentials.json` 或保持 `client_secret_*.json` 格式

### 3. 启动 Web 服务

**方式一：使用启动脚本**

```bash
./run.sh
```

**方式二：直接运行**

```bash
python3 app.py
```

或使用指定的 Python 解释器：

```bash
/Users/admin/miniconda3/bin/python3 app.py
```

### 4. 访问 Web 界面

打开浏览器访问：http://localhost:5004

## 使用说明

### 首次使用

1. 访问 http://localhost:5004
2. 点击"登录"或直接访问登录页面
3. 输入用户ID（可选，默认为 "default"）
4. 点击"开始授权"
5. 在 Google 授权页面授予应用访问 Gmail 的权限
6. 授权完成后自动返回应用

### 搜索和删除邮件

1. 在搜索表单中填写过滤条件：
   - **主题包含** - 搜索邮件主题
   - **发件人** - 指定发件人邮箱
   - **收件人** - 指定收件人邮箱
   - **关键词** - 全文搜索
   - **日期范围** - 选择开始和结束日期
   - **标签** - Gmail 标签（如 INBOX, SPAM）
   - **包含附件** - 只搜索带附件的邮件
   - **已读/未读** - 筛选已读或未读邮件
   - **已加星标** - 只搜索已加星标的邮件

2. 点击"搜索邮件"查看匹配结果

3. 确认结果后，删除按钮

4. 查看删除进度和结果

### 多用户管理

- 每个用户ID对应一个独立的目录（`users/{user_id}/`）
- Token 文件按用户隔离存储
- 可以在登录时指定不同的用户ID来管理多个账户

## 支持的过滤条件

| 条件 | Gmail 查询语法 | 说明 |
|------|---------------|------|
| 主题 | `subject:"关键词"` | 主题包含指定关键词 |
| 发件人 | `from:"邮箱"` | 来自指定发件人 |
| 收件人 | `to:"邮箱"` | 发送给指定收件人 |
| 关键词 | `"关键词"` | 全文搜索 |
| 日期范围 | `after:YYYY/MM/DD before:YYYY/MM/DD` | 日期范围过滤 |
| 标签 | `label:"标签名"` | Gmail 标签过滤 |
| 附件 | `has:attachment` | 包含附件 |
| 已读状态 | `is:read` / `is:unread` | 已读/未读 |
| 星标 | `is:starred` | 已加星标 |

## API 接口

### POST /api/search
搜索邮件

**请求体：**
```json
{
  "filters": {
    "subject": "关键词",
    "from": "example@gmail.com",
    "after_date": "2024/01/01"
  }
}
```

**响应：**
```json
{
  "count": 100,
  "messages": [...],
  "query": "subject:\"关键词\" from:\"example@gmail.com\""
}
```

### POST /api/delete
删除邮件

**请求体：**
```json
{
  "filters": {
    "subject": "关键词"
  }
}
```

或直接指定邮件ID：

```json
{
  "message_ids": ["id1", "id2", "id3"]
}
```

**响应：**
```json
{
  "deleted": 100,
  "failed": 0,
  "failed_batches": []
}
```

### GET /api/user/info
获取用户信息

**响应：**
```json
{
  "authorized": true,
  "email": "user@gmail.com",
  "messages_total": 10000,
  "threads_total": 5000
}
```

## 注意事项

- ⚠️ **删除操作不可恢复**，请谨慎操作
- 批量删除每批最多 1000 封邮件（Gmail API 限制）
- Token 文件存储在 `users/{user_id}/token.pickle`
- 如果遇到权限问题，删除对应的 token.pickle 文件后重新授权
- Web 服务默认运行在 `http://localhost:5004`
- 生产环境建议使用 HTTPS 和更安全的 session 密钥

## 命令行版本

如果需要使用命令行版本，可以运行：

```bash
python3 delete_gmail.py
```

命令行版本的使用说明请参考文件内的注释。

## 故障排除

### 权限不足错误

如果遇到 `insufficient authentication scopes` 错误：

1. 删除对应的 token 文件：`users/{user_id}/token.pickle`
2. 重新授权

### 找不到凭据文件

确保项目目录中存在以下文件之一：
- `credentials.json`
- `client_secret_*.json`

### 端口被占用

修改 `app.py` 文件末尾的端口号：

```python
app.run(debug=True, host='0.0.0.0', port=5004)  # 改为其他端口
```

## 开发调试

使用 VS Code/Cursor 调试：

1. 按 `F5` 启动调试
2. 或使用调试配置：`.vscode/launch.json`

## 许可证

MIT License
