// Dados iniciais e configurações
let currentUser = null;
let isAdmin = false;
let employees = []; // Agora conterá objetos de usuário do banco de dados
let spreadsheetDataPortabilidade = {};
let spreadsheetDataNovo = {};
let currentSheet = null; // 'portabilidade' ou 'novo'

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
});

async function initializeApp() {
    // 🔑 PRIMEIRO: Carregar dados do servidor (sempre)
    try {
        // Carrega dados de ambas as planilhas
        const [dataPort, dataNovo] = await Promise.all([
            fetch('/api/data?type=portabilidade', { credentials: 'include' }).then(r => r.json()),
            fetch('/api/data?type=novo', { credentials: 'include' }).then(r => r.json())
        ]);
        
        employees = dataPort.employees || dataNovo.employees || [];
        
        spreadsheetDataPortabilidade = dataPort.spreadsheetData || {};
        spreadsheetDataNovo = dataNovo.spreadsheetData || {};
        
        // Inicializa dados ausentes
        employees.forEach(emp => {
            const username = emp.username;
            if (!spreadsheetDataPortabilidade[username]) {
                spreadsheetDataPortabilidade[username] = { monday: 0, tuesday: 0, wednesday: 0, thursday: 0, friday: 0 };
            }
            if (!spreadsheetDataNovo[username]) {
                spreadsheetDataNovo[username] = { monday: 0, tuesday: 0, wednesday: 0, thursday: 0, friday: 0 };
            }
        });
    } catch (error) {
        console.error('Erro ao carregar dados do servidor:', error);
        employees = [];
        spreadsheetDataPortabilidade = {};
        spreadsheetDataNovo = {};
    }

    // 🔑 DEPOIS: Verificar sessão para definir permissões
    try {
        const sessionResponse = await fetch('/api/check-session', {
            credentials: 'include'
        });
        if (sessionResponse.ok) {
            const sessionData = await sessionResponse.json();
            if (sessionData.logged_in) {
                currentUser = sessionData.user;
                isAdmin = sessionData.is_admin;
                showDashboard(); // Mostra o dashboard após login
                return;
            }
        }
    } catch (error) {
        console.error('Erro ao verificar sessão:', error);
    }

    // Se não estiver logado, mostra login
    document.getElementById('login-section').style.display = 'flex';
}

function getCurrentSpreadsheetData() {
    return currentSheet === 'novo' ? spreadsheetDataNovo : spreadsheetDataPortabilidade;
}

function setCurrentSpreadsheetData(data) {
    if (currentSheet === 'novo') {
        spreadsheetDataNovo = data;
    } else {
        spreadsheetDataPortabilidade = data;
    }
}

async function saveCellToServer(employeeName, day, value, sheetType) {
    try {
        const dataToSave = {
            employee_name: employeeName,
            day: day,
            value: value,
            sheet_type: sheetType
        };
        
        const response = await fetch(\'/api/data/cell\', {
            method: \'POST\',
            headers: {
                \'Content-Type\': \'application/json\',
            },
            body: JSON.stringify(dataToSave),
            credentials: \'include\'
        });
        
        if (!response.ok) {
            throw new Error(\'Erro ao salvar célula no servidor\');
        }
        
        return true;
    } catch (error) {
        console.error(\'Erro ao salvar célula:\', error);
        showMessage(\'Erro ao salvar célula no servidor!\', \'error\');
        return false;
    }
}

async function saveDataToServer() {
    // Esta função ainda é usada para salvamento completo (ex: ao adicionar/remover vendedor)
    try {
        const dataToSave = {
            sheet_type: currentSheet,
            spreadsheetData: getCurrentSpreadsheetData()
        };
        
        const response = await fetch(\'/api/data\', {
            method: \'POST\',
            headers: {
                \'Content-Type\': \'application/json\',
            },
            body: JSON.stringify(dataToSave),
            credentials: \'include\'
        });
        
        if (!response.ok) {
            throw new Error(\'Erro ao salvar dados completos no servidor\');
        }
        
        return true;
    } catch (error) {
        console.error(\'Erro ao salvar dados completos:\', error);
        showMessage(\'Erro ao salvar dados completos no servidor!\', \'error\');
        return false;
    }
}

function setupEventListeners() {
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    
    // Dashboard buttons
    document.getElementById('btn-portabilidade')?.addEventListener('click', () => showSheet('portabilidade'));
    document.getElementById('btn-novo')?.addEventListener('click', () => showSheet('novo'));
    
    // Logout buttons
    document.getElementById('logout-btn')?.addEventListener('click', handleLogout);
    document.getElementById('logout-btn-novo')?.addEventListener('click', handleLogout);
    
    // Back to dashboard
    document.getElementById('back-to-dashboard-from-port')?.addEventListener('click', showDashboard);
    document.getElementById('back-to-dashboard-from-novo')?.addEventListener('click', showDashboard);
    
    // Admin panel
    document.getElementById('admin-panel-btn')?.addEventListener('click', showAdminPanel);
    document.getElementById('admin-panel-btn-novo')?.addEventListener('click', showAdminPanel);
    document.getElementById('back-to-main')?.addEventListener('click', () => {
        if (currentSheet === 'novo') {
            showSheet('novo');
        } else {
            showSheet('portabilidade');
        }
    });
    
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', switchTab);
    });
    
    document.getElementById('add-employee-form')?.addEventListener('submit', handleAddEmployee);
}

async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    
    if (!username || !password) {
        showMessage('Por favor, preencha todos os campos!', 'error');
        return;
    }

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
            credentials: 'include'
        });

        const data = await response.json();

        if (data.success) {
            currentUser = data.user;
            isAdmin = data.is_admin;
            showDashboard(); // Mostra o dashboard em vez da planilha direta
        } else {
            showMessage(data.message || 'Erro no login', 'error');
        }
    } catch (error) {
        console.error('Erro no login:', error);
        showMessage('Erro de conexão. Tente novamente.', 'error');
    }
}

