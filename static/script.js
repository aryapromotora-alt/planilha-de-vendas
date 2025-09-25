// ========================
// UTILS
// ========================

function formatBRL(value) {
    if (typeof value !== 'number' || isNaN(value)) return 'R$ 0,00';
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

// ========================
// AUTENTICAÇÃO
// ========================

async function checkAuth() {
    try {
        const res = await fetch('/api/me');
        if (res.ok) {
            const data = await res.json();
            return data.logged_in ? data.username : null;
        }
    } catch (error) {
        console.warn('Erro ao verificar autenticação:', error);
    }
    return null;
}

async function login(username, password) {
    try {
        const res = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        return await res.json();
    } catch (error) {
        console.error('Erro no login:', error);
        return { success: false, message: 'Erro de conexão' };
    }
}

async function logout() {
    try {
        await fetch('/api/logout', { method: 'POST' });
    } catch (error) {
        console.warn('Erro no logout:', error);
    }
    window.location.reload();
}

// ========================
// GERENCIAMENTO DE SENHAS (NOVO)
// ========================

async function updatePassword(username, newPassword) {
    try {
        const res = await fetch('/api/users/password', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, newPassword })
        });
        return await res.json();
    } catch (error) {
        console.error('Erro ao atualizar senha:', error);
        return { success: false, message: 'Erro de conexão' };
    }
}

// ========================
// CARREGAMENTO DE DADOS
// ========================

async function loadSpreadsheetData() {
    try {
        const res = await fetch('/api/data');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const rawData = await res.json();

        const employees = rawData.employees || [];
        const spreadsheetData = rawData.spreadsheetData || {};

        const processedEmployees = employees
            .filter(emp => emp.name !== 'admin') // Esconde "admin" da planilha
            .map(emp => {
                const data = spreadsheetData[emp.name] || {};
                return {
                    name: emp.name,
                    monday: data.monday || 0,
                    tuesday: data.tuesday || 0,
                    wednesday: data.wednesday || 0,
                    thursday: data.thursday || 0,
                    friday: data.friday || 0
                };
            });

        const dailyTotals = {
            monday: 0, tuesday: 0, wednesday: 0, thursday: 0, friday: 0
        };

        processedEmployees.forEach(emp => {
            dailyTotals.monday += emp.monday;
            dailyTotals.tuesday += emp.tuesday;
            dailyTotals.wednesday += emp.wednesday;
            dailyTotals.thursday += emp.thursday;
            dailyTotals.friday += emp.friday;
        });

        const weekTotal = Object.values(dailyTotals).reduce((sum, val) => sum + val, 0);

        return {
            employees: processedEmployees,
            dailyTotals: { ...dailyTotals, week: weekTotal }
        };
    } catch (error) {
        console.error('Erro ao carregar dados:', error);
        return {
            employees: [],
            dailyTotals: { monday: 0, tuesday: 0, wednesday: 0, thursday: 0, friday: 0, week: 0 }
        };
    }
}

