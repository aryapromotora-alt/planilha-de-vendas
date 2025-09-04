// Dados iniciais e configurações
let currentUser = null;
let isAdmin = false;
let employees = [];
let spreadsheetData = {};

// Dados padrão
const defaultEmployees = [
    { name: 'Anderson', password: '123' },
    { name: 'Vitoria', password: '123' },
    { name: 'Jemima', password: '123' },
    { name: 'Maiany', password: '123' },
    { name: 'Fernanda', password: '123' },
    { name: 'Nadia', password: '123' },
    { name: 'Giovana', password: '123' }
];

const adminCredentials = { username: 'admin', password: 'admin123' };

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
});

function initializeApp() {
    // Carregar dados do localStorage ou usar dados padrão
    const savedEmployees = localStorage.getItem('employees');
    const savedSpreadsheetData = localStorage.getItem('spreadsheetData');
    
    if (savedEmployees) {
        employees = JSON.parse(savedEmployees);
    } else {
        employees = [...defaultEmployees];
        saveEmployees();
    }
    
    if (savedSpreadsheetData) {
        spreadsheetData = JSON.parse(savedSpreadsheetData);
    } else {
        initializeSpreadsheetData();
    }
}

function initializeSpreadsheetData() {
    spreadsheetData = {};
    employees.forEach(emp => {
        spreadsheetData[emp.name] = {
            monday: 0,
            tuesday: 0,
            wednesday: 0,
            thursday: 0,
            friday: 0
        };
    });
    saveSpreadsheetData();
}

function setupEventListeners() {
    // Login
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    
    // Logout
    document.getElementById('logout-btn').addEventListener('click', handleLogout);
    
    // Admin panel
    document.getElementById('admin-panel-btn').addEventListener('click', showAdminPanel);
    document.getElementById('back-to-main').addEventListener('click', hideAdminPanel);
    
    // Admin tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', switchTab);
    });
    
    // Adicionar funcionário
    document.getElementById('add-employee-form').addEventListener('submit', handleAddEmployee);
}

function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    
    // Verificar se é admin
    if (username === adminCredentials.username && password === adminCredentials.password) {
        currentUser = 'Administrador';
        isAdmin = true;
        showMainSection();
        return;
    }
    
    // Verificar funcionários
    const employee = employees.find(emp => 
        emp.name.toLowerCase() === username.toLowerCase() && emp.password === password
    );
    
    if (employee) {
        currentUser = employee.name;
        isAdmin = false;
        showMainSection();
    } else {
        showMessage('Usuário ou senha incorretos!', 'error');
    }
}

function handleLogout() {
    currentUser = null;
    isAdmin = false;
    document.getElementById('login-section').style.display = 'block';
    document.getElementById('main-section').style.display = 'none';
    document.getElementById('admin-section').style.display = 'none';
    
    // Limpar formulário de login
    document.getElementById('login-form').reset();
}

function showMainSection() {
    document.getElementById('login-section').style.display = 'none';
    document.getElementById('main-section').style.display = 'block';
    document.getElementById('admin-section').style.display = 'none';
    
    // Atualizar informações do usuário
    document.getElementById('logged-user').textContent = `Logado como: ${currentUser}`;
    
    // Mostrar botão admin se for admin
    if (isAdmin) {
        document.getElementById('admin-panel-btn').style.display = 'inline-block';
    } else {
        document.getElementById('admin-panel-btn').style.display = 'none';
    }
    
    // Renderizar planilha
    renderSpreadsheet();
}

function renderSpreadsheet() {
    const tbody = document.getElementById('employee-rows');
    tbody.innerHTML = '';
    
    employees.forEach(employee => {
        const row = createEmployeeRow(employee.name);
        tbody.appendChild(row);
    });
    
    updateTotals();
}

