// app.js - Navegação e controle principal
let currentTab = 'tasks';

const tabConfig = {
    tasks: {
        title: 'Tarefas',
        subtitle: 'Organize seu dia',
        render: TasksModule.render,
    },
    habits: {
        title: 'Hábitos',
        subtitle: 'Construa rotinas saudáveis',
        render: HabitsModule.render,
    },
    shopping: {
        title: 'Lista de Compras',
        subtitle: 'Controle seus gastos',
        render: ShoppingModule.render,
    },
    bills: {
        title: 'Contas a Pagar',
        subtitle: 'Nunca esqueça um vencimento',
        render: BillsModule.render,
    },
};

function switchTab(tabName) {
    currentTab = tabName;
    
    // Atualizar navegação
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.tab === tabName);
    });
    
    // Atualizar header
    const config = tabConfig[tabName];
    document.getElementById('page-title').textContent = config.title;
    document.getElementById('page-subtitle').textContent = config.subtitle;
    
    // Atualizar botão de adicionar
    const btnAdd = document.getElementById('btn-add');
    if (config.render && typeof config.render.showAddModal === 'function') {
        btnAdd.style.display = 'flex';
        btnAdd.onclick = () => config.render.showAddModal();
    } else {
        btnAdd.style.display = 'none';
    }
    
    // Renderizar conteúdo
    if (config.render && typeof config.render.load === 'function') {
        config.render.load();
    }
}

// Inicializar navegação
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => switchTab(item.dataset.tab));
});

// Modal helpers
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

// Toast notifications
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

// Iniciar com a aba de tarefas
document.addEventListener('DOMContentLoaded', () => {
    switchTab('tasks');
});
