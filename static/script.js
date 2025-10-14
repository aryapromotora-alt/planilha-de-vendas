let employees = [];
let spreadsheetData = {};
let currentUser = null;
let isAdmin = false;

async function loadDataFromServer() {
    try {
        const response = await fetch('/api/users', { credentials: 'include' });
        if (response.ok) {
            const data = await response.json();
            employees = data || [];

            employees.forEach(emp => {
                if (!spreadsheetData[emp.username]) {
                    spreadsheetData[emp.username] = {
                        monday: 0,
                        tuesday: 0,
                        wednesday: 0,
                        thursday: 0,
                        friday: 0
                    };
                }
            });

            renderEmployeeManagement();
            renderSpreadsheet();
        } else {
            throw new Error('Erro ao carregar usuários');
        }
    } catch (error) {
        console.error('Erro na requisição:', error);
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
            credentials: 'include'
        });

        const result = await response.json();
        if (response.ok && result.success) {
            currentUser = result.user;
            isAdmin = result.is_admin;
            document.getElementById('login-section').style.display = 'none';
            document.getElementById('main-section').style.display = 'block';
            loadDataFromServer();
        } else {
            showMessage(result.message || 'Login falhou', 'error');
        }
    } catch (err) {
        console.error(err);
        showMessage('Erro de conexão. Tente novamente.', 'error');
    }
}

function handleLogout() {
    fetch('/api/logout', {
        method: 'POST',
        credentials: 'include'
    }).then(() => {
        currentUser = null;
        isAdmin = false;
        document.getElementById('main-section').style.display = 'none';
        document.getElementById('login-section').style.display = 'block';
    });
}
async function handleAddEmployee(e) {
    e.preventDefault();
    const name = document.getElementById('new-employee-name').value.trim();
    const password = document.getElementById('new-employee-password').value;

    if (!name || !password) {
        showMessage('Preencha todos os campos!', 'error');
        return;
    }

    if (employees.find(emp => emp.username.toLowerCase() === name.toLowerCase())) {
        showMessage('Funcionário já existe!', 'error');
        return;
    }

    try {
        const response = await fetch('/api/users', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: name,
                email: `${name.toLowerCase()}@sistema.local`,
                password: password
            }),
            credentials: 'include'
        });

        if (response.ok) {
            const newUser = await response.json();
            employees.push(newUser);
            spreadsheetData[newUser.username] = {
                monday: 0, tuesday: 0, wednesday: 0, thursday: 0, friday: 0
            };
            renderEmployeeManagement();
            renderSpreadsheet();
            showMessage('Funcionário adicionado com sucesso!', 'success');
            document.getElementById('add-employee-form').reset();
        } else {
            const error = await response.json();
            showMessage(error.message || 'Erro ao adicionar funcionário', 'error');
        }
    } catch (err) {
        console.error(err);
        showMessage('Erro de conexão. Tente novamente.', 'error');
    }
}

async function removeEmployee(employeeName) {
    const user = employees.find(emp => emp.username === employeeName);
    if (!user) return;

    if (confirm(`Tem certeza que deseja remover ${employeeName}?`)) {
        try {
            const response = await fetch(`/api/users/${user.id}`, {
                method: 'DELETE',
                credentials: 'include'
            });

            if (response.ok) {
                employees = employees.filter(emp => emp.id !== user.id);
                delete spreadsheetData[employeeName];
                renderEmployeeManagement();
                renderSpreadsheet();
                showMessage('Funcionário removido com sucesso!', 'success');
            } else {
                showMessage('Erro ao remover funcionário', 'error');
            }
        } catch (err) {
            console.error(err);
            showMessage('Erro de conexão. Tente novamente.', 'error');
        }
    }
}

async function handleChangePassword(employeeName) {
    const user = employees.find(emp => emp.username === employeeName);
    if (!user) return;

    const newPassword = prompt(`Digite a nova senha para ${employeeName}:`);
    if (!newPassword || newPassword.length < 3) {
        showMessage('A senha deve ter pelo menos 3 caracteres!', 'error');
        return;
    }

    try {
        const response = await fetch(`/api/users/${user.id}/change_password`, {
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
    } catch (err) {
        console.error(err);
        showMessage('Erro de conexão. Tente novamente.', 'error');
    }
}
function renderEmployeeManagement() {
    const container = document.getElementById('employee-list');
    container.innerHTML = '';

    employees.forEach(emp => {
        const div = document.createElement('div');
        div.className = 'employee-item';
        div.innerHTML = `
            <span>${emp.username}</span>
            <button onclick="removeEmployee('${emp.username}')">Remover</button>
            <button onclick="handleChangePassword('${emp.username}')">Alterar Senha</button>
        `;
        container.appendChild(div);
    });
}

function renderSpreadsheet() {
    const table = document.getElementById('spreadsheet-body');
    table.innerHTML = '';

    employees.forEach(emp => {
        const row = document.createElement('tr');
        const data = spreadsheetData[emp.username] || {};

        row.innerHTML = `
            <td>${emp.username}</td>
            <td><input type="number" value="${data.monday || 0}" onchange="updateCell('${emp.username}', 'monday', this.value)" /></td>
            <td><input type="number" value="${data.tuesday || 0}" onchange="updateCell('${emp.username}', 'tuesday', this.value)" /></td>
            <td><input type="number" value="${data.wednesday || 0}" onchange="updateCell('${emp.username}', 'wednesday', this.value)" /></td>
            <td><input type="number" value="${data.thursday || 0}" onchange="updateCell('${emp.username}', 'thursday', this.value)" /></td>
            <td><input type="number" value="${data.friday || 0}" onchange="updateCell('${emp.username}', 'friday', this.value)" /></td>
        `;
        table.appendChild(row);
    });
}

function updateCell(username, day, value) {
    if (!spreadsheetData[username]) {
        spreadsheetData[username] = {};
    }
    spreadsheetData[username][day] = parseFloat(value) || 0;
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

document.getElementById('login-form').addEventListener('submit', handleLogin);
document.getElementById('logout-button').addEventListener('click', handleLogout);
document.getElementById('add-employee-form').addEventListener('submit', handleAddEmployee);