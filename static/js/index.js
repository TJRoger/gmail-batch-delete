// 首页JavaScript

let searchResults = null;

// 搜索表单提交
document.getElementById('search-form').addEventListener('submit', async function (e) {
    e.preventDefault();

    const formData = new FormData(e.target);
    const filters = {};

    // 收集表单数据
    if (formData.get('subject')) filters.subject = formData.get('subject');
    if (formData.get('from')) filters.from = formData.get('from');
    if (formData.get('to')) filters.to = formData.get('to');
    if (formData.get('keyword')) filters.keyword = formData.get('keyword');
    if (formData.get('after_date')) filters.after_date = formData.get('after_date');
    if (formData.get('before_date')) filters.before_date = formData.get('before_date');
    if (formData.get('label')) filters.label = formData.get('label');
    if (document.getElementById('has-attachment').checked) filters.has_attachment = true;
    if (document.getElementById('is-read').checked) filters.is_read = true;
    if (document.getElementById('is-starred').checked) filters.is_starred = true;
    filters.search_scope = document.getElementById('search-scope').value;

    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ filters })
        });

        const data = await response.json();

        if (response.ok) {
            searchResults = data;
            displayResults(data);
        } else {
            alert('搜索失败: ' + (data.error || '未知错误'));
        }
    } catch (error) {
        console.error('搜索错误:', error);
        alert('搜索时发生错误，请检查网络连接');
    }
});

// 显示搜索结果
function displayResults(data) {
    const resultsPanel = document.getElementById('results-panel');
    const resultsInfo = document.getElementById('results-info');

    resultsPanel.style.display = 'block';
    resultsInfo.innerHTML = `
        <strong>找到 ${data.count} 封匹配的邮件</strong><br>
        <small>搜索查询: ${data.query || 'N/A'}</small>
    `;

    // 滚动到结果面板
    resultsPanel.scrollIntoView({ behavior: 'smooth' });
}

// 预览邮件列表
document.getElementById('preview-btn').addEventListener('click', function () {
    if (!searchResults || !searchResults.messages) {
        alert('请先搜索邮件');
        return;
    }

    const previewList = document.getElementById('preview-list');
    previewList.innerHTML = '<h4>邮件预览（前100条）:</h4>';

    searchResults.messages.forEach((msg, index) => {
        const item = document.createElement('div');
        item.className = 'preview-item';

        // 获取邮件信息
        const subject = msg.subject || '无标题';
        const from = msg.from || '未知发件人';
        const date = msg.date || '';
        const snippet = msg.snippet || '';

        // 创建更详细的显示
        item.innerHTML = `
            <div style="margin-bottom: 0.5rem;">
                <strong>${index + 1}. ${subject}</strong>
            </div>
            <div style="font-size: 0.875rem; color: #666;">
                发件人: ${from} | ${date ? '日期: ' + date : ''}
            </div>
            ${snippet ? `<div style="font-size: 0.875rem; color: #888; margin-top: 0.25rem;">${snippet.substring(0, 100)}${snippet.length > 100 ? '...' : ''}</div>` : ''}
        `;

        previewList.appendChild(item);
    });
});

// 删除邮件
document.getElementById('delete-btn').addEventListener('click', async function () {
    if (!searchResults) {
        alert('请先搜索邮件');
        return;
    }

    const count = searchResults.count;
    if (count === 0) {
        alert('没有找到要删除的邮件');
        return;
    }

    if (!confirm(`确定要删除 ${count} 封邮件吗？\n\n⚠️ 警告：此操作不可恢复！`)) {
        return;
    }

    // 显示进度面板
    const progressPanel = document.getElementById('progress-panel');
    progressPanel.style.display = 'block';
    progressPanel.scrollIntoView({ behavior: 'smooth' });

    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');

    try {
        // 获取所有邮件ID（需要完整搜索）
        const form = document.getElementById('search-form');
        const formData = new FormData(form);
        const filters = {};

        if (formData.get('subject')) filters.subject = formData.get('subject');
        if (formData.get('from')) filters.from = formData.get('from');
        if (formData.get('to')) filters.to = formData.get('to');
        if (formData.get('keyword')) filters.keyword = formData.get('keyword');
        if (formData.get('after_date')) filters.after_date = formData.get('after_date');
        if (formData.get('before_date')) filters.before_date = formData.get('before_date');
        if (formData.get('label')) filters.label = formData.get('label');
        if (document.getElementById('has-attachment').checked) filters.has_attachment = true;
        if (document.getElementById('is-read').checked) filters.is_read = true;
        if (document.getElementById('is-starred').checked) filters.is_starred = true;
        filters.search_scope = document.getElementById('search-scope').value;

        progressText.textContent = '正在删除邮件...';

        const response = await fetch('/api/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ filters })
        });

        const result = await response.json();

        if (response.ok) {
            const percentage = (result.deleted / count) * 100;
            progressFill.style.width = percentage + '%';
            progressFill.textContent = Math.round(percentage) + '%';

            progressText.innerHTML = `
                <strong>删除完成！</strong><br>
                成功删除: ${result.deleted} 封<br>
                删除失败: ${result.failed || 0} 封
            `;

            // 更新搜索结果
            searchResults.count = 0;
            displayResults(searchResults);
        } else {
            progressText.textContent = '删除失败: ' + (result.error || '未知错误');
            progressFill.style.backgroundColor = '#dc3545';
        }
    } catch (error) {
        console.error('删除错误:', error);
        progressText.textContent = '删除时发生错误: ' + error.message;
        progressFill.style.backgroundColor = '#dc3545';
    }
});

// 清空表单
document.getElementById('clear-btn').addEventListener('click', function () {
    document.getElementById('search-form').reset();
    document.getElementById('results-panel').style.display = 'none';
    document.getElementById('progress-panel').style.display = 'none';
    searchResults = null;
});

