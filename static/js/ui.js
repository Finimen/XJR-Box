const UI = {
    renderScripts(scripts, onRun, onDelete, onDetail) {
        const container = document.getElementById('scriptsGrid');
        if (!scripts.length) {
            container.innerHTML = '<div style="text-align: center; padding: 40px; color: #666;">No scripts yet. Click "New Script" to create your first automation!</div>';
            return;
        }
        
        container.innerHTML = scripts.map(script => `
            <div class="script-tile" onclick="(${onDetail})(this, ${script.id})">
                <div class="script-tile-header">
                    <h3>📜 ${escapeHtml(script.name)}</h3>
                    <div class="script-status ${script.is_active ? '' : 'inactive'}"></div>
                </div>
                <div class="script-tile-code">
                    <code>${escapeHtml(script.code.substring(0, 150))}${script.code.length > 150 ? '...' : ''}</code>
                </div>
                <div class="script-tile-footer">
                    <small>⏰ ${script.schedule || 'Manual only'}</small>
                    <div class="script-actions" onclick="event.stopPropagation()">
                        <button onclick="(${onRun})(${script.id})" style="background:#28a745;color:white;">▶ Run</button>
                        <button onclick="(${onDelete})(${script.id})" style="background:#dc3545;color:white;">🗑</button>
                    </div>
                </div>
            </div>
        `).join('');
    },
    
    renderLogs(executions) {
        const container = document.getElementById('logsContainer');
        if (!executions.length) {
            container.innerHTML = '<div style="text-align: center; padding: 40px;">No executions yet</div>';
            return;
        }
        
        container.innerHTML = executions.map(exec => `
            <div class="log-item ${exec.status}" onclick="viewLogDetails(${exec.id})">
                <div class="log-header">
                    <span class="log-script-name">📜 ${escapeHtml(exec.script_name || `Script #${exec.script_id}`)}</span>
                    <span class="log-status ${exec.status}">${exec.status}</span>
                </div>
                <div class="log-time">🕐 ${formatDate(exec.started_at)}</div>
                ${exec.duration_ms ? `<div>⏱️ Duration: ${exec.duration_ms}ms</div>` : ''}
                ${exec.output ? `<div class="log-output-preview">📤 ${escapeHtml(exec.output.substring(0, 100))}${exec.output.length > 100 ? '...' : ''}</div>` : ''}
                ${exec.error ? `<div class="log-output-preview" style="color:#dc3545;">❌ ${escapeHtml(exec.error.substring(0, 100))}</div>` : ''}
            </div>
        `).join('');
    },
    
    renderRecentExecutions(executions) {
        const container = document.getElementById('recentExecutions');
        if (!executions.length) {
            container.innerHTML = '<div class="recent-item">No executions yet</div>';
            return;
        }
        
        container.innerHTML = executions.map(exec => `
            <div class="recent-item">
                <div>
                    <strong>Script ID: ${exec.script_id}</strong>
                    <span class="status ${exec.status}"> ${exec.status}</span>
                </div>
                <div class="log-time">${formatDate(exec.started_at)}</div>
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
    
    showModal(id) { document.getElementById(id).style.display = 'flex'; },
    hideModal(id) { document.getElementById(id).style.display = 'none'; },
    
    clearModalInputs(ids) {
        ids.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.value = '';
        });
    }
};