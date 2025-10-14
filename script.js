// Dados iniciais e configurações
let currentUser = null;
let isAdmin = false;
let employees = [];
let spreadsheetData = {};

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
});

async function initializeApp() {
    // 🔑 PRIMEIRO: Carregar dados do servidor (sempre)
    try {
        await loadDataFromServer();
    } catch (error) {
        console.error('Erro ao carregar dados do servidor:', error);
        employees = [];
        initializeSpreadsheetData();
    }

    // 🔑 DEPOIS: Verificar sessão para definir permissões
    try {
        const sessionResponse = await fetch('/check-session', {
            credentials: 'include'
        });
        if (sessionResponse.ok) {
            const sessionData = await sessionResponse.json();
            if (sessionData.logged_in) {
                currentUser = sessionData.user;
                isAdmin = sessionData.is_admin;
                showMainSection();
                return;
            }
        }
    } catch (error) {
        console.error('Erro ao verificar sessão:', error);
    }

    // Se não estiver logado, mostra login (mas dados já foram carregados)
    document.getElementById('login-section').style.display = 'flex';
}

async function loadDataFromServer() {
    try {
        const response = await fetch('/data', {
            credentials: 'include'
        });
        if (response.ok) {
            const data = await response.json();
            employees = data.employees || [];
            spreadsheetData = data.spreadsheetData || {};
            
            employees.forEach(emp => {
                if (!spreadsheetData[emp.name]) {
                    spreadsheetData[emp.name] = {
                        monday: 0,
                        tuesday: 0,
                        wednesday: 0,
                        thursday: 0,
                        friday: 0
                    };
                }
            });
        } else {
            throw new Error('Erro ao carregar dados do servidor');
        }
    } catch (error) {
        console.error('Erro na requisição:', error);
        throw error;
    }
}

async function saveDataToServer() {
    try {
        const dataToSave = {
          spreadsheetData: spreadsheetData
        };
        
        const response = await fetch('/data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(dataToSave),
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error('Erro ao salvar dados no servidor');
        }
        
        return true;
    } catch (error) {
        console.error('Erro ao salvar dados:', error);
        showMessage('Erro ao salvar dados no servidor!', 'error');
        return false;
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
}

function setupEventListeners() {
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    document.getElementById('logout-btn').addEventListener('click', handleLogout);
    document.getElementById('admin-panel-btn').addEventListener('click', showAdminPanel);
    document.getElementById('back-to-main').addEventListener('click', hideAdminPanel);
    
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', switchTab);
    });
    
    document.getElementById('add-employee-form').addEventListener('submit', handleAddEmployee);
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
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, name, password }),
            credentials: 'include'
        });

        const data = await response.json();

        if (data.success) {
            currentUser = data.user;
            isAdmin = data.is_admin;
            showMainSection();
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
        await fetch('/logout', {
            method: 'POST',
            credentials: 'include'
        });
    } catch (error) {
        console.error('Erro no logout:', error);
    }
    
    currentUser = null;
    isAdmin = false;
    document.getElementById('login-section').style.display = 'flex';
    document.getElementById('main-section').style.display = 'none';
    document.getElementById('admin-section').style.display = 'none';
    document.getElementById('login-form').reset();
}

function showMainSection() {
    document.getElementById('login-section').style.display = 'none';
    document.getElementById('main-section').style.display = 'block';
    document.getElementById('admin-section').style.display = 'none';
    document.getElementById('logged-user').textContent = `Logado como: ${currentUser}`;
    
    if (isAdmin) {
        document.getElementById('admin-panel-btn').style.display = 'inline-block';
    } else {
        document.getElementById('admin-panel-btn').style.display = 'none';
    }
    
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
    
    const nameCell = document.createElement('td');
    nameCell.textContent = employeeName;
    nameCell.className = 'employee-name';
    row.appendChild(nameCell);
    
    const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'];
    days.forEach(day => {
        const cell = document.createElement('td');
        const value = spreadsheetData[employeeName] ? spreadsheetData[employeeName][day] : 0;
        cell.textContent = formatCurrency(value);
        cell.className = 'editable-cell';
        cell.dataset.employee = employeeName;
        cell.dataset.day = day;
        
        if (isAdmin || currentUser === employeeName) {
            cell.addEventListener('click', handleCellClick);
        }
        
        row.appendChild(cell);
    });
    
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
    
    input.addEventListener('blur', () => finishEditing(cell, input));
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            finishEditing(cell, input);
        }
    });
}

