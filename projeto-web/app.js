// ==========================================
// CONFIGURAÇÃO DO SUPABASE
// ==========================================
const SUPABASE_URL = 'https://ikknxtvmdoykppnmnryx.supabase.co';
const SUPABASE_KEY = 'sb_publishable_aA_Bm7tCXzMynYZ5u4nSjw_wjAzHt8L';

const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

// ==========================================
// ESTADO GLOBAL
// ==========================================
let currentTab = 'tasks';

const tabConfig = {
    tasks: {
        title: 'Tarefas',
        subtitle: 'Organize seu dia',
        load: loadTasks,
        add: showAddTaskModal,
    },
    habits: {
        title: 'Hábitos',
        subtitle: 'Construa rotinas saudáveis',
        load: loadHabits,
        add: showAddHabitModal,
    },
    shopping: {
        title: 'Lista de Compras',
        subtitle: 'Controle seus gastos',
        load: loadShopping,
        add: showAddShoppingModal,
    },
    bills: {
        title: 'Contas a Pagar',
        subtitle: 'Nunca esqueça um vencimento',
        load: loadBills,
        add: showAddBillModal,
    },
};

// ==========================================
// NAVEGAÇÃO
// ==========================================
function switchTab(tabName) {
    currentTab = tabName;
    
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.tab === tabName);
    });
    
    const config = tabConfig[tabName];
    document.getElementById('page-title').textContent = config.title;
    document.getElementById('page-subtitle').textContent = config.subtitle;
    document.getElementById('btn-add').onclick = config.add;
    
    config.load();
}

document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => switchTab(item.dataset.tab));
});

// ==========================================
// MODAL HELPERS
// ==========================================
function openModal(title, bodyHTML) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = bodyHTML;
    document.getElementById('modal-overlay').classList.add('active');
}

function closeModal() {
    document.getElementById('modal-overlay').classList.remove('active');
}

document.getElementById('modal-close').addEventListener('click', closeModal);
document.getElementById('modal-overlay').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) closeModal();
});

// ==========================================
// TOAST NOTIFICATIONS
// ==========================================
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ==========================================
// UTILS & TIMEZONE-SAFE DATE PARSING
// ==========================================
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}

/**
 * Parses a date string safely to prevent timezone-related off-by-one errors.
 * Treats YYYY-MM-DD as local midnight instead of UTC.
 */
function parseLocalDate(dateStr) {
    if (!dateStr) return null;
    if (dateStr.includes('T')) {
        // datetime-local: "YYYY-MM-DDTHH:mm"
        const [datePart, timePart] = dateStr.split('T');
        const [year, month, day] = datePart.split('-').map(Number);
        const [hour, minute] = timePart.split(':').map(Number);
        return new Date(year, month - 1, day, hour, minute);
    } else {
        // date-only: "YYYY-MM-DD"
        const [year, month, day] = dateStr.split('-').map(Number);
        return new Date(year, month - 1, day);
    }
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = parseLocalDate(dateStr);
    if (!date) return '';
    return date.toLocaleString('pt-BR', { 
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });
}

function getDaysLeft(dateStr) {
    if (!dateStr) return 0;
    const due = parseLocalDate(dateStr);
    if (!due) return 0;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    due.setHours(0, 0, 0, 0);
    return Math.ceil((due - today) / (1000 * 60 * 60 * 24));
}

