function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleString();
}

function formatDuration(ms) {
    if (!ms) return 'N/A';
    if (ms < 1000) return `${ms} ms`;
    const seconds = Math.floor(ms / 1000);
    if (seconds < 60) return `${seconds} sec`;
    const minutes = Math.floor(seconds / 60);
    return `${minutes} min ${seconds % 60} sec`;
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <span class="material-icons">${type === 'success' ? 'check_circle' : 'info'}</span>
            <span>${message}</span>
        </div>
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function loadSettings() {
    const settings = JSON.parse(localStorage.getItem('user_settings') || '{}');
    if (document.getElementById('emailNotifications')) {
        document.getElementById('emailNotifications').checked = settings.email_notifications || false;
        document.getElementById('successAlerts').checked = settings.success_alerts !== false;
        document.getElementById('failureAlerts').checked = settings.failure_alerts !== false;
        document.getElementById('dailyDigest').checked = settings.daily_digest || false;
        document.getElementById('maxConcurrent').value = settings.max_concurrent || '3';
        document.getElementById('defaultTimeout').value = settings.default_timeout || '30';
        document.getElementById('pythonVersion').value = settings.python_version || '3.11';
        document.getElementById('logRetention').value = settings.log_retention || '30';
        if (document.getElementById('webhookUrl')) {
            document.getElementById('webhookUrl').value = settings.webhook_url || '';
        }
    }
}

function saveSetting(key, value) {
    const settings = JSON.parse(localStorage.getItem('user_settings') || '{}');
    settings[key] = value;
    localStorage.setItem('user_settings', JSON.stringify(settings));
    showToast(`${key.replace('_', ' ')} saved!`, 'success');
}

function saveWebhook() {
    const url = document.getElementById('webhookUrl')?.value;
    if (url) saveSetting('webhook_url', url);
}

function copyApiKey() {
    const apiKey = document.getElementById('apiKey')?.innerText;
    if (apiKey) {
        navigator.clipboard.writeText(apiKey);
        showToast('API Key copied!', 'success');
    }
}

function rotateApiKey() {
    const newKey = 'sk_live_' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
    if (document.getElementById('apiKey')) {
        document.getElementById('apiKey').innerText = newKey;
        saveSetting('api_key', newKey);
        showToast('New API key generated!', 'success');
    }
}