function renderSpreadsheet(data) {
    const tbody = document.getElementById('employee-rows');
    if (!tbody) return;

    tbody.innerHTML = '';

    data.employees.forEach(emp => {
        const total = emp.monday + emp.tuesday + emp.wednesday + emp.thursday + emp.friday;
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${emp.name}</td>
            <td>${formatBRL(emp.monday)}</td>
            <td>${formatBRL(emp.tuesday)}</td>
            <td>${formatBRL(emp.wednesday)}</td>
            <td>${formatBRL(emp.thursday)}</td>
            <td>${formatBRL(emp.friday)}</td>
            <td class="total-cell">${formatBRL(total)}</td>
        `;
        tbody.appendChild(row);
    });

    const totals = data.dailyTotals;
    document.getElementById('monday-total')?.textContent = formatBRL(totals.monday);
    document.getElementById('tuesday-total')?.textContent = formatBRL(totals.tuesday);
    document.getElementById('wednesday-total')?.textContent = formatBRL(totals.wednesday);
    document.getElementById('thursday-total')?.textContent = formatBRL(totals.thursday);
    document.getElementById('friday-total')?.textContent = formatBRL(totals.friday);
    document.getElementById('week-total')?.textContent = formatBRL(totals.week);
}

// ========================
// PAINEL DE ADMIN (ATUALIZADO)
// ========================

async function loadEmployeesForAdmin() {
    try {
        const res = await fetch('/api/data');
        const data = await res.json();
        return data.employees.filter(emp => emp.name !== 'admin');
    } catch (error) {
        console.error('Erro ao carregar vendedores:', error);
        return [];
    }
}

function renderEmployeeList(employees, isAdmin) {
    const list = document.getElementById('employee-management-list');
    if (!list) return;

    list.innerHTML = employees.map(emp => `
        <li style="display: flex; justify-content: space-between; align-items: center; padding: 8px; border-bottom: 1px solid #333;">
            <span>${emp.name}</span>
            <div>
                ${isAdmin ? `
                    <button onclick="editPassword('${emp.name}')" style="margin-right: 8px; padding: 4px 8px; background: #444; color: #FFD700; border: none; border-radius: 4px;">Editar Senha</button>
                    <button onclick="removeEmployee('${emp.name}')" style="padding: 4px 8px; background: #ff4d4d; color: white; border: none; border-radius: 4px;">Remover</button>
                ` : ''}
            </div>
        </li>
    `).join('');
}

async function addEmployee(name, password) {
    try {
        const res = await fetch('/api/data');
        const data = await res.json();

        // Adiciona novo vendedor
        data.employees.push({ name, password });
        if (!data.spreadsheetData[name]) {
            data.spreadsheetData[name] = { monday: 0, tuesday: 0, wednesday: 0, thursday: 0, friday: 0 };
        }

        // Salva
        const saveRes = await fetch('/api/data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        return saveRes.ok;
    } catch (error) {
        console.error('Erro ao adicionar vendedor:', error);
        return false;
    }
}

async function removeEmployee(name) {
    if (!confirm(`Tem certeza que deseja remover ${name}?`)) return;

    try {
        const res = await fetch('/api/data');
        const data = await res.json();

        data.employees = data.employees.filter(emp => emp.name !== name);
        delete data.spreadsheetData[name];

        const saveRes = await fetch('/api/data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (saveRes.ok) {
            alert('Vendedor removido com sucesso!');
            if (window.currentSection === 'admin') {
                const employees = await loadEmployeesForAdmin();
                renderEmployeeList(employees, true);
            }
        } else {
            alert('Erro ao remover vendedor');
        }
    } catch (error) {
        console.error('Erro ao remover vendedor:', error);
        alert('Erro ao remover vendedor');
    }
}

// Função global para editar senha (acessível pelo onclick)
window.editPassword = async function(name) {
    const newPassword = prompt(`Digite a nova senha para ${name}:`);
    if (!newPassword) return;

    const result = await updatePassword(name, newPassword);
    if (result.success) {
        alert('Senha atualizada com sucesso!');
    } else {
        alert(result.message || 'Erro ao atualizar senha');
    }
};

window.removeEmployee = removeEmployee;

// ========================
// INICIALIZAÇÃO
// ========================

document.addEventListener('DOMContentLoaded', async () => {
    const loginSection = document.getElementById('login-section');
    const mainSection = document.getElementById('main-section');
    const adminSection = document.getElementById('admin-section');
    const adminBtn = document.getElementById('admin-panel-btn');
    const logoutBtn = document.getElementById('logout-btn');
    const backToMainBtn = document.getElementById('back-to-main');
    const addEmployeeForm = document.getElementById('add-employee-form');

    const username = await checkAuth();
    if (username) {
        loginSection.style.display = 'none';
        mainSection.style.display = 'block';
        document.getElementById('logged-user').textContent = `Logado como: ${username}`;

        // Só "admin" é admin
        const isAdmin = username === 'admin';
        if (isAdmin && adminBtn) {
            adminBtn.style.display = 'block';
        }

        const data = await loadSpreadsheetData();
        renderSpreadsheet(data);
    } else {
        loginSection.style.display = 'flex';
        mainSection.style.display = 'none';
        if (adminSection) adminSection.style.display = 'none';
    }

    // Login
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username')?.value || '';
            const password = document.getElementById('password')?.value || '';
            const result = await login(username, password);
            if (result.success) {
                window.location.reload();
            } else {
                alert(result.message || 'Erro ao fazer login');
            }
        });
    }

    // Logout
    if (logoutBtn) logoutBtn.addEventListener('click', logout);

    // Admin panel
    if (adminBtn) {
        adminBtn.addEventListener('click', async () => {
            mainSection.style.display = 'none';
            adminSection.style.display = 'block';
            window.currentSection = 'admin';

            const employees = await loadEmployeesForAdmin();
            renderEmployeeList(employees, true);
        });
    }

    if (backToMainBtn) {
        backToMainBtn.addEventListener('click', () => {
            adminSection.style.display = 'none';
            mainSection.style.display = 'block';
            window.currentSection = 'main';
        });
    }

    // Adicionar vendedor
    if (addEmployeeForm) {
        addEmployeeForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = document.getElementById('new-employee-name')?.value;
            const password = document.getElementById('new-employee-password')?.value;
            if (!name || !password) {
                alert('Nome e senha são obrigatórios');
                return;
            }

            const success = await addEmployee(name, password);
            if (success) {
                alert('Vendedor adicionado com sucesso!');
                addEmployeeForm.reset();
                // Atualiza lista
                const employees = await loadEmployeesForAdmin();
                renderEmployeeList(employees, true);
            } else {
                alert('Erro ao adicionar vendedor');
            }
        });
    }
});