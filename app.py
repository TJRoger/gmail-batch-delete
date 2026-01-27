#!/usr/bin/env python3
"""
Gmail 邮件批量删除 Web 服务
支持多用户、多维度过滤、批量删除
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import pickle
import glob
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import secrets

# 允许在开发环境中使用 HTTP（仅用于本地开发）
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # 用于session加密

# Gmail API 权限范围
SCOPES = ['https://mail.google.com/']

# 配置
CONFIG = {
    'CLIENT_SECRETS_FILE': None,  # 将在启动时自动查找
    'USERS_DIR': 'users',  # 用户数据目录
    'BATCH_SIZE': 1000,  # 批量删除大小
}

# 确保用户目录存在
os.makedirs(CONFIG['USERS_DIR'], exist_ok=True)


def find_credentials_file():
    """查找凭据文件"""
    if os.path.exists('credentials.json'):
        return 'credentials.json'
    client_secret_files = glob.glob('client_secret*.json')
    if client_secret_files:
        return client_secret_files[0]
    return None


def get_user_dir(user_id):
    """获取用户目录路径"""
    user_dir = os.path.join(CONFIG['USERS_DIR'], str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    return user_dir


def get_gmail_service(user_id):
    """获取 Gmail API 服务对象（按用户ID）"""
    user_dir = get_user_dir(user_id)
    token_path = os.path.join(user_dir, 'token.pickle')
    creds = None
    
    # 加载已保存的凭据
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    # 检查权限范围
    # https://mail.google.com/ 是最广泛的权限，包含所有 Gmail 权限
    # 如果 token 中有这个权限或我们需要的权限，就认为是有效的
    if creds and creds.scopes:
        required_scope = SCOPES[0]
        # 检查是否有我们需要的权限，或者有更广泛的 mail.google.com 权限
        has_required_scope = required_scope in creds.scopes
        has_full_scope = 'https://mail.google.com/' in creds.scopes
        
        if not has_required_scope and not has_full_scope:
            print(f"用户 {user_id}: 权限范围不匹配，删除旧token")
            print(f"  需要的权限: {required_scope}")
            print(f"  当前权限: {creds.scopes}")
            os.remove(token_path)
            creds = None
        elif has_full_scope and not has_required_scope:
            # 如果有更广泛的权限，这是可以的，只是打印信息
            print(f"用户 {user_id}: 使用更广泛的权限范围 (https://mail.google.com/)")
    
    # 如果没有有效的凭据，返回None（需要重新授权）
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # 保存刷新后的token
                with open(token_path, 'wb') as token:
                    pickle.dump(creds, token)
            except Exception as e:
                print(f"刷新token失败: {e}")
                if os.path.exists(token_path):
                    os.remove(token_path)
                creds = None
    
    if not creds:
        return None
    
    try:
        service = build('gmail', 'v1', credentials=creds)
        return service
    except HttpError as error:
        print(f'创建Gmail服务时发生错误: {error}')
        return None


def build_query(filters):
    """构建Gmail搜索查询"""
    query_parts = []
    
    # 主题过滤
    if filters.get('subject'):
        query_parts.append(f'subject:"{filters["subject"]}"')
    
    # 发件人过滤
    if filters.get('from'):
        query_parts.append(f'from:"{filters["from"]}"')
    
    # 收件人过滤
    if filters.get('to'):
        query_parts.append(f'to:"{filters["to"]}"')
    
    # 日期过滤
    if filters.get('after_date'):
        query_parts.append(f'after:{filters["after_date"]}')
    
    if filters.get('before_date'):
        query_parts.append(f'before:{filters["before_date"]}')
    
    # 标签过滤
    if filters.get('label'):
        query_parts.append(f'label:"{filters["label"]}"')
    
    # 包含附件
    if filters.get('has_attachment'):
        query_parts.append('has:attachment')
    
    # 已读/未读
    if filters.get('is_read') is not None:
        if filters['is_read']:
            query_parts.append('is:read')
        else:
            query_parts.append('is:unread')
    
    # 已加星标
    if filters.get('is_starred'):
        query_parts.append('is:starred')
    
    # 关键词搜索（全文搜索）
    if filters.get('keyword'):
        query_parts.append(f'"{filters["keyword"]}"')
    
    return ' '.join(query_parts) if query_parts else None


def search_emails(service, query):
    """搜索匹配查询的邮件"""
    if not query:
        return []
    
    try:
        messages = []
        results = service.users().messages().list(userId='me', q=query).execute()
        messages.extend(results.get('messages', []))
        
        # 处理分页
        while 'nextPageToken' in results:
            page_token = results['nextPageToken']
            results = service.users().messages().list(
                userId='me', q=query, pageToken=page_token).execute()
            messages.extend(results.get('messages', []))
        
        return messages
    except HttpError as error:
        print(f'搜索邮件时发生错误: {error}')
        return []


def get_message_details(service, message_ids, max_results=100):
    """获取邮件详细信息（标题、发件人等）"""
    if not message_ids:
        return []
    
    messages_with_details = []
    # 限制获取数量，避免请求过多
    message_ids_to_fetch = message_ids[:max_results]
    
    for msg in message_ids_to_fetch:
        try:
            message = service.users().messages().get(
                userId='me', 
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'To', 'Subject', 'Date']
            ).execute()
            
            # 提取邮件头信息
            headers = message.get('payload', {}).get('headers', [])
            header_dict = {}
            for header in headers:
                name = header.get('name', '').lower()
                value = header.get('value', '')
                header_dict[name] = value
            
            messages_with_details.append({
                'id': msg['id'],
                'threadId': msg.get('threadId', ''),
                'subject': header_dict.get('subject', '无标题'),
                'from': header_dict.get('from', '未知发件人'),
                'to': header_dict.get('to', ''),
                'date': header_dict.get('date', ''),
                'snippet': message.get('snippet', '')
            })
        except HttpError as error:
            # 如果获取失败，至少返回ID
            messages_with_details.append({
                'id': msg['id'],
                'threadId': msg.get('threadId', ''),
                'subject': '获取失败',
                'from': '未知',
                'to': '',
                'date': '',
                'snippet': ''
            })
    
    return messages_with_details


def delete_emails_batch(service, message_ids, batch_size=1000):
    """批量删除邮件"""
    if not message_ids:
        return {'deleted': 0, 'failed': 0, 'failed_batches': []}
    
    total_count = len(message_ids)
    deleted_count = 0
    failed_count = 0
    failed_batches = []
    
    # 分批处理
    batches = []
    for i in range(0, total_count, batch_size):
        batch = [msg['id'] for msg in message_ids[i:i + batch_size]]
        batches.append(batch)
    
    for batch_num, batch_ids in enumerate(batches, 1):
        try:
            service.users().messages().batchDelete(
                userId='me',
                body={'ids': batch_ids}
            ).execute()
            deleted_count += len(batch_ids)
        except HttpError as error:
            error_str = str(error)
            if 'insufficientPermissions' in error_str or 'insufficient authentication scopes' in error_str:
                return {
                    'deleted': deleted_count,
                    'failed': total_count - deleted_count,
                    'failed_batches': failed_batches,
                    'error': '权限不足，请重新授权'
                }
            
            # 批量删除失败，尝试逐个删除
            for msg_id in batch_ids:
                try:
                    service.users().messages().delete(userId='me', id=msg_id).execute()
                    deleted_count += 1
                except HttpError:
                    failed_count += 1
            failed_batches.append(batch_num)
    
    return {
        'deleted': deleted_count,
        'failed': failed_count,
        'failed_batches': failed_batches
    }


# Web路由
@app.route('/')
def index():
    """首页"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    return render_template('index.html', user_id=user_id)