async function handleLogout() {
    try {
        await fetch('/api/logout', {
            method: 'POST',
            credentials: 'include'
        });
    } catch (error) {
        console.error('Erro no logout:', error);
    }
    
    currentUser = null;
    isAdmin = false;
    currentSheet = null;
    document.getElementById('login-section').style.display = 'flex';
    document.getElementById('dashboard-section').style.display = 'none';
    document.getElementById('main-section').style.display = 'none';
    document.getElementById('novo-section').style.display = 'none';
    document.getElementById('admin-section').style.display = 'none';
    document.getElementById('login-form').reset();
}

function showDashboard() {
    document.getElementById('login-section').style.display = 'none';
    document.getElementById('dashboard-section').style.display = 'flex';
    document.getElementById('main-section').style.display = 'none';
    document.getElementById('novo-section').style.display = 'none';
    document.getElementById('admin-section').style.display = 'none';
}

function showSheet(sheetType) {
    currentSheet = sheetType;
    document.getElementById('dashboard-section').style.display = 'none';
    document.getElementById('admin-section').style.display = 'none';
    
    if (sheetType === 'novo') {
        document.getElementById('novo-section').style.display = 'block';
        document.getElementById('logged-user-novo').textContent = `Logado como: ${currentUser}`;
        if (isAdmin) {
            document.getElementById('admin-panel-btn-novo').style.display = 'inline-block';
        } else {
            document.getElementById('admin-panel-btn-novo').style.display = 'none';
        }
        renderSpreadsheetNovo();
    } else {
        document.getElementById('main-section').style.display = 'block';
        document.getElementById('logged-user').textContent = `Logado como: ${currentUser}`;
        if (isAdmin) {
            document.getElementById('admin-panel-btn').style.display = 'inline-block';
        } else {
            document.getElementById('admin-panel-btn').style.display = 'none';
        }
        renderSpreadsheet();
    }
}

function renderSpreadsheet() {
    const tbody = document.getElementById('employee-rows');
    if (!tbody) return;
    tbody.innerHTML = '';
    
    employees.forEach(employee => {
        const row = createEmployeeRow(employee.username, 'portabilidade');
        tbody.appendChild(row);
    });
    
    updateTotals('portabilidade');
}

function renderSpreadsheetNovo() {
    const tbody = document.getElementById('employee-rows-novo');
    if (!tbody) return;
    tbody.innerHTML = '';
    
    employees.forEach(employee => {
        const row = createEmployeeRow(employee.username, 'novo');
        tbody.appendChild(row);
    });
    
    updateTotals('novo');
}

function createEmployeeRow(employeeName, sheetType) {
    const row = document.createElement('tr');
    
    const nameCell = document.createElement('td');
    nameCell.textContent = employeeName;
    nameCell.className = 'employee-name';
    row.appendChild(nameCell);
    
    const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'];
    const data = sheetType === 'novo' ? spreadsheetDataNovo : spreadsheetDataPortabilidade;
    
    days.forEach(day => {
        const cell = document.createElement('td');
        const value = data[employeeName] ? data[employeeName][day] : 0;
        cell.textContent = formatCurrency(value);
        cell.className = 'editable-cell';
        cell.dataset.employee = employeeName;
        cell.dataset.day = day;
        cell.dataset.sheet = sheetType;
        
        if (isAdmin || currentUser === employeeName) {
            cell.addEventListener('click', handleCellClick);
        }
        
        row.appendChild(cell);
    });
    
    const totalCell = document.createElement('td');
    const weeklyTotal = calculateWeeklyTotal(employeeName, sheetType);
    totalCell.textContent = formatCurrency(weeklyTotal);
    totalCell.className = 'total-cell';
    row.appendChild(totalCell);
    
    return row;
}