// ==========================================
// TAREFAS
// ==========================================
async function loadTasks() {
    const content = document.getElementById('content-area');
    content.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
    
    try {
        const { data: tasks, error } = await supabase
            .from('tasks')
            .select('*')
            .order('due_date', { ascending: true });
        
        if (error) throw error;
        
        if (!tasks || tasks.length === 0) {
            content.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📋</div>
                    <h3>Nenhuma tarefa ainda</h3>
                    <p>Clique em "Adicionar" para criar sua primeira tarefa</p>
                </div>
            `;
            document.getElementById('tasks-badge').textContent = '0';
            return;
        }
        
        const pending = tasks.filter(t => !t.is_completed).length;
        document.getElementById('tasks-badge').textContent = pending;
        
        content.innerHTML = tasks.map(task => `
            <div class="card ${task.is_completed ? 'completed' : ''}">
                <div class="card-header">
                    <div>
                        <div class="card-title">${escapeHtml(task.title)}</div>
                        ${task.due_date ? `<div class="card-subtitle">📅 ${formatDate(task.due_date)}</div>` : ''}
                    </div>
                    <div class="card-actions">
                        ${!task.is_completed ? `<button class="btn-icon" onclick="completeTask(${task.id})" title="Concluir">✓</button>` : ''}
                        <button class="btn-icon" onclick="deleteTask(${task.id})" title="Excluir">🗑</button>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (error) {
        content.innerHTML = `<div class="empty-state"><h3>Erro ao carregar: ${error.message}</h3></div>`;
    }
}

function showAddTaskModal() {
    const html = `
        <form id="task-form">
            <div class="form-group">
                <label class="form-label">Título</label>
                <input type="text" class="form-input" name="title" required placeholder="Ex: Estudar inglês">
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label class="form-label">Data de vencimento</label>
                    <input type="datetime-local" class="form-input" name="due_date">
                </div>
                <div class="form-group">
                    <label class="form-label">Lembrete (Minutos antes)</label>
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
        const data = {
            title: formData.get('title'),
            due_date: formData.get('due_date') || null,
            advance_minutes: parseInt(formData.get('advance_minutes')) || 5,
            is_completed: false,
        };
        
        try {
            const { error } = await supabase.from('tasks').insert([data]);
            if (error) throw error;
            closeModal();
            showToast('Tarefa criada com sucesso!');
            loadTasks();
        } catch (error) {
            showToast('Erro ao criar tarefa', 'error');
        }
    };
}

async function completeTask(id) {
    try {
        const { error } = await supabase.from('tasks').update({ is_completed: true }).eq('id', id);
        if (error) throw error;
        showToast('Tarefa concluída!');
        loadTasks();
    } catch (error) {
        showToast('Erro ao concluir tarefa', 'error');
    }
}

async function deleteTask(id) {
    if (!confirm('Deseja realmente excluir esta tarefa?')) return;
    try {
        const { error } = await supabase.from('tasks').delete().eq('id', id);
        if (error) throw error;
        showToast('Tarefa excluída!');
        loadTasks();
    } catch (error) {
        showToast('Erro ao excluir tarefa', 'error');
    }
}

// ==========================================
// HÁBITOS
// ==========================================
async function loadHabits() {
    const content = document.getElementById('content-area');
    content.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
    
    try {
        const { data: habits, error } = await supabase.from('habits').select('*');
        if (error) throw error;
        
        if (!habits || habits.length === 0) {
            content.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">🔄</div>
                    <h3>Nenhum hábito cadastrado</h3>
                    <p>Crie hábitos recorrentes para construir rotinas</p>
                </div>
            `;
            return;
        }
        
        content.innerHTML = habits.map(habit => `
            <div class="card">
                <div class="card-header">
                    <div>
                        <div class="card-title">${escapeHtml(habit.name)}</div>
                        <div class="card-subtitle">⏱️ A cada ${habit.interval_minutes} minutos</div>
                    </div>
                    <div class="card-actions">
                        <button class="btn-icon" onclick="remindHabit(${habit.id})" title="Lembrar agora">🔔</button>
                        <button class="btn-icon" onclick="deleteHabit(${habit.id})" title="Excluir">🗑</button>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (error) {
        content.innerHTML = `<div class="empty-state"><h3>Erro ao carregar: ${error.message}</h3></div>`;
    }
}

function showAddHabitModal() {
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
            const { error } = await supabase.from('habits').insert([data]);
            if (error) throw error;
            closeModal();
            showToast('Hábito criado com sucesso!');
            loadHabits();
        } catch (error) {
            showToast('Erro ao criar hábito', 'error');
        }
    };
}

async function remindHabit(id) {
    showToast('Lembrete de hábito disparado!');
}

async function deleteHabit(id) {
    if (!confirm('Deseja excluir este hábito?')) return;
    try {
        const { error } = await supabase.from('habits').delete().eq('id', id);
        if (error) throw error;
        showToast('Hábito excluído!');
        loadHabits();
    } catch (error) {
        showToast('Erro ao excluir hábito', 'error');
    }
}

// ==========================================
// LISTA DE COMPRAS
// ==========================================
async function loadShopping() {
    const content = document.getElementById('content-area');
    content.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
    
    try {
        const { data: items, error } = await supabase.from('shopping_list').select('*');
        if (error) throw error;
        
        if (!items || items.length === 0) {
            content.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">🛒</div>
                    <h3>Lista vazia</h3>
                    <p>Adicione itens para suas compras</p>
                </div>
            `;
            return;
        }
        
        const total = items
            .filter(i => !i.is_bought)
            .reduce((sum, i) => sum + (parseFloat(i.price) || 0) * (parseFloat(i.quantity) || 1), 0);
        
        const pending = items.filter(i => !i.is_bought);
        const bought = items.filter(i => i.is_bought);
        
        content.innerHTML = `
            <div class="card" style="background: linear-gradient(135deg, var(--accent-primary), var(--accent-hover)); border: none;">
                <div class="card-title" style="color: var(--bg-primary);">💰 Total estimado</div>
                <div style="font-size: 28px; font-weight: 700; color: var(--bg-primary); margin-top: 8px;">
                    R$ ${total.toFixed(2).replace('.', ',')}
                </div>
            </div>
            
            ${pending.length > 0 ? `
                <h3 style="margin: 24px 0 12px; font-size: 14px; color: var(--text-muted);">PENDENTES (${pending.length})</h3>
                ${pending.map(item => renderItemCard(item)).join('')}
            ` : ''}
            
            ${bought.length > 0 ? `
                <h3 style="margin: 24px 0 12px; font-size: 14px; color: var(--text-muted);">COMPRADOS (${bought.length})</h3>
                ${bought.map(item => renderItemCard(item)).join('')}
                <button class="btn-secondary" style="margin-top: 16px; width: 100%; height: 44px; display: flex; align-items: center; justify-content: center; gap: 8px;" onclick="clearBought()">
                    🗑 Limpar comprados
                </button>
            ` : ''}
        `;
    } catch (error) {
        content.innerHTML = `<div class="empty-state"><h3>Erro ao carregar: ${error.message}</h3></div>`;
    }
}