async function finishEditing(cell, input) {
    const newValue = parseFloat(input.value) || 0;
    const employee = cell.dataset.employee;
    const day = cell.dataset.day;
    
    if (!spreadsheetData[employee]) {
        spreadsheetData[employee] = {
            monday: 0, tuesday: 0, wednesday: 0, thursday: 0, friday: 0
        };
    }
    
    spreadsheetData[employee][day] = newValue;
    cell.textContent = formatCurrency(newValue);
    
    await saveDataToServer();
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
    
    const weekTotalElement = document.getElementById('week-total');
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

function showAdminPanel() {
    document.getElementById('admin-section').style.display = 'block';
    renderEmployeeManagement();
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

function renderEmployeeManagement() {
    const list = document.getElementById('employee-management-list');
    list.innerHTML = '';
    
    const regularEmployees = employees.filter(emp => emp.name !== 'admin');
    
    regularEmployees.forEach(employee => {
        const li = document.createElement("li");
        const info = document.createElement("span");
        info.className = "employee-info";
        info.textContent = employee.name;
        
        const actionsDiv = document.createElement("div");
        actionsDiv.className = "employee-actions";

        const changePasswordBtn = document.createElement("button");
        changePasswordBtn.textContent = "Alterar Senha";
        changePasswordBtn.className = "change-password-btn";
        changePasswordBtn.addEventListener("click", () => handleChangePassword(employee.name));
        actionsDiv.appendChild(changePasswordBtn);

        const removeBtn = document.createElement("button");
        removeBtn.textContent = "Remover";
        removeBtn.className = "remove-btn";
        removeBtn.addEventListener("click", () => removeEmployee(employee.name));
        actionsDiv.appendChild(removeBtn);
        
        li.appendChild(info);
        li.appendChild(actionsDiv);
        list.appendChild(li);
    });
}

async function handleAddEmployee(e) {
    e.preventDefault();
    const name = document.getElementById('employeeName').value.trim();
    const password = document.getElementById('employeePassword').value.trim();

    if (!name || !password) {
        showMessage('Nome e senha são obrigatórios!', 'error');
        return;
    }

    if (employees.find(emp => emp.name.toLowerCase() === name.toLowerCase())) {
        showMessage('Funcionário já existe!', 'error');
        return;
    }

    // 🧠 Tenta salvar o novo usuário no backend
    const response = await fetch('/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: name, password }),
        credentials: 'include'
    });

    const result = await response.json();
    if (!response.ok || result.error) {
        showMessage(result.message || 'Erro ao adicionar vendedor!', 'error');
        return;
    }

    // ✅ Se salvou com sucesso, atualiza localmente
    employees.push({ name });
    spreadsheetData[name] = {
        monday: 0, tuesday: 0, wednesday: 0, thursday: 0, friday: 0
    };

    const saved = await saveDataToServer();
    if (!saved) {
        employees = employees.filter(emp => emp.name !== name);
        delete spreadsheetData[name];
    } else {
        showMessage('Funcionário adicionado com sucesso!', 'success');
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
        const response = await fetch('/change-employee-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                employee_name: employeeName,
                new_password: newPassword
            }),
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            const employee = employees.find(emp => emp.name === employeeName);
            if (employee) {
                employee.password = newPassword;
            }
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
    
    const loginForm = document.querySelector('.login-form');
    const adminPanel = document.querySelector('.admin-panel');
    
    if (document.getElementById('login-section').style.display !== 'none') {
        loginForm.insertBefore(message, loginForm.firstChild);
    } else if (document.getElementById('admin-section').style.display !== 'none') {
        adminPanel.insertBefore(message, adminPanel.firstChild);
    }
    
    setTimeout(() => {
        if (message.parentNode) {
            message.remove();
        }
    }, 3000);
}