function handleCellClick(e) {
    const cell = e.target;
    const sheetType = cell.dataset.sheet;
    const data = sheetType === 'novo' ? spreadsheetDataNovo : spreadsheetDataPortabilidade;
    const currentValue = data[cell.dataset.employee][cell.dataset.day];
    
    const input = document.createElement('input');
    input.type = 'number';
    input.step = '0.01';
    input.value = currentValue;
    input.style.width = '100%';
    input.style.textAlign = 'center';
    
    cell.innerHTML = '';
    cell.appendChild(input);
    input.focus();
    input.select();
    
    input.addEventListener('blur', () => finishEditing(cell, input, sheetType));
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            finishEditing(cell, input, sheetType);
        }
    });
}

async function finishEditing(cell, input, sheetType) {
    const newValue = parseFloat(input.value) || 0;
    const employee = cell.dataset.employee;
    const day = cell.dataset.day;
    
    let data = sheetType === 'novo' ? spreadsheetDataNovo : spreadsheetDataPortabilidade;
    if (!data[employee]) {
        data[employee] = { monday: 0, tuesday: 0, wednesday: 0, thursday: 0, friday: 0 };
    }
    
    data[employee][day] = newValue;
    cell.textContent = formatCurrency(newValue);
    
    // Atualiza o estado global
    if (sheetType === 'novo') {
        spreadsheetDataNovo = data;
    } else {
        spreadsheetDataPortabilidade = data;
    }
    
    // Salva a célula individualmente no servidor
    await saveCellToServer(employee, day, newValue, sheetType);
    
    updateTotals(sheetType);
}

function calculateWeeklyTotal(employeeName, sheetType) {
    const data = sheetType === 'novo' ? spreadsheetDataNovo : spreadsheetDataPortabilidade;
    if (!data[employeeName]) return 0;
    const d = data[employeeName];
    return d.monday + d.tuesday + d.wednesday + d.thursday + d.friday;
}

function updateTotals(sheetType) {
    const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'];
    let weekTotal = 0;
    const data = sheetType === 'novo' ? spreadsheetDataNovo : spreadsheetDataPortabilidade;
    
    days.forEach(day => {
        let dayTotal = 0;
        employees.forEach(employee => {
            if (data[employee.username]) {
                dayTotal += data[employee.username][day];
            }
        });
        const dayTotalElement = document.getElementById(`${day}-total${sheetType === 'novo' ? '-novo' : ''}`);
        if (dayTotalElement) {
            dayTotalElement.textContent = formatCurrency(dayTotal);
        }
        weekTotal += dayTotal;
    });
    
    employees.forEach(employee => {
        const weeklyTotal = calculateWeeklyTotal(employee.username, sheetType);
        const selector = sheetType === 'novo' 
            ? `[data-employee="${employee.username}"][data-sheet="novo"]` 
            : `[data-employee="${employee.username}"]`;
        const row = document.querySelector(selector)?.parentElement;
        if (row) {
            const totalCell = row.querySelector('.total-cell');
            if (totalCell) {
                totalCell.textContent = formatCurrency(weeklyTotal);
            }
        }
    });
    
    const weekTotalElement = document.getElementById(`week-total${sheetType === 'novo' ? '-novo' : ''}`);
    if (weekTotalElement) {
        weekTotalElement.textContent = formatCurrency(weekTotal);
    }
}

