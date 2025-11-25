# buy-me-a-coffee
<img src="https://raw.githubusercontent.com/TJRoger/node-dota2-spectator/master/alipay_collect.jpg" width=400px >
# Gmail 邮件删除工具

这个工具可以帮你删除 Gmail 邮箱中主题包含 "ruanyf/weekly" 的全部邮件。

## 使用步骤

### 1. 安装依赖

```bash
pip install -r requirements.txt
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
   - 选择应用类型为 "桌面应用"
   - 下载凭据文件
   - 将下载的文件重命名为 `credentials.json` 并放在项目目录中

### 3. 运行脚本

```bash
python delete_gmail.py
```

首次运行时会打开浏览器进行授权，授权完成后会自动保存 token，之后运行就不需要再次授权了。

### 4. 确认删除

脚本会显示找到的邮件数量，并询问是否确认删除。输入 `yes` 或 `y` 确认删除。

## 注意事项

- ⚠️ **删除操作不可恢复**，请谨慎操作
- 脚本会先搜索所有匹配的邮件，然后批量删除
- 如果邮件数量很多，删除过程可能需要一些时间
- 建议先测试搜索功能，确认找到的邮件是正确的

## 修改搜索条件

如果需要修改搜索条件，可以编辑 `delete_gmail.py` 文件中的 `query` 变量：

```python
query = 'subject:"ruanyf/weekly"'  # 当前搜索条件
```

你也可以使用其他 Gmail 搜索语法，例如：
- `subject:"关键词"` - 主题包含关键词
- `from:example@gmail.com` - 来自特定发件人
- `has:attachment` - 包含附件
- 等等

