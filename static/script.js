// Dados iniciais e configurações
let currentUser = null;
let isAdmin = false;
let employees = [];
let spreadsheetDataPortabilidade = {};
let spreadsheetDataNovo = {};
let currentSheet = null; // 'portabilidade' ou 'novo'

// ✅ Nova variável: controla a ordem de exibição (frontend-only)
let employeeDisplayOrder = []; // Array de usernames na ordem desejada

// Inicialização
document.addEventListener('DOMContentLoaded', function () {
    initializeApp();
    setupEventListeners();
});

async function initializeApp() {
    try {
        const [dataPort, dataNovo] = await Promise.all([
            fetch('/api/data?type=portabilidade', { credentials: 'include' }).then(r => r.json()),
            fetch('/api/data?type=novo', { credentials: 'include' }).then(r => r.json())
        ]);

        const incomingEmployees = dataPort.employees || dataNovo.employees || [];

        // ✅ Preserva ordem existente e adiciona novos no final
        if (employeeDisplayOrder.length === 0) {
            // Primeira carga: inicializa com a ordem recebida (ordem atual é mantida!)
            employeeDisplayOrder = incomingEmployees.map(emp => emp.username);
        } else {
            // Recarga (ex: após adicionar vendedor): mantém ordem atual + novos no final
            const existingSet = new Set(employeeDisplayOrder);
            const newOnly = incomingEmployees.filter(emp => !existingSet.has(emp.username));
            employeeDisplayOrder.push(...newOnly.map(emp => emp.username));
        }

        // ✅ Reordena employees para bater com employeeDisplayOrder
        const empMap = {};
        incomingEmployees.forEach(emp => empMap[emp.username] = emp);
        employees = employeeDisplayOrder
            .map(username => empMap[username])
            .filter(Boolean); // remove undefined (caso algum tenha sido removido)

        spreadsheetDataPortabilidade = dataPort.spreadsheetData || {};
        spreadsheetDataNovo = dataNovo.spreadsheetData || {};

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
        employeeDisplayOrder = [];
        spreadsheetDataPortabilidade = {};
        spreadsheetDataNovo = {};
    }

    try {
        const sessionResponse = await fetch('/api/check-session', { credentials: 'include' });
        if (sessionResponse.ok) {
            const sessionData = await sessionResponse.json();
            if (sessionData.logged_in) {
                currentUser = sessionData.user;
                isAdmin = sessionData.is_admin;
                showDashboard();
                return;
            }
        }
    } catch (error) {
        console.error('Erro ao verificar sessão:', error);
    }

    document.getElementById('login-section').style.display = 'flex';
}

function getCurrentSpreadsheetData() {
    return currentSheet === 'novo' ? spreadsheetDataNovo : spreadsheetDataPortabilidade;
}

// 🔁 Atualiza dados do servidor periodicamente
async function pollServerData() {
    if (!currentUser || !currentSheet) return;

    try {
        const response = await fetch(`/api/data?type=${currentSheet}`, {
            credentials: 'include'
        });

        if (response.ok) {
            const newData = await response.json();
            const incomingEmployees = newData.employees || [];

            // ✅ Mantém ordem existente e adiciona novos no final
            const existingSet = new Set(employeeDisplayOrder);
            const newOnly = incomingEmployees.filter(emp => !existingSet.has(emp.username));
            employeeDisplayOrder.push(...newOnly.map(emp => emp.username));

            // ✅ Atualiza employees na ordem correta
            const empMap = {};
            incomingEmployees.forEach(emp => empMap[emp.username] = emp);
            employees = employeeDisplayOrder
                .map(username => empMap[username])
                .filter(Boolean);

            if (currentSheet === 'novo') {
                spreadsheetDataNovo = newData.spreadsheetData || {};
            } else {
                spreadsheetDataPortabilidade = newData.spreadsheetData || {};
            }

            if (currentSheet === 'novo') {
                renderSpreadsheetNovo();
            } else {
                renderSpreadsheet();
            }
        }
    } catch (error) {
        console.warn('Falha ao atualizar dados em segundo plano:', error);
    }
}

function startAutoRefresh() {
    if (window.autoRefreshInterval) {
        clearInterval(window.autoRefreshInterval);
    }
    window.autoRefreshInterval = setInterval(pollServerData, 30000); // a cada 30s
}

function stopAutoRefresh() {
    if (window.autoRefreshInterval) {
        clearInterval(window.autoRefreshInterval);
        window.autoRefreshInterval = null;
    }
}

// ✅ Salvar APENAS uma célula
async function saveCellToServer(sheetType, employee, day, value) {
    try {
        const response = await fetch('/api/cell', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sheet_type: sheetType, employee, day, value }),
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error('Falha ao salvar célula');
        }
        return true;
    } catch (error) {
        console.error('Erro ao salvar célula:', error);
        showMessage('Erro ao salvar valor!', 'error');
        return false;
    }
}