function formatCurrency(value) {
    return "R$ " + parseFloat(value).toLocaleString("pt-BR", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// ====== Funções de Admin (sem alterações) ======
async function showAdminPanel() {
    await loadEmployeesForAdmin();
    document.getElementById('admin-section').style.display = 'block';
}

function hideAdminPanel() {
    document.getElementById('admin-section').style.display = 'none';
}

function switchTab(e) {
    const targetTab = e.target.dataset.tab;
    
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    e.target.classList.add('active');
    
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(targetTab).classList.add('active');
    
    if (targetTab === 'manage-employees') {
        renderEmployeeManagement();
    }
}

let adminEmployees = [];

async function loadEmployeesForAdmin() {
    try {
        const response = await fetch('/api/users', { credentials: 'include' });
        if (response.ok) {
            adminEmployees = await response.json();
            adminEmployees = adminEmployees.filter(emp => emp.role === 'user');
        } else {
            console.error('Erro ao carregar usuários para o admin:', response.statusText);
            adminEmployees = [];
        }
    } catch (error) {
        console.error('Erro na requisição de usuários para o admin:', error);
        adminEmployees = [];
    }
}

function renderEmployeeManagement() {
    const list = document.getElementById('employee-management-list');
    if (!list) return;
    list.innerHTML = '';
    
    adminEmployees.forEach(employee => {
        const li = document.createElement("li");
        const info = document.createElement("span");
        info.className = "employee-info";
        info.textContent = employee.username;
        
        const actionsDiv = document.createElement("div");
        actionsDiv.className = "employee-actions";

        const changePasswordBtn = document.createElement("button");
        changePasswordBtn.textContent = "Alterar Senha";
        changePasswordBtn.className = "change-password-btn";
        changePasswordBtn.addEventListener("click", () => handleChangePassword(employee.username));
        actionsDiv.appendChild(changePasswordBtn);

        const removeBtn = document.createElement("button");
        removeBtn.textContent = "Remover";
        removeBtn.className = "remove-btn";
        removeBtn.addEventListener("click", () => removeEmployee(employee.id, employee.username));
        actionsDiv.appendChild(removeBtn);
        
        li.appendChild(info);
        li.appendChild(actionsDiv);
        list.appendChild(li);
    });
}

async function handleAddEmployee(e) {
    e.preventDefault();
    
    const name = document.getElementById('new-employee-name')?.value.trim();
    const password = document.getElementById('new-employee-password')?.value;
    const email = document.getElementById('new-employee-email')?.value.trim();
    
    if (!name || !password) {
        showMessage('Por favor, preencha o nome de usuário e a senha!', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/users', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username: name, password: password, email: email, role: 'user' }),
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Não é mais necessário recarregar tudo, apenas atualizar a exibição
            // O initializeApp() já é chamado no início para carregar o estado inicial.
            // A adição de um novo funcionário não deve apagar os dados existentes.
            // Apenas recarregar os dados do servidor para garantir que o novo funcionário apareça
            // e, em seguida, renderizar as planilhas novamente.
            await initializeApp();
            renderEmployeeManagement();
            if (currentSheet) {
                showSheet(currentSheet); // Atualiza a planilha ativa
            }
            document.getElementById('add-employee-form').reset();
            showMessage('Funcionário adicionado com sucesso!', 'success');
        } else {
            showMessage(data.message || 'Erro ao adicionar funcionário!', 'error');
        }
    } catch (error) {
        console.error('Erro ao adicionar funcionário:', error);
        showMessage('Erro de conexão ao adicionar funcionário.', 'error');
    }
}

async function removeEmployee(employeeId, employeeName) {
    if (confirm(`Tem certeza que deseja remover ${employeeName}? Esta ação também removerá todos os dados de vendas associados.`)) {
        try {
            const response = await fetch(`/api/users/${employeeId}`, {
                method: 'DELETE',
                credentials: 'include'
            });
            
            if (response.ok) {
            // Não é mais necessário recarregar tudo, apenas atualizar a exibição
            // A remoção de um funcionário não deve apagar os dados existentes.
            // Apenas recarregar os dados do servidor para garantir que o funcionário removido desapareça
            // e, em seguida, renderizar as planilhas novamente.
            await initializeApp();
            renderEmployeeManagement();
            if (currentSheet) {
                showSheet(currentSheet); // Atualiza a planilha ativa
            }
                showMessage('Funcionário removido com sucesso!', 'success');
            } else {
                const errorData = await response.json();
                showMessage(errorData.message || 'Erro ao remover funcionário!', 'error');
            }
        } catch (error) {
            console.error('Erro ao remover funcionário:', error);
            showMessage('Erro de conexão ao remover funcionário.', 'error');
        }
    }
}

async function handleChangePassword(employeeName) {
    const newPassword = prompt(`Digite a nova senha para ${employeeName}:`);
    
    if (!newPassword) return;
    if (newPassword.length < 3) {
        showMessage('A senha deve ter pelo menos 3 caracteres!', 'error');
        return;
    }
    
    try {
        const employee = adminEmployees.find(emp => emp.username === employeeName);
        if (!employee) {
            showMessage('Funcionário não encontrado para alterar a senha.', 'error');
            return;
        }

        const response = await fetch(`/api/users/${employee.id}/change_password`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ new_password: newPassword }),
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage('Senha alterada com sucesso!', 'success');
        } else {
            showMessage(data.message || 'Erro ao alterar senha', 'error');
        }
    } catch (error) {
        console.error('Erro ao alterar senha:', error);
        showMessage('Erro de conexão. Tente novamente.', 'error');
    }
}

function showMessage(text, type) {
    const existingMessage = document.querySelector('.message');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    const message = document.createElement('div');
    message.className = `message ${type}`;
    message.textContent = text;
    
    const container = document.querySelector('.login-form') || 
                      document.querySelector('.admin-panel') ||
                      document.querySelector('.main-container') ||
                      document.body;
    
    container.insertBefore(message, container.firstChild);
    
    setTimeout(() => {
        if (message.parentNode) {
            message.remove();
        }
    }, 3000);
}