function createEmployeeRow(employeeName) {
    const row = document.createElement('tr');
    
    // Nome do funcionário
    const nameCell = document.createElement('td');
    nameCell.textContent = employeeName;
    nameCell.className = 'employee-name';
    row.appendChild(nameCell);
    
    // Dias da semana
    const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'];
    days.forEach(day => {
        const cell = document.createElement('td');
        const value = spreadsheetData[employeeName] ? spreadsheetData[employeeName][day] : 0;
        cell.textContent = formatCurrency(value);
        cell.className = 'editable-cell';
        cell.dataset.employee = employeeName;
        cell.dataset.day = day;
        
        // Adicionar evento de clique para edição (apenas se não for admin ou se for o próprio funcionário)
        if (isAdmin || currentUser === employeeName) {
            cell.addEventListener('click', handleCellClick);
        }
        
        row.appendChild(cell);
    });
    
    // Total semanal
    const totalCell = document.createElement('td');
    const weeklyTotal = calculateWeeklyTotal(employeeName);
    totalCell.textContent = formatCurrency(weeklyTotal);
    totalCell.className = 'total-cell';
    row.appendChild(totalCell);
    
    return row;
}

function handleCellClick(e) {
    const cell = e.target;
    const currentValue = spreadsheetData[cell.dataset.employee][cell.dataset.day];
    
    // Criar input para edição
    const input = document.createElement('input');
    input.type = 'number';
    input.step = '0.01';
    input.value = currentValue;
    input.style.width = '100%';
    input.style.textAlign = 'center';
    
    // Substituir conteúdo da célula
    cell.innerHTML = '';
    cell.appendChild(input);
    input.focus();
    input.select();
    
    // Eventos do input
    input.addEventListener('blur', () => finishEditing(cell, input));
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            finishEditing(cell, input);
        }
    });
}

function finishEditing(cell, input) {
    const newValue = parseFloat(input.value) || 0;
    const employee = cell.dataset.employee;
    const day = cell.dataset.day;
    
    // Atualizar dados
    if (!spreadsheetData[employee]) {
        spreadsheetData[employee] = {
            monday: 0, tuesday: 0, wednesday: 0, thursday: 0, friday: 0
        };
    }
    
    spreadsheetData[employee][day] = newValue;
    
    // Restaurar célula
    cell.textContent = formatCurrency(newValue);
    
    // Salvar e atualizar totais
    saveSpreadsheetData();
    updateTotals();
}

function calculateWeeklyTotal(employeeName) {
    if (!spreadsheetData[employeeName]) return 0;
    
    const data = spreadsheetData[employeeName];
    return data.monday + data.tuesday + data.wednesday + data.thursday + data.friday;
}

function updateTotals() {
    const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'];
    let weekTotal = 0;
    
    days.forEach(day => {
        let dayTotal = 0;
        employees.forEach(employee => {
            if (spreadsheetData[employee.name]) {
                dayTotal += spreadsheetData[employee.name][day];
            }
        });
        
        const dayTotalElement = document.getElementById(`${day}-total`);
        if (dayTotalElement) {
            dayTotalElement.textContent = formatCurrency(dayTotal);
        }
        
        weekTotal += dayTotal;
    });
    
    // Atualizar totais semanais individuais
    employees.forEach(employee => {
        const weeklyTotal = calculateWeeklyTotal(employee.name);
        const row = document.querySelector(`[data-employee="${employee.name}"]`)?.parentElement;
        if (row) {
            const totalCell = row.querySelector('.total-cell');
            if (totalCell) {
                totalCell.textContent = formatCurrency(weeklyTotal);
            }
        }
    });
    
    // Atualizar total geral da semana
    const weekTotalElement = document.getElementById('week-total');
    if (weekTotalElement) {
        weekTotalElement.textContent = formatCurrency(weekTotal);
    }
}

function formatCurrency(value) {
    return `R$ ${value.toFixed(2).replace('.', ',')}`;
}

// Funções de administração
function showAdminPanel() {
    document.getElementById('admin-section').style.display = 'block';
    renderEmployeeManagement();
}

function hideAdminPanel() {
    document.getElementById('admin-section').style.display = 'none';
}

