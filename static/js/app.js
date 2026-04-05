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
    document.getElementById(`${page}Page`).style.display = 'block';
    
    if (page === 'logs') refreshLogs();
    else if (page === 'dashboard') loadDashboard();
    else if (page === 'scripts') loadScripts();
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
        }, 5000);
        
    } catch (error) {
        console.error('Auth failed:', error);
        logout();
    }
}

async function login() {
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    
    try {
        const data = await API.login(username, password);
        API.setToken(data.access_token);
        token = data.access_token;
        UI.hideModal('loginModal');
        await checkAuth();
    } catch (error) {
        alert('Login failed: ' + error.message);
    }
}

async function register() {
    const username = document.getElementById('regUsername').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;
    
    try {
        await API.register(username, email, password);
        alert('Registration successful! Please login.');
        UI.hideModal('registerModal');
        UI.showModal('loginModal');
    } catch (error) {
        alert('Registration failed: ' + error.message);
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
        console.error('Failed to load dashboard:', error);
    }
}

async function loadScripts() {
    try {
        allScripts = await API.getScripts();
        UI.renderScripts(allScripts, runScript, deleteScript, showScriptDetail);
    } catch (error) {
        console.error('Failed to load scripts:', error);
    }
}

async function createScriptFromModal() {
    const name = document.getElementById('modalScriptName').value;
    const code = document.getElementById('modalScriptCode').value;
    const schedule = document.getElementById('modalScriptSchedule').value || null;
    
    if (!name || !code) {
        alert('Name and code are required!');
        return;
    }
    
    try {
        await API.createScript({ name, code, schedule });
        alert('Script created successfully!');
        UI.hideModal('createScriptModal');
        UI.clearModalInputs(['modalScriptName', 'modalScriptCode', 'modalScriptSchedule']);
        await Promise.all([loadScripts(), loadDashboard()]);
    } catch (error) {
        alert('Failed to create script: ' + error.message);
    }
}

async function runScript(scriptId) {
    try {
        const data = await API.runScript(scriptId);
        alert(`✅ Script started! Execution ID: ${data.execution_id}`);
        setTimeout(() => {
            loadDashboard();
            refreshLogs();
        }, 1000);
    } catch (error) {
        alert('Failed to run script: ' + error.message);
    }
}

async function deleteScript(scriptId) {
    if (!confirm('Are you sure you want to delete this script?')) return;
    
    try {
        await API.deleteScript(scriptId);
        alert('Script deleted!');
        await Promise.all([loadScripts(), loadDashboard()]);
    } catch (error) {
        alert('Failed to delete script: ' + error.message);
    }
}

