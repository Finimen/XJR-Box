const API = {
    token: localStorage.getItem('token'),
    
    setToken(token) {
        this.token = token;
        if (token) localStorage.setItem('token', token);
        else localStorage.removeItem('token');
    },
    
    async request(url, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        
        const response = await fetch(url, { ...options, headers });
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }
        return response.json();
    },
    
    get(url) { return this.request(url); },
    post(url, data) { return this.request(url, { method: 'POST', body: JSON.stringify(data) }); },
    put(url, data) { return this.request(url, { method: 'PUT', body: JSON.stringify(data) }); },
    delete(url) { return this.request(url, { method: 'DELETE' }); },
    
    login(username, password) { return this.post('/auth/login', { username, password }); },
    register(username, email, password) { return this.post('/auth/register', { username, email, password }); },
    getMe() { return this.get('/auth/me'); },
    logout() { return this.post('/auth/logout', {}).catch(() => ({})); },
    
    getScripts() { return this.get('/scripts/'); },
    createScript(data) { return this.post('/scripts/', data); },
    deleteScript(id) { return this.delete(`/scripts/${id}`); },
    runScript(id) { return this.post(`/scripts/${id}/run`, {}); },
    getScriptExecutions(id, limit = 50) { return this.get(`/scripts/${id}/executions?limit=${limit}`); },
    getAllExecutions() { return this.get('/scripts/executions/all').catch(() => null); }
};