// api.js - Funções de comunicação com o backend Flask
const API_BASE = '';

async function apiRequest(endpoint, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
        },
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        
        if (!response.ok) {
            throw new Error(`Erro ${response.status}: ${response.statusText}`);
        }
        
        if (response.status === 204) return null;
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Tarefas
const TasksAPI = {
    getAll: () => apiRequest('/api/tasks'),
    create: (data) => apiRequest('/api/tasks', 'POST', data),
    update: (id, data) => apiRequest(`/api/tasks/${id}`, 'PUT', data),
    delete: (id) => apiRequest(`/api/tasks/${id}`, 'DELETE'),
    complete: (id) => apiRequest(`/api/tasks/${id}/complete`, 'POST'),
};

// Hábitos
const HabitsAPI = {
    getAll: () => apiRequest('/api/habits'),
    create: (data) => apiRequest('/api/habits', 'POST', data),
    delete: (id) => apiRequest(`/api/habits/${id}`, 'DELETE'),
    remind: (id) => apiRequest(`/api/habits/${id}/remind`, 'POST'),
};

// Compras
const ShoppingAPI = {
    getAll: () => apiRequest('/api/shopping'),
    create: (data) => apiRequest('/api/shopping', 'POST', data),
    update: (id, data) => apiRequest(`/api/shopping/${id}`, 'PUT', data),
    delete: (id) => apiRequest(`/api/shopping/${id}`, 'DELETE'),
    clearBought: () => apiRequest('/api/shopping/clear-bought', 'POST'),
};

// Contas
const BillsAPI = {
    getAll: () => apiRequest('/api/bills'),
    create: (data) => apiRequest('/api/bills', 'POST', data),
    delete: (id) => apiRequest(`/api/bills/${id}`, 'DELETE'),
};