function renderItemCard(item) {
    return `
        <div class="card ${item.is_bought ? 'completed' : ''}">
            <div class="card-header">
                <div>
                    <div class="card-title" style="${item.is_bought ? 'text-decoration: line-through;' : ''}">
                        ${item.is_bought ? '✅ ' : ''}${escapeHtml(item.item_name)}
                    </div>
                    <div class="card-subtitle">
                        Qtd: ${item.quantity} × R$ ${(item.price || 0).toFixed(2).replace('.', ',')}
                        = R$ ${((item.price || 0) * (item.quantity || 1)).toFixed(2).replace('.', ',')}
                    </div>
                </div>
                <div class="card-actions">
                    ${!item.is_bought ? `<button class="btn-icon" onclick="toggleItem(${item.id})" title="Marcar como comprado">✓</button>` : ''}
                    <button class="btn-icon" onclick="deleteItem(${item.id})" title="Excluir">🗑</button>
                </div>
            </div>
        </div>
    `;
}

function showAddShoppingModal() {
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
        
        let rawPrice = formData.get('price') || '0';
        rawPrice = rawPrice.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.');
        const price = parseFloat(rawPrice) || 0.0;
        
        const data = {
            item_name: formData.get('item_name'),
            quantity: parseFloat(formData.get('quantity')) || 1,
            price: price,
            is_bought: false,
        };
        
        try {
            const { error } = await supabase.from('shopping_list').insert([data]);
            if (error) throw error;
            closeModal();
            showToast('Item adicionado!');
            loadShopping();
        } catch (error) {
            showToast('Erro ao adicionar item', 'error');
        }
    };
}

async function toggleItem(id) {
    try {
        const { data: item, error: fetchError } = await supabase.from('shopping_list').select('*').eq('id', id).single();
        if (fetchError) throw fetchError;
        
        const { error } = await supabase.from('shopping_list').update({ is_bought: !item.is_bought }).eq('id', id);
        if (error) throw error;
        loadShopping();
    } catch (error) {
        showToast('Erro ao atualizar item', 'error');
    }
}

