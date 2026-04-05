// ==================== ui.js (исправленная версия) ====================
const UI = {
    renderScripts(scripts, onRun, onDelete, onDetail) {
        const container = document.getElementById('scriptsGrid');
        if (!scripts.length) {
            container.innerHTML = `<div class="empty-state">
                <span class="material-icons">inbox</span>
                <p>No scripts yet</p>
                <button class="btn-primary" onclick="showCreateScriptModal()">Create first script</button>
            </div>`;
            return;
        }
        
        container.innerHTML = scripts.map(script => `
            <div class="script-tile" data-id="${script.id}">
                <div class="script-tile-header">
                    <h3><span class="material-icons">auto_awesome</span> ${escapeHtml(script.name)}</h3>
                    <div class="script-status ${script.is_active ? 'active' : 'inactive'}"></div>
                </div>
                <div class="script-tile-code">
                    <code>${escapeHtml(script.code.substring(0, 120))}${script.code.length > 120 ? '…' : ''}</code>
                </div>
                <div class="script-tile-footer">
                    <span class="schedule-badge">⏱️ ${script.schedule || 'manual only'}</span>
                    <div class="script-actions">
                        <button class="icon-btn run" onclick="event.stopPropagation(); ${onRun.name}(${script.id})" title="Run">
                            <span class="material-icons">play_arrow</span>
                        </button>
                        <button class="icon-btn info" onclick="event.stopPropagation(); ${onDetail.name}(this, ${script.id})" title="Details">
                            <span class="material-icons">info</span>
                        </button>
                        <button class="icon-btn delete" onclick="event.stopPropagation(); ${onDelete.name}(${script.id})" title="Delete">
                            <span class="material-icons">delete</span>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    },
    
    renderScriptDetail(script, executions) {
        return `
            <div class="detail-header">
                <h3>${escapeHtml(script.name)}</h3>
                <div class="detail-meta">
                    <span>📅 Created: ${formatDate(script.created_at)}</span>
                    <span>🕒 Last run: ${script.last_run_at ? formatDate(script.last_run_at) : 'Never'}</span>
                    <span>⏲️ Schedule: ${script.schedule || 'manual'}</span>
                </div>
            </div>
            <div class="detail-code">
                <label>Source code</label>
                <pre><code>${escapeHtml(script.code)}</code></pre>
            </div>
            <div class="detail-executions">
                <label>Recent executions</label>
                ${executions.map(exec => `
                    <div class="exec-mini ${exec.status}">
                        <span>${formatDate(exec.started_at)}</span>
                        <span class="status ${exec.status}">${exec.status}</span>
                        <span>${formatDuration(exec.duration_ms)}</span>
                    </div>
                `).join('') || '<p>No executions yet</p>'}
            </div>
        `;
    },
    
    renderLogs(executions) {
        const container = document.getElementById('logsContainer');
        if (!executions.length) {
            container.innerHTML = `<div class="empty-state"><span class="material-icons">history</span><p>No executions recorded</p></div>`;
            return;
        }
        
        container.innerHTML = executions.map(exec => `
            <div class="log-item ${exec.status}" onclick="viewLogDetails(${exec.id})">
                <div class="log-header">
                    <div class="log-script-name">📜 ${escapeHtml(exec.script_name || `Script #${exec.script_id}`)}</div>
                    <div class="log-status ${exec.status}">${exec.status}</div>
                </div>
                <div class="log-time">${formatDate(exec.started_at)}</div>
                ${exec.duration_ms ? `<div class="log-duration">⏱️ ${formatDuration(exec.duration_ms)}</div>` : ''}
                ${exec.output ? `<div class="log-output-preview">📤 ${escapeHtml(exec.output.substring(0, 90))}${exec.output.length > 90 ? '…' : ''}</div>` : ''}
                ${exec.error ? `<div class="log-output-preview error">⚠️ ${escapeHtml(exec.error.substring(0, 90))}</div>` : ''}
            </div>
        `).join('');
    },
    
    renderRecentExecutions(executions) {
        const container = document.getElementById('recentExecutions');
        if (!executions.length) {
            container.innerHTML = '<div class="recent-item empty">✨ No activity yet. Run your first script!</div>';
            return;
        }
        
        container.innerHTML = executions.map(exec => `
            <div class="recent-item">
                <div class="recent-info">
                    <span class="material-icons">${exec.status === 'success' ? 'check_circle' : 'error'}</span>
                    <strong>Script #${exec.script_id}</strong>
                    <span class="status ${exec.status}">${exec.status}</span>
                </div>
                <div class="recent-time">${formatDate(exec.started_at)}</div>
            </div>
        `).join('');
    },
    
    updateDashboardStats(scriptsCount, executionsCount, successRate) {
        document.getElementById('totalScripts').innerText = scriptsCount;
        document.getElementById('totalRuns').innerText = executionsCount;
        document.getElementById('successRate').innerText = `${successRate}%`;
    },
    
    updateProfile(user) {
        document.getElementById('profileUsername').innerText = user.username;
        document.getElementById('profileEmail').innerText = user.email;
        document.getElementById('profileCreated').innerText = formatDate(user.created_at);
        document.getElementById('sidebarUsername').innerText = user.username;
        document.getElementById('dashboardUsername').innerText = user.username;
    },
    
    showModal(id) { 
        const modal = document.getElementById(id);
        if (modal) {
            modal.style.display = 'flex';
            modal.classList.add('active');
        }
    },
    hideModal(id) { 
        const modal = document.getElementById(id);
        if (modal) {
            modal.style.display = 'none';
            modal.classList.remove('active');
        }
    },
    
    clearModalInputs(ids) {
        ids.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.value = '';
        });
    }
};