async function showScriptDetail(_, scriptId) {
    const script = allScripts.find(s => s.id === scriptId);
    if (!script) return;
    
    const executions = await API.getScriptExecutions(scriptId, 5);
    
    document.getElementById('scriptDetailContent').innerHTML = `
        <div style="margin-bottom: 20px;">
            <h3>${escapeHtml(script.name)}</h3>
            <p><strong>Schedule:</strong> ${script.schedule || 'Manual only'}</p>
            <p><strong>Created:</strong> ${formatDate(script.created_at)}</p>
            <p><strong>Last run:</strong> ${script.last_run_at ? formatDate(script.last_run_at) : 'Never'}</p>
        </div>
        <div><strong>Code:</strong>
            <pre style="background:#1e1e1e;color:#d4d4d4;padding:15px;border-radius:8px;overflow-x:auto;">${escapeHtml(script.code)}</pre>
        </div>
        <div style="margin-top:20px;">
            <strong>Recent Executions:</strong>
            <div id="detailExecutions">${executions.map(exec => `
                <div style="background:#f9f9f9;padding:10px;margin-top:10px;border-radius:5px;">
                    <span class="status ${exec.status}">${exec.status}</span> - ${formatDate(exec.started_at)}
                    ${exec.duration_ms ? ` (${exec.duration_ms}ms)` : ''}
                </div>
            `).join('') || '<p>No executions yet</p>'}</div>
        </div>
    `;
    
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
        console.error('Failed to load logs:', error);
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
        console.error('Failed to refresh logs:', error);
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
        alert('Execution not found');
        return;
    }
    
    document.getElementById('logDetails').innerHTML = `
        <div><strong>Script ID:</strong> ${execution.script_id}</div>
        <div><strong>Status:</strong> <span class="status ${execution.status}">${execution.status}</span></div>
        <div><strong>Started:</strong> ${formatDate(execution.started_at)}</div>
        <div><strong>Finished:</strong> ${execution.finished_at ? formatDate(execution.finished_at) : 'N/A'}</div>
        <div><strong>Duration:</strong> ${formatDuration(execution.duration_ms)}</div>
        ${execution.output ? `<div style="margin-top:15px;"><strong>Output:</strong><pre style="background:#1e1e1e;color:#d4d4d4;padding:10px;border-radius:5px;overflow-x:auto;">${escapeHtml(execution.output)}</pre></div>` : ''}
        ${execution.error ? `<div style="margin-top:15px;"><strong>Error:</strong><pre style="background:#2d1e1e;color:#ff6b6b;padding:10px;border-radius:5px;">${escapeHtml(execution.error)}</pre></div>` : ''}
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
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

async function changePassword() {
    const oldPassword = document.getElementById('oldPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    if (!oldPassword || !newPassword) {
        alert('Please fill all fields');
        return;
    }
    
    if (newPassword !== confirmPassword) {
        alert('New passwords do not match');
        return;
    }
    
    try {
        await API.post('/auth/change-password', { old_password: oldPassword, new_password: newPassword });
        alert('Password changed successfully! Please login again.');
        logout();
    } catch (error) {
        alert('Failed to change password: ' + error.message);
    }
}

async function deleteAccount() {
    if (!confirm('⚠️ WARNING: This will permanently delete your account AND all your scripts!\n\nAre you absolutely sure?')) return;
    if (!confirm('Type "DELETE" to confirm')) return;
    
    try {
        await API.delete('/auth/delete-account');
        alert('Account deleted successfully');
        logout();
    } catch (error) {
        alert('Failed to delete account: ' + error.message);
    }
}

function showCreateScriptModal() {
    UI.clearModalInputs(['modalScriptName', 'modalScriptCode', 'modalScriptSchedule']);
    UI.showModal('createScriptModal');
}

function showLoginForm() { UI.showModal('loginModal'); }
function showRegisterForm() { UI.showModal('registerModal'); }
function showChangePasswordModal() {
    UI.clearModalInputs(['oldPassword', 'newPassword', 'confirmPassword']);
    UI.showModal('changePasswordModal');
}

function closeCreateScriptModal() { UI.hideModal('createScriptModal'); }
function closeLoginModal() { UI.hideModal('loginModal'); }
function closeRegisterModal() { UI.hideModal('registerModal'); }
function closeChangePasswordModal() { UI.hideModal('changePasswordModal'); }
function closeScriptDetailModal() { UI.hideModal('scriptDetailModal'); }
function closeViewLogModal() { UI.hideModal('viewLogModal'); }

function editField(field) {
    const newValue = prompt(`Enter new ${field}:`);
    if (newValue) {
        showToast(`${field} updated to: ${newValue} (demo)`, 'success');
        if (field === 'username') document.getElementById('profileUsername').innerText = newValue;
        if (field === 'email') document.getElementById('profileEmail').innerText = newValue;
    }
}

function showUpgradeModal() { showToast('Upgrade to Premium plan - More features coming soon!', 'info'); }
function show2FAModal() { showToast('2FA setup would be implemented here', 'info'); }
function showSessionsModal() { showToast('Active sessions management coming soon', 'info'); }
function showAccessLogs() { showToast('Access logs feature coming soon', 'info'); }
function exportData() {
    showToast('Exporting your data... (demo)', 'info');
    setTimeout(() => showToast('Data export would start here', 'success'), 1500);
}