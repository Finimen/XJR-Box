let token = localStorage.getItem('token');
let currentUser = null;
let allScripts = [];
let allExecutions = [];
let refreshInterval = null;

document.addEventListener('DOMContentLoaded', () => {
    if (token) {
        API.setToken(token);
        checkAuth();
    }
    setupNavigation();
    loadSettings();
});

function setupNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.dataset.page;
            showPage(page);
            document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
        });
    });
}

function showPage(page) {
    document.querySelectorAll('.page').forEach(p => p.style.display = 'none');
    const targetPage = document.getElementById(`${page}Page`);
    if (targetPage) targetPage.style.display = 'block';
    
    if (page === 'logs') refreshLogs();
    else if (page === 'dashboard') loadDashboard();
    else if (page === 'scripts') loadScripts();
    else if (page === 'profile') loadProfileStats();
}

async function checkAuth() {
    try {
        currentUser = await API.getMe();
        
        document.getElementById('authRequired').style.display = 'none';
        document.getElementById('mainAppContent').style.display = 'block';
        document.getElementById('userInfoSidebar').style.display = 'flex';
        
        UI.updateProfile(currentUser);
        
        await Promise.all([
            loadDashboard(),
            loadScripts(),
            loadAllLogs(),
            loadProfileStats()
        ]);
        
        if (refreshInterval) clearInterval(refreshInterval);
        refreshInterval = setInterval(() => {
            const activePage = document.querySelector('.nav-item.active')?.dataset.page;
            if (activePage === 'logs') refreshLogs();
            else if (activePage === 'dashboard') loadDashboard();
        }, 6000);
        
    } catch (error) {
        console.error('Auth failed:', error);
        logout();
    }
}

async function login() {
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;
    
    if (!username || !password) {
        showToast('Please fill all fields', 'error');
        return;
    }
    
    try {
        const data = await API.login(username, password);
        API.setToken(data.access_token);
        token = data.access_token;
        UI.hideModal('loginModal');
        await checkAuth();
        showToast(`Welcome back, ${username}!`, 'success');
    } catch (error) {
        showToast('Login failed: ' + error.message, 'error');
    }
}

async function register() {
    const username = document.getElementById('regUsername').value.trim();
    const email = document.getElementById('regEmail').value.trim();
    const password = document.getElementById('regPassword').value;
    
    if (!username || !email || !password) {
        showToast('All fields are required', 'error');
        return;
    }
    
    try {
        await API.register(username, email, password);
        showToast('Registration successful! Please login.', 'success');
        UI.hideModal('registerModal');
        UI.showModal('loginModal');
    } catch (error) {
        showToast('Registration failed: ' + error.message, 'error');
    }
}

async function logout() {
    await API.logout();
    API.setToken(null);
    token = null;
    currentUser = null;
    if (refreshInterval) clearInterval(refreshInterval);
    
    document.getElementById('authRequired').style.display = 'flex';
    document.getElementById('mainAppContent').style.display = 'none';
    document.getElementById('userInfoSidebar').style.display = 'none';
    UI.clearModalInputs(['loginUsername', 'loginPassword']);
    showToast('Signed out', 'info');
}

async function loadDashboard() {
    try {
        const scripts = await API.getScripts();
        const executions = await API.getAllExecutions();
        const allExecs = executions || [];
        
        allExecutions = allExecs.sort((a, b) => new Date(b.started_at) - new Date(a.started_at));
        const successCount = allExecutions.filter(e => e.status === 'success').length;
        const successRate = allExecutions.length > 0 ? Math.round((successCount / allExecutions.length) * 100) : 0;
        
        UI.updateDashboardStats(scripts.length, allExecutions.length, successRate);
        UI.renderRecentExecutions(allExecutions.slice(0, 5));
    } catch (error) {
        console.error('Dashboard error:', error);
    }
}

async function loadScripts() {
    try {
        allScripts = await API.getScripts();
        UI.renderScripts(allScripts, runScript, deleteScript, showScriptDetail);
    } catch (error) {
        console.error('Load scripts error:', error);
    }
}

