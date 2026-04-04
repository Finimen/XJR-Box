// Глобальные переменные
let token = localStorage.getItem('token');
let currentUser = null;

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    if (token) {
        checkAuth();
    }
});

// ========== AUTH ==========

async function checkAuth() {
    try {
        const response = await fetch('/auth/me', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const user = await response.json();
            currentUser = user;
            showMainContent(user.username);
        } else {
            logout();
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        logout();
    }
}

function showLoginForm() {
    document.getElementById('loginForm').style.display = 'flex';
}

function hideLoginForm() {
    document.getElementById('loginForm').style.display = 'none';
}

function showRegisterForm() {
    document.getElementById('registerForm').style.display = 'flex';
}

function hideRegisterForm() {
    document.getElementById('registerForm').style.display = 'none';
}

async function login() {
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    
    try {
        const response = await fetch('/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        if (response.ok) {
            const data = await response.json();
            token = data.access_token;
            localStorage.setItem('token', token);
            hideLoginForm();
            await checkAuth();
        } else {
            const error = await response.json();
            alert('Login failed: ' + (error.detail || 'Unknown error'));
        }
    } catch (error) {
        alert('Login failed: ' + error.message);
    }
}

async function register() {
    const username = document.getElementById('regUsername').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;
    
    try {
        const response = await fetch('/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, email, password })
        });
        
        if (response.ok) {
            alert('Registration successful! Please login.');
            hideRegisterForm();
            showLoginForm();
        } else {
            const error = await response.json();
            alert('Registration failed: ' + (error.detail || 'Unknown error'));
        }
    } catch (error) {
        alert('Registration failed: ' + error.message);
    }
}

async function logout() {
    try {
        await fetch('/auth/logout', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
    } catch (error) {
        console.error('Logout error:', error);
    }
    
    token = null;
    currentUser = null;
    localStorage.removeItem('token');
    document.getElementById('authButtons').style.display = 'flex';
    document.getElementById('userInfo').style.display = 'none';
    document.getElementById('mainContent').style.display = 'none';
}

function showMainContent(username) {
    document.getElementById('authButtons').style.display = 'none';
    document.getElementById('userInfo').style.display = 'flex';
    document.getElementById('username').innerText = username;
    document.getElementById('mainContent').style.display = 'block';
    
    // Загружаем скрипты
    loadScripts();
}

// ========== SCRIPTS ==========

async function createScript() {
    const name = document.getElementById('scriptName').value;
    const code = document.getElementById('scriptCode').value;
    const schedule = document.getElementById('scriptSchedule').value || null;
    
    if (!name || !code) {
        alert('Name and code are required!');
        return;
    }
    
    try {
        const response = await fetch('/scripts/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ name, code, schedule })
        });
        
        if (response.ok) {
            alert('Script created!');
            document.getElementById('scriptName').value = '';
            document.getElementById('scriptCode').value = '';
            document.getElementById('scriptSchedule').value = '';
            loadScripts();
        } else {
            const error = await response.json();
            alert('Failed to create script: ' + (error.detail || 'Unknown error'));
        }
    } catch (error) {
        alert('Failed to create script: ' + error.message);
    }
}

async function loadScripts() {
    try {
        const response = await fetch('/scripts/', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const scripts = await response.json();
            displayScripts(scripts);
        }
    } catch (error) {
        console.error('Failed to load scripts:', error);
    }
}

function displayScripts(scripts) {
    const container = document.getElementById('scriptsContainer');
    
    if (scripts.length === 0) {
        container.innerHTML = '<p>No scripts yet. Create your first script!</p>';
        return;
    }
    
    container.innerHTML = scripts.map(script => `
        <div class="script-card">
            <h3>${escapeHtml(script.name)}</h3>
            <p>${script.description || 'No description'}</p>
            <p><small>Schedule: ${script.schedule || 'Manual only'}</small></p>
            <p><small>Active: ${script.is_active ? '✅' : '❌'}</small></p>
            <pre>${escapeHtml(script.code.substring(0, 200))}${script.code.length > 200 ? '...' : ''}</pre>
            <button onclick="runScript(${script.id})">▶ Run Now</button>
            <button onclick="deleteScript(${script.id})">🗑 Delete</button>
            <div id="executions-${script.id}"></div>
        </div>
    `).join('');
    
    // Загружаем историю выполнения для каждого скрипта
    scripts.forEach(script => {
        loadExecutions(script.id);
    });
}

async function runScript(scriptId) {
    try {
        const response = await fetch(`/scripts/${scriptId}/run`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            alert(`Script started! Execution ID: ${data.execution_id}`);
            // Подождать немного и обновить историю
            setTimeout(() => loadExecutions(scriptId), 1000);
        } else {
            const error = await response.json();
            alert('Failed to run script: ' + (error.detail || 'Unknown error'));
        }
    } catch (error) {
        alert('Failed to run script: ' + error.message);
    }
}

async function deleteScript(scriptId) {
    if (!confirm('Are you sure you want to delete this script?')) {
        return;
    }
    
    try {
        const response = await fetch(`/scripts/${scriptId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            alert('Script deleted!');
            loadScripts();
        } else {
            alert('Failed to delete script');
        }
    } catch (error) {
        alert('Failed to delete script: ' + error.message);
    }
}

async function loadExecutions(scriptId) {
    try {
        const response = await fetch(`/scripts/${scriptId}/executions?limit=5`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const executions = await response.json();
            displayExecutions(scriptId, executions);
        }
    } catch (error) {
        console.error('Failed to load executions:', error);
    }
}

function displayExecutions(scriptId, executions) {
    const container = document.getElementById(`executions-${scriptId}`);
    
    if (!executions || executions.length === 0) {
        container.innerHTML = '<p><small>No executions yet</small></p>';
        return;
    }
    
    container.innerHTML = `
        <div class="executions">
            <strong>Recent executions:</strong>
            ${executions.map(exec => `
                <div class="execution-item">
                    <span class="${exec.status}">${exec.status}</span>
                    - ${new Date(exec.started_at).toLocaleString()}
                    ${exec.duration_ms ? ` (${exec.duration_ms}ms)` : ''}
                </div>
            `).join('')}
        </div>
    `;
}

// Helper function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}