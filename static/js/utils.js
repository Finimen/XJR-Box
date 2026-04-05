function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString(undefined, {
        year: 'numeric', month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });
}

function formatDuration(ms) {
    if (!ms) return '—';
    if (ms < 1000) return `${ms}ms`;
    const sec = Math.floor(ms / 1000);
    if (sec < 60) return `${sec}s`;
    const min = Math.floor(sec / 60);
    return `${min}m ${sec % 60}s`;
}

function showToast(message, type = 'info') {
    const existingToasts = document.querySelectorAll('.toast');
    existingToasts.forEach(t => t.remove());
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <span class="material-icons">${type === 'success' ? 'check_circle' : type === 'error' ? 'error' : 'info'}</span>
            <span>${escapeHtml(message)}</span>
        </div>
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

function loadSettings() {
    const settings = JSON.parse(localStorage.getItem('user_settings') || '{}');
    const checkboxes = ['emailNotifications', 'successAlerts', 'failureAlerts', 'dailyDigest'];
    checkboxes.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            const key = id === 'emailNotifications' ? 'email_notifications' :
                        id === 'successAlerts' ? 'success_alerts' :
                        id === 'failureAlerts' ? 'failure_alerts' : 'daily_digest';
            el.checked = settings[key] !== undefined ? settings[key] : (id === 'successAlerts' || id === 'failureAlerts');
        }
    });
    const selects = ['maxConcurrent', 'defaultTimeout', 'pythonVersion', 'logRetention'];
    selects.forEach(id => {
        const el = document.getElementById(id);
        if (el && settings[id.replace(/([A-Z])/g, '_$1').toLowerCase()]) {
            el.value = settings[id.replace(/([A-Z])/g, '_$1').toLowerCase()];
        }
    });
    const webhook = document.getElementById('webhookUrl');
    if (webhook && settings.webhook_url) webhook.value = settings.webhook_url;
}

function saveSetting(key, value) {
    const settings = JSON.parse(localStorage.getItem('user_settings') || '{}');
    settings[key] = value;
    localStorage.setItem('user_settings', JSON.stringify(settings));
    showToast(`${key.replace(/_/g, ' ')} updated`, 'success');
}

function saveWebhook() {
    const url = document.getElementById('webhookUrl')?.value;
    if (url) saveSetting('webhook_url', url);
    else showToast('Enter a valid URL', 'error');
}

function copyApiKey() {
    const keySpan = document.getElementById('apiKey');
    if (keySpan) {
        navigator.clipboard.writeText(keySpan.innerText);
        showToast('API Key copied', 'success');
    }
}

function rotateApiKey() {
    const newKey = 'sk_live_' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 10);
    if (document.getElementById('apiKey')) {
        document.getElementById('apiKey').innerText = newKey;
        saveSetting('api_key', newKey);
        showToast('New API key generated', 'success');
    }
}