function switchTab(e) {
    const targetTab = e.target.dataset.tab;
    
    // Atualizar botões
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    e.target.classList.add('active');
    
    // Atualizar conteúdo
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(targetTab).classList.add('active');
    
    if (targetTab === 'manage-employees') {
        renderEmployeeManagement();
    }
}

function renderEmployeeManagement() {
    const list = document.getElementById('employee-management-list');
    list.innerHTML = '';
    
    // Filtrar funcionários (não mostrar admin)
    const regularEmployees = employees.filter(emp => emp.name !== 'admin');
    
    regularEmployees.forEach(employee => {
        const li = document.createElement('li');
        
        const info = document.createElement('span');
        info.className = 'employee-info';
        info.textContent = employee.name;
        
        const removeBtn = document.createElement('button');
        removeBtn.textContent = 'Remover';
        removeBtn.className = 'remove-btn';
        removeBtn.addEventListener('click', () => removeEmployee(employee.name));
        
        li.appendChild(info);
        li.appendChild(removeBtn);
        list.appendChild(li);
    });
}

function handleAddEmployee(e) {
    e.preventDefault();
    
    const name = document.getElementById('new-employee-name').value.trim();
    const password = document.getElementById('new-employee-password').value;
    
    if (!name || !password) {
        showMessage('Por favor, preencha todos os campos!', 'error');
        return;
    }
    
    // Verificar se já existe
    if (employees.find(emp => emp.name.toLowerCase() === name.toLowerCase())) {
        showMessage('Funcionário já existe!', 'error');
        return;
    }
    
    // Adicionar funcionário
    employees.push({ name, password });
    
    // Inicializar dados da planilha para o novo funcionário
    spreadsheetData[name] = {
        monday: 0, tuesday: 0, wednesday: 0, thursday: 0, friday: 0
    };
    
    // Salvar dados
    saveEmployees();
    saveSpreadsheetData();
    
    // Limpar formulário
    document.getElementById('add-employee-form').reset();
    
    // Atualizar interface
    renderEmployeeManagement();
    renderSpreadsheet();
    
    showMessage('Funcionário adicionado com sucesso!', 'success');
}

function removeEmployee(employeeName) {
    if (confirm(`Tem certeza que deseja remover ${employeeName}?`)) {
        // Remover da lista de funcionários
        employees = employees.filter(emp => emp.name !== employeeName);
        
        // Remover dados da planilha
        delete spreadsheetData[employeeName];
        
        // Salvar dados
        saveEmployees();
        saveSpreadsheetData();
        
        // Atualizar interface
        renderEmployeeManagement();
        renderSpreadsheet();
        
        showMessage('Funcionário removido com sucesso!', 'success');
    }
}

// Funções de persistência
function saveEmployees() {
    localStorage.setItem('employees', JSON.stringify(employees));
}

function saveSpreadsheetData() {
    localStorage.setItem('spreadsheetData', JSON.stringify(spreadsheetData));
}

// Função para mostrar mensagens
function showMessage(text, type) {
    // Remover mensagem anterior se existir
    const existingMessage = document.querySelector('.message');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    const message = document.createElement('div');
    message.className = `message ${type}`;
    message.textContent = text;
    
    // Inserir no formulário de login ou no painel admin
    const loginForm = document.querySelector('.login-form');
    const adminPanel = document.querySelector('.admin-panel');
    
    if (document.getElementById('login-section').style.display !== 'none') {
        loginForm.insertBefore(message, loginForm.firstChild);
    } else if (document.getElementById('admin-section').style.display !== 'none') {
        adminPanel.insertBefore(message, adminPanel.firstChild);
    }
    
    // Remover mensagem após 3 segundos
    setTimeout(() => {
        if (message.parentNode) {
            message.remove();
        }
    }, 3000);
}

// Função para resetar dados (para desenvolvimento/teste)
function resetData() {
    localStorage.removeItem('employees');
    localStorage.removeItem('spreadsheetData');
    location.reload();
}

// Expor função reset para console (apenas para desenvolvimento)
window.resetData = resetData;