async function createScriptFromModal() {
    const name = document.getElementById('modalScriptName').value.trim();
    const code = document.getElementById('modalScriptCode').value;
    const schedule = document.getElementById('modalScriptSchedule').value.trim() || null;
    
    if (!name || !code) {
        showToast('Name and code are required', 'error');
        return;
    }
    
    try {
        await API.createScript({ name, code, schedule });
        showToast('Script created successfully', 'success');
        UI.hideModal('createScriptModal');
        UI.clearModalInputs(['modalScriptName', 'modalScriptCode', 'modalScriptSchedule']);
        await Promise.all([loadScripts(), loadDashboard()]);
    } catch (error) {
        showToast('Failed to create script: ' + error.message, 'error');
    }
}

async function runScript(scriptId) {
    try {
        const data = await API.runScript(scriptId);
        showToast(`✅ Script started! Execution ID: ${data.execution_id}`, 'success');
        setTimeout(() => {
            loadDashboard();
            refreshLogs();
        }, 1000);
    } catch (error) {
        showToast('Failed to run script: ' + error.message, 'error');
    }
}

async function deleteScript(scriptId) {
    if (!confirm('⚠️ Permanently delete this script? This action cannot be undone.')) return;
    
    try {
        await API.deleteScript(scriptId);
        showToast('Script deleted', 'success');
        await Promise.all([loadScripts(), loadDashboard()]);
    } catch (error) {
        showToast('Delete failed: ' + error.message, 'error');
    }
}

async function showScriptDetail(_, scriptId) {
    const script = allScripts.find(s => s.id === scriptId);
    if (!script) return;
    
    const executions = await API.getScriptExecutions(scriptId, 5);
    
    document.getElementById('scriptDetailContent').innerHTML = UI.renderScriptDetail(script, executions);
    
    document.getElementById('detailScriptName').innerText = script.name;
    document.getElementById('runFromDetailBtn').onclick = () => runScript(script.id);
    UI.showModal('scriptDetailModal');
}

async function loadAllLogs() {
    try {
        const scripts = allScripts.length ? allScripts : await API.getScripts();
        allScripts = scripts;
        
        let allExecs = [];
        for (const script of scripts) {
            const execs = await API.getScriptExecutions(script.id, 20);
            allExecs.push(...execs.map(e => ({ ...e, script_name: script.name })));
        }
        
        allExecutions = allExecs.sort((a, b) => new Date(b.started_at) - new Date(a.started_at));
        UI.renderLogs(allExecutions);
    } catch (error) {
        console.error('Load logs error:', error);
    }
}

async function refreshLogs() {
    if (!token) return;
    try {
        const executions = await API.getAllExecutions();
        if (executions) {
            allExecutions = executions.sort((a, b) => new Date(b.started_at) - new Date(a.started_at));
            for (const exec of allExecutions) {
                const script = allScripts.find(s => s.id === exec.script_id);
                exec.script_name = script ? script.name : `Script #${exec.script_id}`;
            }
            const filter = document.getElementById('logFilter')?.value || 'all';
            UI.renderLogs(filter === 'all' ? allExecutions : allExecutions.filter(e => e.status === filter));
        }
    } catch (error) {
        console.error('Refresh logs error:', error);
    }
}

function filterLogs() {
    const filter = document.getElementById('logFilter').value;
    UI.renderLogs(filter === 'all' ? allExecutions : allExecutions.filter(e => e.status === filter));
}

async function viewLogDetails(executionId) {
    let execution = allExecutions.find(e => e.id === executionId);
    
    if (!execution) {
        for (const script of allScripts) {
            const execs = await API.getScriptExecutions(script.id, 100);
            execution = execs.find(e => e.id === executionId);
            if (execution) break;
        }
    }
    
    if (!execution) {
        showToast('Execution not found', 'error');
        return;
    }
    
    document.getElementById('logDetails').innerHTML = `
        <div class="log-detail-grid">
            <div><strong>Script ID</strong> ${execution.script_id}</div>
            <div><strong>Status</strong> <span class="status ${execution.status}">${execution.status}</span></div>
            <div><strong>Started</strong> ${formatDate(execution.started_at)}</div>
            <div><strong>Finished</strong> ${execution.finished_at ? formatDate(execution.finished_at) : '—'}</div>
            <div><strong>Duration</strong> ${formatDuration(execution.duration_ms)}</div>
        </div>
        ${execution.output ? `<div class="log-output-block"><strong>Output</strong><pre>${escapeHtml(execution.output)}</pre></div>` : ''}
        ${execution.error ? `<div class="log-error-block"><strong>Error trace</strong><pre>${escapeHtml(execution.error)}</pre></div>` : ''}
    `;
    
    UI.showModal('viewLogModal');
}

