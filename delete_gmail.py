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

def delete_emails(service, message_ids, batch_size=1000):
    """批量删除邮件（使用 Gmail API 的批量删除功能）"""
    if not message_ids:
        print("没有找到要删除的邮件")
        return
    
    total_count = len(message_ids)
    print(f"\n找到 {total_count} 封邮件，开始批量删除...")
    print(f"批量大小: {batch_size} 封/批")
    
    deleted_count = 0
    failed_count = 0
    failed_batches = []
    
    # 将邮件 ID 列表分批处理（Gmail API 批量删除最多支持 1000 封）
    batches = []
    for i in range(0, total_count, batch_size):
        batch = [msg['id'] for msg in message_ids[i:i + batch_size]]
        batches.append(batch)
    
    total_batches = len(batches)
    print(f"共 {total_batches} 批需要处理\n")
    
    for batch_num, batch_ids in enumerate(batches, 1):
        try:
            # 使用批量删除 API
            service.users().messages().batchDelete(
                userId='me',
                body={'ids': batch_ids}
            ).execute()
            
            deleted_count += len(batch_ids)
            progress = (batch_num / total_batches) * 100
            print(f"进度: [{batch_num}/{total_batches}] ({progress:.1f}%) - 已删除 {deleted_count}/{total_count} 封邮件")
            
        except HttpError as error:
            error_str = str(error)
            if 'insufficientPermissions' in error_str or 'insufficient authentication scopes' in error_str:
                print("\n错误: 权限不足！")
                print("需要删除旧的 token 并重新授权。")
                print("请删除 token.pickle 文件后重新运行脚本。")
                if os.path.exists('token.pickle'):
                    print("正在删除旧的 token.pickle...")
                    os.remove('token.pickle')
                return
            
            # 如果批量删除失败，尝试逐个删除这一批
            print(f"\n警告: 第 {batch_num} 批批量删除失败，尝试逐个删除...")
            failed_batch_count = 0
            for msg_id in batch_ids:
                try:
                    service.users().messages().delete(userId='me', id=msg_id).execute()
                    deleted_count += 1
                    failed_batch_count += 1
                except HttpError as e:
                    failed_count += 1
                    if 'insufficientPermissions' in str(e) or 'insufficient authentication scopes' in str(e):
                        print("\n错误: 权限不足！")
                        if os.path.exists('token.pickle'):
                            os.remove('token.pickle')
                        return
                    print(f"  删除邮件 {msg_id} 失败: {e}")
            
            if failed_batch_count > 0:
                print(f"  第 {batch_num} 批中成功删除 {failed_batch_count}/{len(batch_ids)} 封")
            else:
                failed_batches.append(batch_num)
    
    print("\n" + "=" * 60)
    print("删除完成！")
    print("=" * 60)
    print(f"成功删除: {deleted_count} 封")
    if failed_count > 0:
        print(f"删除失败: {failed_count} 封")
    if failed_batches:
        print(f"失败的批次: {failed_batches}")

def main():
    """主函数"""
    print("=" * 60)
    print("Gmail 邮件删除工具 (批量删除模式)")
    print("=" * 60)
    print("使用 Gmail API 批量删除功能，每批最多删除 1000 封邮件")
    print("=" * 60)
    
    # 获取 Gmail 服务
    service = get_gmail_service()
    if not service:
        return
    
    # 搜索主题包含 "ruanyf/weekly" Unity Ads/ gave you kudos的邮件
    keywords = 'New ios questions'
    keywords = '猎头'
    query = f'subject:"{keywords}"'

    print(f"\n正在搜索主题包含 '{keywords}' 的邮件...")
    
    messages = search_emails(service, query)
    
    if not messages:
        print("没有找到匹配的邮件")
        return
    
    print(f"找到 {len(messages)} 封匹配的邮件")
    
    # 计算预计批次数
    batch_size = 1000
    estimated_batches = (len(messages) + batch_size - 1) // batch_size
    print(f"预计将分 {estimated_batches} 批进行删除（每批 {batch_size} 封）")
    
    # 确认删除
    # response = input(f"\n确定要删除这 {len(messages)} 封邮件吗? (yes/no): ")
    # if response.lower() not in ['yes', 'y', '是']:
    #     print("操作已取消")
    #     return
    
    # 批量删除邮件
    delete_emails(service, messages, batch_size=batch_size)
    
    print("\n操作完成！")

if __name__ == '__main__':
    main()