@app.route('/login')
def login():
    """登录/授权页面"""
    return render_template('login.html')


@app.route('/auth')
def auth():
    """开始OAuth授权流程"""
    user_id = request.args.get('user_id', 'default')
    session['user_id'] = user_id
    
    credentials_file = find_credentials_file()
    if not credentials_file:
        return jsonify({'error': '找不到凭据文件'}), 500
    
    CONFIG['CLIENT_SECRETS_FILE'] = credentials_file
    
    flow = Flow.from_client_secrets_file(
        credentials_file,
        scopes=SCOPES,
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    
    session['state'] = state
    return redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():
    """OAuth回调处理"""
    user_id = session.get('user_id', 'default')
    state = session.get('state')
    
    if not state or state != request.args.get('state'):
        return jsonify({'error': '状态不匹配'}), 400
    
    credentials_file = CONFIG.get('CLIENT_SECRETS_FILE') or find_credentials_file()
    if not credentials_file:
        return jsonify({'error': '找不到凭据文件'}), 500
    
    flow = Flow.from_client_secrets_file(
        credentials_file,
        scopes=SCOPES,
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    
    # 捕获权限范围变化的警告（这是正常的，因为 https://mail.google.com/ 包含所有权限）
    # oauthlib 会将 Warning 作为异常抛出，我们需要捕获并处理
    # 注意：授权码只能使用一次，所以不能重新调用 fetch_token
    
    # 使用 monkey patch 来忽略权限范围变化的警告
    import oauthlib.oauth2.rfc6749.parameters as oauth_params
    original_validate = oauth_params.validate_token_parameters
    
    def patched_validate(params):
        """修改后的验证函数，忽略权限范围变化的警告"""
        try:
            return original_validate(params)
        except Warning as w:
            if 'Scope has changed' in str(w):
                # 忽略权限范围变化的警告，直接返回参数
                print(f"权限范围变化警告（已忽略）: {w}")
                return params
            raise
    
    # 临时替换验证函数
    oauth_params.validate_token_parameters = patched_validate
    
    try:
        flow.fetch_token(authorization_response=request.url)
    finally:
        # 恢复原始函数
        oauth_params.validate_token_parameters = original_validate
    
    creds = flow.credentials
    user_dir = get_user_dir(user_id)
    token_path = os.path.join(user_dir, 'token.pickle')
    
    with open(token_path, 'wb') as token:
        pickle.dump(creds, token)
    
    return redirect(url_for('index'))


@app.route('/api/search', methods=['POST'])
def api_search():
    """搜索邮件API"""
    user_id = session.get('user_id', 'default')
    service = get_gmail_service(user_id)
    
    if not service:
        return jsonify({'error': '未授权，请先登录'}), 401
    
    filters = request.json.get('filters', {})
    query = build_query(filters)
    
    if not query:
        return jsonify({'error': '请至少提供一个搜索条件'}), 400
    
    # 搜索邮件（只返回ID列表）
    message_ids = search_emails(service, query)
    
    # 获取前100条邮件的详细信息（包括标题、发件人等）
    messages_with_details = get_message_details(service, message_ids, max_results=100)
    
    return jsonify({
        'count': len(message_ids),
        'messages': messages_with_details,  # 返回包含详细信息的邮件列表
        'query': query
    })


@app.route('/api/delete', methods=['POST'])
def api_delete():
    """删除邮件API"""
    user_id = session.get('user_id', 'default')
    service = get_gmail_service(user_id)
    
    if not service:
        return jsonify({'error': '未授权，请先登录'}), 401
    
    data = request.json
    filters = data.get('filters', {})
    message_ids = data.get('message_ids', [])
    
    if message_ids:
        # 直接删除指定的邮件ID
        result = delete_emails_batch(service, [{'id': mid} for mid in message_ids])
    elif filters:
        # 根据过滤条件搜索并删除
        query = build_query(filters)
        if not query:
            return jsonify({'error': '请至少提供一个搜索条件'}), 400
        
        messages = search_emails(service, query)
        result = delete_emails_batch(service, messages)
    else:
        return jsonify({'error': '请提供过滤条件或邮件ID列表'}), 400
    
    return jsonify(result)


@app.route('/api/user/info')
def api_user_info():
    """获取用户信息"""
    user_id = session.get('user_id', 'default')
    service = get_gmail_service(user_id)
    
    if not service:
        return jsonify({'authorized': False})
    
    try:
        profile = service.users().getProfile(userId='me').execute()
        return jsonify({
            'authorized': True,
            'email': profile.get('emailAddress'),
            'messages_total': profile.get('messagesTotal'),
            'threads_total': profile.get('threadsTotal')
        })
    except HttpError:
        return jsonify({'authorized': False})


if __name__ == '__main__':
    # 初始化时查找凭据文件
    CONFIG['CLIENT_SECRETS_FILE'] = find_credentials_file()
    app.run(debug=True, host='0.0.0.0', port=5004)