async function deleteItem(id) {
    if (!confirm('Deseja excluir este item?')) return;
    try {
        const { error } = await supabase.from('shopping_list').delete().eq('id', id);
        if (error) throw error;
        showToast('Item excluído!');
        loadShopping();
    } catch (error) {
        showToast('Erro ao excluir item', 'error');
    }
}

async function clearBought() {
    if (!confirm('Limpar todos os itens comprados?')) return;
    try {
        const { error } = await supabase.from('shopping_list').delete().eq('is_bought', true);
        if (error) throw error;
        showToast('Itens comprados removidos!');
        loadShopping();
    } catch (error) {
        showToast('Erro ao limpar itens', 'error');
    }
}

// ==========================================
// CONTAS
// ==========================================
async function loadBills() {
    const content = document.getElementById('content-area');
    content.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
    
    try {
        const { data: bills, error } = await supabase.from('bills').select('*').order('due_date', { ascending: true });
        if (error) throw error;
        
        if (!bills || bills.length === 0) {
            content.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">💸</div>
                    <h3>Nenhuma conta cadastrada</h3>
                    <p>Adicione suas contas para não esquecer os vencimentos</p>
                </div>
            `;
            return;
        }
        
        const total = bills.reduce((sum, b) => sum + parseFloat(b.value || 0), 0);
        
        content.innerHTML = `
            <div class="card" style="background: linear-gradient(135deg, #ef4444, #f97316); border: none;">
                <div class="card-title" style="color: white; font-weight: 600;">💸 Total de contas</div>
                <div style="font-size: 28px; font-weight: 700; color: white; margin-top: 8px;">
                    R$ ${total.toFixed(2).replace('.', ',')}
                </div>
            </div>
            
            ${bills.map(bill => {
                const daysLeft = getDaysLeft(bill.due_date);
                const statusColor = daysLeft < 0 ? 'var(--danger)' : daysLeft <= 3 ? 'var(--warning)' : 'var(--success)';
                const statusText = daysLeft < 0 ? `Vencida há ${Math.abs(daysLeft)} dias` : daysLeft === 0 ? 'Vence hoje!' : `Vence em ${daysLeft} dias`;
                
                return `
                    <div class="card">
                        <div class="card-header">
                            <div>
                                <div class="card-title">${escapeHtml(bill.name)}</div>
                                <div class="card-subtitle" style="margin-top: 4px;">
                                    <span style="color: ${statusColor}; font-weight: 600;">${statusText}</span>
                                    • Vencimento: ${bill.due_date ? bill.due_date.split('-').reverse().join('/') : ''}
                                </div>
                            </div>
                            <div style="text-align: right; display: flex; flex-direction: column; align-items: flex-end; gap: 8px;">
                                <div style="font-size: 20px; font-weight: 700; color: var(--text-primary);">
                                    R$ ${parseFloat(bill.value).toFixed(2).replace('.', ',')}
                                </div>
                                <button class="btn-icon" onclick="deleteBill(${bill.id})" title="Excluir">🗑</button>
                            </div>
                        </div>
                    </div>
                `;
            }).join('')}
        `;
    } catch (error) {
        content.innerHTML = `<div class="empty-state"><h3>Erro ao carregar: ${error.message}</h3></div>`;
    }
}

function showAddBillModal() {
    const html = `
        <form id="bill-form">
            <div class="form-group">
                <label class="form-label">Nome da conta</label>
                <input type="text" class="form-input" name="name" required placeholder="Ex: Aluguel">
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
            const { error } = await supabase.from('bills').insert([data]);
            if (error) throw error;
            closeModal();
            showToast('Conta adicionada com sucesso!');
            loadBills();
        } catch (error) {
            showToast('Erro ao adicionar conta', 'error');
        }
    };
}

async function deleteBill(id) {
    if (!confirm('Deseja excluir esta conta?')) return;
    try {
        const { error } = await supabase.from('bills').delete().eq('id', id);
        if (error) throw error;
        showToast('Conta excluída!');
        loadBills();
    } catch (error) {
        showToast('Erro ao excluir conta', 'error');
    }
}

// ==========================================
// INICIALIZAÇÃO
// ==========================================
switchTab('tasks');
