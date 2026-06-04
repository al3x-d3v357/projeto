// bills.js - Gerenciamento de Contas
const BillsModule = {
    render: null,
    bills: [],
    
    async load() {
        const content = document.getElementById('content-area');
        content.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
        
        try {
            this.bills = await BillsAPI.getAll();
            this.renderBills();
        } catch (error) {
            content.innerHTML = '<div class="empty-state"><h3>Erro ao carregar contas</h3></div>';
        }
    },
    
    renderBills() {
        const content = document.getElementById('content-area');
        
        if (this.bills.length === 0) {
            content.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">💳</div>
                    <h3>Nenhuma conta cadastrada</h3>
                    <p>Adicione suas contas para não esquecer os vencimentos</p>
                </div>
            `;
            return;
        }
        
        const total = this.bills.reduce((sum, b) => sum + parseFloat(b.value || 0), 0);
        
        content.innerHTML = `
            <div class="card" style="background: linear-gradient(135deg, #ef4444, #f97316); border: none;">
                <div class="card-title" style="color: white; font-weight: 600;">💸 Total de contas</div>
                <div style="font-size: 28px; font-weight: 700; color: white; margin-top: 8px;">
                    R$ ${total.toFixed(2).replace('.', ',')}
                </div>
            </div>
            
            ${this.bills.map(bill => {
                const daysLeft = this.getDaysLeft(bill.due_date);
                const statusColor = daysLeft < 0 ? 'var(--danger)' : daysLeft <= 3 ? 'var(--warning)' : 'var(--success)';
                const statusText = daysLeft < 0 ? `Vencida há ${Math.abs(daysLeft)} dias` : daysLeft === 0 ? 'Vence hoje!' : `Vence em ${daysLeft} dias`;
                
                return `
                    <div class="card">
                        <div class="card-header">
                            <div>
                                <div class="card-title">${this.escapeHtml(bill.name)}</div>
                                <div class="card-subtitle" style="margin-top: 4px;">
                                    <span style="color: ${statusColor}; font-weight: 600;">${statusText}</span>
                                    • Vencimento: ${this.formatDate(bill.due_date)}
                                </div>
                            </div>
                            <div style="text-align: right; display: flex; flex-direction: column; align-items: flex-end; gap: 8px;">
                                <div style="font-size: 20px; font-weight: 700; color: var(--text-primary);">
                                    R$ ${parseFloat(bill.value).toFixed(2).replace('.', ',')}
                                </div>
                                <button class="btn-icon" onclick="BillsModule.delete('${bill.id}')" title="Excluir">🗑</button>
                            </div>
                        </div>
                    </div>
                `;
            }).join('')}
        `;
    },
    
    showAddModal() {
        const html = `
            <form id="bill-form">
                <div class="form-group">
                    <label class="form-label">Nome da conta</label>
                    <input type="text" class="form-input" name="name" required placeholder="Ex: Internet">
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Valor (R$)</label>
                        <input type="number" class="form-input" name="value" required min="0" step="0.01" value="0.00">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Data de vencimento</label>
                        <input type="date" class="form-input" name="due_date" required>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn-secondary" onclick="closeModal()">Cancelar</button>
                    <button type="submit" class="btn-primary">Adicionar</button>
                </div>
            </form>
        `;
        openModal('Nova Conta', html);
        
        document.getElementById('bill-form').onsubmit = async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = {
                name: formData.get('name'),
                value: parseFloat(formData.get('value')) || 0.0,
                due_date: formData.get('due_date'),
            };
            
            try {
                await BillsAPI.create(data);
                closeModal();
                showToast('Conta adicionada!');
                this.load();
            } catch (error) {
                showToast('Erro ao adicionar conta', 'error');
            }
        };
    },
    
    async delete(id) {
        if (!confirm('Deseja excluir esta conta?')) return;
        try {
            await BillsAPI.delete(id);
            showToast('Conta excluída!');
            this.load();
        } catch (error) {
            showToast('Erro ao excluir conta', 'error');
        }
    },
    
    getDaysLeft(dateStr) {
        if (!dateStr) return 0;
        const [year, month, day] = dateStr.split('-');
        const due = new Date(year, month - 1, day);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        due.setHours(0, 0, 0, 0);
        return Math.ceil((due - today) / (1000 * 60 * 60 * 24));
    },
    
    formatDate(dateStr) {
        if (!dateStr) return '';
        const [year, month, day] = dateStr.split('-');
        return `${day}/${month}/${year}`;
    },
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
};

BillsModule.render = BillsModule;