function setupEventListeners() {
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    document.getElementById('btn-portabilidade')?.addEventListener('click', () => showSheet('portabilidade'));
    document.getElementById('btn-novo')?.addEventListener('click', () => showSheet('novo'));
    document.getElementById('logout-btn')?.addEventListener('click', handleLogout);
    document.getElementById('logout-btn-novo')?.addEventListener('click', handleLogout);
    document.getElementById('back-to-dashboard-from-port')?.addEventListener('click', showDashboard);
    document.getElementById('back-to-dashboard-from-novo')?.addEventListener('click', showDashboard);
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
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
            credentials: 'include'
        });
        const data = await response.json();
        if (data.success) {
            currentUser = data.user;
            isAdmin = data.is_admin;
            showDashboard();
        } else {
            showMessage(data.message || 'Erro no login', 'error');
        }
    } catch (error) {
        console.error('Erro no login:', error);
        showMessage('Erro de conexão. Tente novamente.', 'error');
    }
}

async function handleLogout() {
    stopAutoRefresh(); // ← Importante!
    try {
        await fetch('/api/logout', { method: 'POST', credentials: 'include' });
    } catch (error) {
        console.error('Erro no logout:', error);
    }
    currentUser = null;
    isAdmin = false;
    currentSheet = null;
    employeeDisplayOrder = []; // ✅ Limpa ao sair
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
        document.getElementById('admin-panel-btn-novo').style.display = isAdmin ? 'inline-block' : 'none';
        renderSpreadsheetNovo();
    } else {
        document.getElementById('main-section').style.display = 'block';
        document.getElementById('logged-user').textContent = `Logado como: ${currentUser}`;
        document.getElementById('admin-panel-btn').style.display = isAdmin ? 'inline-block' : 'none';
        renderSpreadsheet();
    }

    startAutoRefresh(); // ← Inicia atualização automática
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
    const currentValue = data[cell.dataset.employee]?.[cell.dataset.day] || 0;

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

    const finish = () => {
        input.removeEventListener('blur', finish);
        input.removeEventListener('keypress', handleKeyPress);
        finishEditing(cell, input, sheetType);
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter') finish();
    };

    input.addEventListener('blur', finish);
    input.addEventListener('keypress', handleKeyPress);
}

async function finishEditing(cell, input, sheetType) {
    const newValue = parseFloat(input.value) || 0;
    const employee = cell.dataset.employee;
    const day = cell.dataset.day;

    // Atualiza visualmente
    let data = sheetType === 'novo' ? spreadsheetDataNovo : spreadsheetDataPortabilidade;
    if (!data[employee]) {
        data[employee] = { monday: 0, tuesday: 0, wednesday: 0, thursday: 0, friday: 0 };
    }
    data[employee][day] = newValue;
    cell.textContent = formatCurrency(newValue);

    if (sheetType === 'novo') {
        spreadsheetDataNovo = data;
    } else {
        spreadsheetDataPortabilidade = data;
    }

    updateTotals(sheetType);

    // ✅ Salva APENAS essa célula
    await saveCellToServer(sheetType, employee, day, newValue);
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

// ====== Funções de Admin ======
async function showAdminPanel() {
    await loadEmployeesForAdmin();
    document.getElementById('admin-section').style.display = 'block';
}

function switchTab(e) {
    const targetTab = e.target.dataset.tab;
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    e.target.classList.add('active');
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
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
            const allUsers = await response.json();
            adminEmployees = allUsers.filter(emp => emp.role === 'user');

            // ✅ Reordena adminEmployees para bater com employeeDisplayOrder
            const empMap = {};
            adminEmployees.forEach(emp => empMap[emp.username] = emp);
            adminEmployees = employeeDisplayOrder
                .map(username => empMap[username])
                .filter(Boolean);
        } else {
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
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: name, password: password, email: email, role: 'user' }),
            credentials: 'include'
        });
        const data = await response.json();
        if (response.ok) {
            await initializeApp(); // ← Recarrega mantendo ordem + novo no final
            renderEmployeeManagement();
            if (currentSheet) showSheet(currentSheet);
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
                // ✅ Remove do employeeDisplayOrder também
                const index = employeeDisplayOrder.indexOf(employeeName);
                if (index !== -1) {
                    employeeDisplayOrder.splice(index, 1);
                }
                await initializeApp();
                renderEmployeeManagement();
                if (currentSheet) showSheet(currentSheet);
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
            headers: { 'Content-Type': 'application/json' },
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
    if (existingMessage) existingMessage.remove();
    const message = document.createElement('div');
    message.className = `message ${type}`;
    message.textContent = text;
    const container = document.querySelector('.login-form') ||
                      document.querySelector('.admin-panel') ||
                      document.querySelector('.main-container') ||
                      document.body;
    container.insertBefore(message, container.firstChild);
    setTimeout(() => {
        if (message.parentNode) message.remove();
    }, 3000);
}