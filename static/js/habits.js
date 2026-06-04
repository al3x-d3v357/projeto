// habits.js - Gerenciamento de Hábitos
const HabitsModule = {
    render: null,
    habits: [],
    
    async load() {
        const content = document.getElementById('content-area');
        content.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
        
        try {
            this.habits = await HabitsAPI.getAll();
            this.renderHabits();
        } catch (error) {
            content.innerHTML = '<div class="empty-state"><h3>Erro ao carregar hábitos</h3></div>';
        }
    },
    
    renderHabits() {
        const content = document.getElementById('content-area');
        
        if (this.habits.length === 0) {
            content.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">🔄</div>
                    <h3>Nenhum hábito cadastrado</h3>
                    <p>Crie hábitos recorrentes para construir rotinas</p>
                </div>
            `;
            return;
        }
        
        content.innerHTML = this.habits.map(habit => `
            <div class="card">
                <div class="card-header">
                    <div>
                        <div class="card-title">${this.escapeHtml(habit.name)}</div>
                        <div class="card-subtitle">🔄 A cada ${habit.interval_minutes} minutos</div>
                    </div>
                    <div class="card-actions">
                        <button class="btn-icon" onclick="HabitsModule.remind('${habit.id}')" title="Lembrar agora">🔔</button>
                        <button class="btn-icon" onclick="HabitsModule.delete('${habit.id}')" title="Excluir">🗑</button>
                    </div>
                </div>
            </div>
        `).join('');
    },
    
    showAddModal() {
        const html = `
            <form id="habit-form">
                <div class="form-group">
                    <label class="form-label">Nome do hábito</label>
                    <input type="text" class="form-input" name="name" required placeholder="Ex: Beber água">
                </div>
                <div class="form-group">
                    <label class="form-label">Intervalo (minutos)</label>
                    <input type="number" class="form-input" name="interval_minutes" required min="1" value="60">
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn-secondary" onclick="closeModal()">Cancelar</button>
                    <button type="submit" class="btn-primary">Salvar</button>
                </div>
            </form>
        `;
        openModal('Novo Hábito', html);
        
        document.getElementById('habit-form').onsubmit = async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = {
                name: formData.get('name'),
                interval_minutes: parseInt(formData.get('interval_minutes')),
            };
            
            try {
                await HabitsAPI.create(data);
                closeModal();
                showToast('Hábito criado!');
                this.load();
            } catch (error) {
                showToast('Erro ao criar hábito', 'error');
            }
        };
    },
    
    async remind(id) {
        try {
            await HabitsAPI.remind(id);
            showToast('Lembrete disparado!');
        } catch (error) {
            showToast('Erro ao disparar lembrete', 'error');
        }
    },
    
    async delete(id) {
        if (!confirm('Deseja excluir este hábito?')) return;
        try {
            await HabitsAPI.delete(id);
            showToast('Hábito excluído!');
            this.load();
        } catch (error) {
            showToast('Erro ao excluir hábito', 'error');
        }
    },
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
};

HabitsModule.render = HabitsModule;
