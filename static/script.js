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
// DADOS DOS USUÁRIOS (mantém o login no frontend)
// ========================

const USERS = {
    'admin': 'minha_senha_secreta',
    'Anderson': '123',
    'Vitoria': '123',
    'Jemima': '123',
    'Maiany': '123',
    'Fernanda': '123',
    'Nadia': '123',
    'Giovana': '123'
};

// ========================
// DADOS DA PLANILHA (valores reais)
// ========================

const SPREADSHEET_DATA = {
    'Anderson': { monday: 52894.08, tuesday: 18245.38, wednesday: 53967.95, thursday: 18553.33, friday: 0 },
    'Vitoria': { monday: 89715.38, tuesday: 31844.79, wednesday: 0, thursday: 0, friday: 0 },
    'Jemima': { monday: 0, tuesday: 11597.24, wednesday: 28200.08, thursday: 0, friday: 0 },
    'Maiany': { monday: 18629.33, tuesday: 23459.00, wednesday: 17023.23, thursday: 0, friday: 0 },
    'Fernanda': { monday: 0, tuesday: 0, wednesday: 0, thursday: 0, friday: 0 },
    'Nadia': { monday: 46888.05, tuesday: 31758.48, wednesday: 69249.82, thursday: 0, friday: 0 },
    'Giovana': { monday: 16270.00, tuesday: 70779.45, wednesday: 0, thursday: 0, friday: 0 }
};

// ========================
// FUNÇÕES DE LOGIN (mantém o funcionamento antigo)
// ========================

function login(username, password) {
    return USERS[username] === password;
}

function logout() {
    sessionStorage.removeItem('loggedUser');
    window.location.reload();
}

function getCurrentUser() {
    return sessionStorage.getItem('loggedUser');
}

// ========================
// RENDERIZAÇÃO DA PLANILHA
// ========================

function renderSpreadsheet() {
    const tbody = document.getElementById('employee-rows');
    tbody.innerHTML = '';

    const employees = Object.keys(SPREADSHEET_DATA);
    const dailyTotals = { monday: 0, tuesday: 0, wednesday: 0, thursday: 0, friday: 0 };

    employees.forEach(name => {
        const data = SPREADSHEET_DATA[name];
        const total = data.monday + data.tuesday + data.wednesday + data.thursday + data.friday;
        
        // Acumula totais diários
        dailyTotals.monday += data.monday;
        dailyTotals.tuesday += data.tuesday;
        dailyTotals.wednesday += data.wednesday;
        dailyTotals.thursday += data.thursday;
        dailyTotals.friday += data.friday;

        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${name}</td>
            <td>${formatBRL(data.monday)}</td>
            <td>${formatBRL(data.tuesday)}</td>
            <td>${formatBRL(data.wednesday)}</td>
            <td>${formatBRL(data.thursday)}</td>
            <td>${formatBRL(data.friday)}</td>
            <td class="total-cell">${formatBRL(total)}</td>
        `;
        tbody.appendChild(row);
    });

    // Atualiza totais diários
    document.getElementById('monday-total').textContent = formatBRL(dailyTotals.monday);
    document.getElementById('tuesday-total').textContent = formatBRL(dailyTotals.tuesday);
    document.getElementById('wednesday-total').textContent = formatBRL(dailyTotals.wednesday);
    document.getElementById('thursday-total').textContent = formatBRL(dailyTotals.thursday);
    document.getElementById('friday-total').textContent = formatBRL(dailyTotals.friday);
    document.getElementById('week-total').textContent = formatBRL(
        dailyTotals.monday + dailyTotals.tuesday + dailyTotals.wednesday + dailyTotals.thursday + dailyTotals.friday
    );
}

// ========================
// INICIALIZAÇÃO
// ========================

document.addEventListener('DOMContentLoaded', () => {
    const loginSection = document.getElementById('login-section');
    const mainSection = document.getElementById('main-section');
    const adminBtn = document.getElementById('admin-panel-btn');
    const logoutBtn = document.getElementById('logout-btn');
    const loggedUserSpan = document.getElementById('logged-user');

    const currentUser = getCurrentUser();
    
    if (currentUser) {
        loginSection.style.display = 'none';
        mainSection.style.display = 'block';
        loggedUserSpan.textContent = `Logado como: ${currentUser}`;
        
        // Mostra botão de admin apenas para "admin"
        if (currentUser === 'admin') {
            adminBtn.style.display = 'block';
        }
        
        renderSpreadsheet();
    } else {
        loginSection.style.display = 'flex';
        mainSection.style.display = 'none';
    }

    // Login
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            if (login(username, password)) {
                sessionStorage.setItem('loggedUser', username);
                window.location.reload();
            } else {
                alert('Usuário ou senha inválidos');
            }
        });
    }

    // Logout
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
});