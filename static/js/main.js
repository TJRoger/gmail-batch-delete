// 主JavaScript文件

// 检查用户授权状态
async function checkUserStatus() {
    try {
        const response = await fetch('/api/user/info');
        const data = await response.json();
        
        const statusDiv = document.getElementById('user-status');
        if (!statusDiv) return;
        
        if (data.authorized) {
            statusDiv.className = 'user-status authorized';
            statusDiv.innerHTML = `
                <h3>✓ 已授权</h3>
                <p>邮箱: ${data.email || '未知'}</p>
                <p>邮件总数: ${data.messages_total || 0} | 会话总数: ${data.threads_total || 0}</p>
                <p><small>最后更新: ${new Date().toLocaleTimeString()}</small></p>
            `;
            
            const userInfo = document.getElementById('user-info');
            if (userInfo) {
                userInfo.textContent = data.email || '已登录';
            }
            
            return true;
        } else {
            statusDiv.className = 'user-status unauthorized';
            statusDiv.innerHTML = `
                <h3>✗ 未授权</h3>
                <p>请先<a href="/login">登录授权</a></p>
                <p><small>最后检查: ${new Date().toLocaleTimeString()}</small></p>
            `;
            
            return false;
        }
    } catch (error) {
        console.error('检查用户状态失败:', error);
        const statusDiv = document.getElementById('user-status');
        if (statusDiv) {
            statusDiv.className = 'user-status unauthorized';
            statusDiv.innerHTML = `
                <h3>✗ 检查失败</h3>
                <p>无法连接到服务器，请刷新页面重试</p>
            `;
        }
        return false;
    }
}

// 页面加载时立即检查状态
(function() {
    // 立即检查（不等待DOMContentLoaded）
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', checkUserStatus);
    } else {
        // DOM已经加载完成，立即检查
        checkUserStatus();
    }
    
    // 页面可见性变化时重新检查（用户切换标签页回来时）
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            checkUserStatus();
        }
    });
    
    // 页面获得焦点时重新检查
    window.addEventListener('focus', checkUserStatus);
    
    // 定期刷新状态（每5分钟）
    setInterval(checkUserStatus, 5 * 60 * 1000);
})();






