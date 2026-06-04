// tasks.js - Gerenciamento de Tarefas
const TasksModule = {
    render: null, // Mapeado para o objeto abaixo para compatibilidade com app.js
    tasks: [],
    
    async load() {
        const content = document.getElementById('content-area');
        content.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
        
        try {
            this.tasks = await TasksAPI.getAll();
            this.renderTasks();
            this.updateBadge();
        } catch (error) {
            content.innerHTML = '<div class="empty-state"><h3>Erro ao carregar tarefas</h3></div>';
        }
    },
    
    renderTasks() {
        const content = document.getElementById('content-area');
        
        if (this.tasks.length === 0) {
            content.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📋</div>
                    <h3>Nenhuma tarefa ainda</h3>
                    <p>Clique em "Adicionar" para criar sua primeira tarefa</p>
                </div>
            `;
            return;
        }
        
        content.innerHTML = this.tasks.map(task => `
            <div class="card ${task.is_completed ? 'completed' : ''}" style="${task.is_completed ? 'opacity: 0.6;' : ''}">
                <div class="card-header">
                    <div>
                        <div class="card-title" style="${task.is_completed ? 'text-decoration: line-through; color: var(--text-muted);' : ''}">${this.escapeHtml(task.title)}</div>
                        ${task.due_date ? `<div class="card-subtitle">📅 ${this.formatDate(task.due_date)}</div>` : ''}
                    </div>
                    <div class="card-actions">
                        ${!task.is_completed ? `<button class="btn-icon" onclick="TasksModule.complete('${task.id}')" title="Concluir">✓</button>` : ''}
                        <button class="btn-icon" onclick="TasksModule.delete('${task.id}')" title="Excluir">🗑</button>
                    </div>
                </div>
            </div>
        `).join('');
    },
    
    showAddModal() {
        const html = `
            <form id="task-form">
                <div class="form-group">
                    <label class="form-label">Título</label>
                    <input type="text" class="form-input" name="title" required>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Data de vencimento</label>
                        <input type="datetime-local" class="form-input" name="due_date">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Minutos de antecedência</label>
                        <input type="number" class="form-input" name="advance_minutes" value="5" min="1">
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn-secondary" onclick="closeModal()">Cancelar</button>
                    <button type="submit" class="btn-primary">Salvar</button>
                </div>
            </form>
        `;
        openModal('Nova Tarefa', html);
        
        document.getElementById('task-form').onsubmit = async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            
            // Format datetime-local "YYYY-MM-DDTHH:MM" to "YYYY-MM-DD HH:MM" or keep date and time separate
            let rawDueDate = formData.get('due_date');
            let dueDate = null;
            let reminderTime = null;
            
            if (rawDueDate) {
                const dt = new Date(rawDueDate);
                const year = dt.getFullYear();
                const month = String(dt.getMonth() + 1).padStart(2, '0');
                const day = String(dt.getDate()).padStart(2, '0');
                const hour = String(dt.getHours()).padStart(2, '0');
                const minute = String(dt.getMinutes()).padStart(2, '0');
                
                dueDate = `${year}-${month}-${day}`;
                reminderTime = `${hour}:${minute}`;
            }

            const data = {
                title: formData.get('title'),
                due_date: dueDate,
                reminder_time: reminderTime,
                advance_minutes: parseInt(formData.get('advance_minutes')) || 5,
            };
            
            try {
                await TasksAPI.create(data);
                closeModal();
                showToast('Tarefa criada com sucesso!');
                this.load();
            } catch (error) {
                showToast('Erro ao criar tarefa', 'error');
            }
        };
    },
    
    async complete(id) {
        try {
            await TasksAPI.complete(id);
            showToast('Tarefa concluída!');
            this.load();
        } catch (error) {
            showToast('Erro ao concluir tarefa', 'error');
        }
    },
    
    async delete(id) {
        if (!confirm('Deseja realmente excluir esta tarefa?')) return;
        
        try {
            await TasksAPI.delete(id);
            showToast('Tarefa excluída!');
            this.load();
        } catch (error) {
            showToast('Erro ao excluir tarefa', 'error');
        }
    },
    
    updateBadge() {
        const pending = this.tasks.filter(t => !t.is_completed).length;
        document.getElementById('tasks-badge').textContent = pending;
    },
    
    formatDate(dateStr) {
        if (!dateStr) return '';
        // Date str YYYY-MM-DD
        const [year, month, day] = dateStr.split('-');
        return `${day}/${month}/${year}`;
    },
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
};

TasksModule.render = TasksModule;
