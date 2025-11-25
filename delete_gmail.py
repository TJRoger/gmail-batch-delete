#!/usr/bin/env python3
"""
删除 Gmail 邮箱中主题包含 "ruanyf/weekly" 的全部邮件
"""

import os
import pickle
import glob
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API 权限范围
SCOPES = ['https://mail.google.com/']

def get_gmail_service():
    """获取 Gmail API 服务对象"""
    creds = None
    
    # token.pickle 存储用户的访问和刷新令牌
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
        
        # 检查权限范围是否匹配
        if creds and creds.scopes:
            required_scope = SCOPES[0]
            if required_scope not in creds.scopes:
                print("警告: 当前 token 的权限范围不匹配")
                print(f"需要权限: {required_scope}")
                print(f"当前权限: {creds.scopes}")
                print("删除旧的 token，需要重新授权...")
                os.remove('token.pickle')
                creds = None
    
    # 如果没有有效的凭据，让用户登录
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except (Exception, OSError) as e:
                print(f"刷新 token 失败: {e}")
                print("删除旧的 token，需要重新授权...")
                if os.path.exists('token.pickle'):
                    os.remove('token.pickle')
                creds = None
        
        if not creds:
            # 查找凭据文件（支持多种文件名）
            credentials_file = None
            
            # 先检查 credentials.json
            if os.path.exists('credentials.json'):
                credentials_file = 'credentials.json'
            else:
                # 查找 client_secret 开头的 JSON 文件
                client_secret_files = glob.glob('client_secret*.json')
                if client_secret_files:
                    credentials_file = client_secret_files[0]
            
            if not credentials_file:
                print("错误: 找不到凭据文件")
                print("请确保存在以下文件之一:")
                print("  - credentials.json")
                print("  - client_secret*.json")
                print("\n请按照以下步骤操作:")
                print("1. 访问 https://console.cloud.google.com/")
                print("2. 创建新项目或选择现有项目")
                print("3. 启用 Gmail API")
                print("4. 创建 OAuth 2.0 客户端 ID (桌面应用)")
                print("5. 下载凭据文件")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_file, SCOPES)
            print("\n正在打开浏览器进行授权...")
            print("请授权应用访问你的 Gmail 邮箱（需要修改权限以删除邮件）")
            creds = flow.run_local_server(port=0)
            
            # 保存凭据供下次运行使用
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
            print("授权成功！token 已保存。")
    
    try:
        service = build('gmail', 'v1', credentials=creds)
        return service
    except HttpError as error:
        print(f'发生错误: {error}')
        return None

def search_emails(service, query):
    """搜索匹配查询的邮件"""
    try:
        results = service.users().messages().list(userId='me', q=query).execute()
        messages = results.get('messages', [])
        
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

def delete_emails(service, message_ids):
    """批量删除邮件"""
    if not message_ids:
        print("没有找到要删除的邮件")
        return
    
    deleted_count = 0
    failed_count = 0
    
    print(f"\n找到 {len(message_ids)} 封邮件，开始删除...")
    
    for i, msg_id in enumerate(message_ids, 1):
        try:
            service.users().messages().delete(userId='me', id=msg_id['id']).execute()
            deleted_count += 1
            if i % 10 == 0:
                print(f"已删除 {i}/{len(message_ids)} 封邮件...")
        except HttpError as error:
            failed_count += 1
            if 'insufficientPermissions' in str(error) or 'insufficient authentication scopes' in str(error):
                print("\n错误: 权限不足！")
                print("需要删除旧的 token 并重新授权。")
                print("请删除 token.pickle 文件后重新运行脚本。")
                if os.path.exists('token.pickle'):
                    print("正在删除旧的 token.pickle...")
                    os.remove('token.pickle')
                break
            print(f"删除邮件 {msg_id['id']} 时发生错误: {error}")
    
    print("\n删除完成！")
    print(f"成功删除: {deleted_count} 封")
    if failed_count > 0:
        print(f"删除失败: {failed_count} 封")

def main():
    """主函数"""
    print("=" * 60)
    print("Gmail 邮件删除工具")
    print("=" * 60)
    
    # 获取 Gmail 服务
    service = get_gmail_service()
    if not service:
        return
    
    # 搜索主题包含 "ruanyf/weekly" 的邮件
    query = 'subject:"ruanyf/weekly"'
    print("\n正在搜索主题包含 'ruanyf/weekly' 的邮件...")
    
    messages = search_emails(service, query)
    
    if not messages:
        print("没有找到匹配的邮件")
        return
    
    print(f"找到 {len(messages)} 封匹配的邮件")
    
    # 确认删除
    response = input(f"\n确定要删除这 {len(messages)} 封邮件吗? (yes/no): ")
    if response.lower() not in ['yes', 'y', '是']:
        print("操作已取消")
        return
    
    # 删除邮件
    delete_emails(service, messages)
    
    print("\n操作完成！")

if __name__ == '__main__':
    main()