async function loadProfileStats() {
    try {
        const scripts = await API.getScripts();
        let totalExecutions = 0, successCount = 0, totalDuration = 0;
        
        for (const script of scripts) {
            const execs = await API.getScriptExecutions(script.id, 100);
            totalExecutions += execs.length;
            successCount += execs.filter(e => e.status === 'success').length;
            totalDuration += execs.reduce((sum, e) => sum + (e.duration_ms || 0), 0);
        }
        
        document.getElementById('statScripts').innerText = scripts.length;
        document.getElementById('statExecutions').innerText = totalExecutions;
        document.getElementById('statSuccessRate').innerText = totalExecutions > 0 ? Math.round((successCount / totalExecutions) * 100) + '%' : '0%';
        document.getElementById('statTotalTime').innerText = formatDuration(totalDuration);
        const usagePercent = Math.min(100, Math.round((totalExecutions / 10000) * 100));
        document.querySelector('.progress-fill').style.width = `${usagePercent}%`;
    } catch (error) {
        console.error('Stats error:', error);
    }
}

async function changePassword() {
    const oldPassword = document.getElementById('oldPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    if (!oldPassword || !newPassword) {
        showToast('Please fill all fields', 'error');
        return;
    }
    if (newPassword !== confirmPassword) {
        showToast('New passwords do not match', 'error');
        return;
    }
    
    try {
        await API.post('/auth/change-password', { old_password: oldPassword, new_password: newPassword });
        showToast('Password changed! Please login again.', 'success');
        logout();
    } catch (error) {
        showToast('Failed: ' + error.message, 'error');
    }
}

async function deleteAccount() {
    if (!confirm('⚠️ PERMANENT ACTION: This will delete your account AND all scripts. Type "DELETE" to confirm.')) return;
    const confirmation = prompt('Type DELETE to confirm');
    if (confirmation !== 'DELETE') return;
    
    try {
        await API.delete('/auth/delete-account');
        showToast('Account deleted', 'success');
        logout();
    } catch (error) {
        showToast('Delete failed: ' + error.message, 'error');
    }
}

// Modal helpers
function showCreateScriptModal() { UI.clearModalInputs(['modalScriptName', 'modalScriptCode', 'modalScriptSchedule']); UI.showModal('createScriptModal'); }
function showLoginForm() { UI.showModal('loginModal'); }
function showRegisterForm() { UI.showModal('registerModal'); }
function showChangePasswordModal() { UI.clearModalInputs(['oldPassword', 'newPassword', 'confirmPassword']); UI.showModal('changePasswordModal'); }
function closeCreateScriptModal() { UI.hideModal('createScriptModal'); }
function closeLoginModal() { UI.hideModal('loginModal'); }
function closeRegisterModal() { UI.hideModal('registerModal'); }
function closeChangePasswordModal() { UI.hideModal('changePasswordModal'); }
function closeScriptDetailModal() { UI.hideModal('scriptDetailModal'); }
function closeViewLogModal() { UI.hideModal('viewLogModal'); }

function editField(field) {
    const newValue = prompt(`Enter new ${field}:`);
    if (newValue && newValue.trim()) {
        showToast(`${field} updated to: ${newValue}`, 'success');
        if (field === 'username') document.getElementById('profileUsername').innerText = newValue;
        if (field === 'email') document.getElementById('profileEmail').innerText = newValue;
    }
}

function showUpgradeModal() { showToast('🚀 Premium plan — more features coming soon!', 'info'); }
function show2FAModal() { showToast('2FA setup would be available in next release', 'info'); }
function showSessionsModal() { showToast('Session management coming soon', 'info'); }
function showAccessLogs() { showToast('Access logs feature in development', 'info'); }
function exportData() { showToast('Preparing data export... (demo)', 'info'); setTimeout(() => showToast('Data export ready for download', 'success'), 1500); }