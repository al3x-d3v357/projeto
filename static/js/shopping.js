// shopping.js - Lista de Compras
const ShoppingModule = {
    render: null,
    items: [],
    
    async load() {
        const content = document.getElementById('content-area');
        content.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
        
        try {
            this.items = await ShoppingAPI.getAll();
            this.renderItems();
        } catch (error) {
            content.innerHTML = '<div class="empty-state"><h3>Erro ao carregar compras</h3></div>';
        }
    },
    
    renderItems() {
        const content = document.getElementById('content-area');
        
        if (this.items.length === 0) {
            content.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">🛒</div>
                    <h3>Lista vazia</h3>
                    <p>Adicione itens para suas compras</p>
                </div>
            `;
            return;
        }
        
        const total = this.items
            .filter(i => !i.is_bought)
            .reduce((sum, i) => sum + (parseFloat(i.price) || 0) * (parseFloat(i.quantity) || 1), 0);
        
        // Ordena: não comprados primeiro
        const pending = this.items.filter(i => !i.is_bought);
        const bought = this.items.filter(i => i.is_bought);
        
        content.innerHTML = `
            <div class="card" style="background: linear-gradient(135deg, var(--accent-primary), var(--accent-hover)); border: none;">
                <div class="card-title" style="color: white; font-weight: 600;">💰 Total estimado</div>
                <div style="font-size: 28px; font-weight: 700; color: white; margin-top: 8px;">
                    R$ ${total.toFixed(2).replace('.', ',')}
                </div>
            </div>
            
            ${pending.length > 0 ? `
                <h3 style="margin: 24px 0 12px; font-size: 14px; color: var(--text-secondary);">PENDENTES (${pending.length})</h3>
                ${pending.map(item => this.renderItemCard(item)).join('')}
            ` : ''}
            
            ${bought.length > 0 ? `
                <h3 style="margin: 24px 0 12px; font-size: 14px; color: var(--text-secondary);">COMPRADOS (${bought.length})</h3>
                ${bought.map(item => this.renderItemCard(item)).join('')}
                <button class="btn-secondary" style="margin-top: 16px; width: 100%; height: 44px; display: flex; align-items: center; justify-content: center; gap: 8px;" onclick="ShoppingModule.clearBought()">
                    🗑 Limpar comprados
                </button>
            ` : ''}
        `;
    },
    
    renderItemCard(item) {
        return `
            <div class="card ${item.is_bought ? 'completed' : ''}" style="${item.is_bought ? 'opacity: 0.6;' : ''}">
                <div class="card-header">
                    <div>
                        <div class="card-title" style="${item.is_bought ? 'text-decoration: line-through; color: var(--text-muted);' : ''}">
                            ${item.is_bought ? '✅ ' : ''}${this.escapeHtml(item.item_name)}
                        </div>
                        <div class="card-subtitle">
                            Qtd: ${item.quantity} × R$ ${(item.price || 0).toFixed(2).replace('.', ',')}
                            = R$ ${((item.price || 0) * (item.quantity || 1)).toFixed(2).replace('.', ',')}
                        </div>
                    </div>
                    <div class="card-actions">
                        ${!item.is_bought ? `<button class="btn-icon" onclick="ShoppingModule.toggle('${item.id}')" title="Marcar como comprado">✓</button>` : ''}
                        <button class="btn-icon" onclick="ShoppingModule.delete('${item.id}')" title="Excluir">🗑</button>
                    </div>
                </div>
            </div>
        `;
    },
    
    showAddModal() {
        const html = `
            <form id="shopping-form">
                <div class="form-group">
                    <label class="form-label">Item</label>
                    <input type="text" class="form-input" name="item_name" required placeholder="Ex: Arroz">
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Quantidade</label>
                        <input type="number" class="form-input" name="quantity" value="1" min="0.1" step="0.1">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Preço unitário (R$)</label>
                        <input type="text" class="form-input" name="price" value="0,00">
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn-secondary" onclick="closeModal()">Cancelar</button>
                    <button type="submit" class="btn-primary">Adicionar</button>
                </div>
            </form>
        `;
        openModal('Novo Item', html);
        
        document.getElementById('shopping-form').onsubmit = async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            
            // Tratamento de preço local (0,00 -> 0.00)
            let rawPrice = formData.get('price') || '0';
            rawPrice = rawPrice.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.');
            const price = parseFloat(rawPrice) || 0.0;

            const data = {
                item_name: formData.get('item_name'),
                quantity: parseFloat(formData.get('quantity')) || 1,
                price: price,
            };
            
            try {
                await ShoppingAPI.create(data);
                closeModal();
                showToast('Item adicionado!');
                this.load();
            } catch (error) {
                showToast('Erro ao adicionar item', 'error');
            }
        };
    },
    
    async toggle(id) {
        try {
            await ShoppingAPI.update(id, {});
            this.load();
        } catch (error) {
            showToast('Erro ao atualizar item', 'error');
        }
    },
    
    async delete(id) {
        if (!confirm('Deseja excluir este item?')) return;
        try {
            await ShoppingAPI.delete(id);
            showToast('Item excluído!');
            this.load();
        } catch (error) {
            showToast('Erro ao excluir item', 'error');
        }
    },
    
    async clearBought() {
        if (!confirm('Limpar todos os itens comprados?')) return;
        try {
            await ShoppingAPI.clearBought();
            showToast('Itens comprados removidos!');
            this.load();
        } catch (error) {
            showToast('Erro ao limpar itens', 'error');
        }
    },
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
};

ShoppingModule.render = ShoppingModule;
