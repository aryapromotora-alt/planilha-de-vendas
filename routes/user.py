from flask import Blueprint, jsonify, request, session
import os
import json

user_bp = Blueprint('user', __name__)

def load_spreadsheet_data():
    """Carrega os dados reais da planilha (mesma lógica do data.py)"""
    DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "database", "planilha_data.json")
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    # Dados fallback - inclui "admin" APENAS para autenticação
    default_employees = [
        {"name": "admin", "password": "minha_senha_secreta"},
        {"name": "Anderson", "password": "123"},
        {"name": "Vitoria", "password": "123"},
        {"name": "Jemima", "password": "123"},
        {"name": "Maiany", "password": "123"},
        {"name": "Fernanda", "password": "123"},
        {"name": "Nadia", "password": "123"},
        {"name": "Giovana", "password": "123"}
    ]
    return {"employees": default_employees}

@user_bp.route('/login', methods=['POST'])
def login():
    """Rota de login segura — valida credenciais no servidor"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'success': False, 'message': 'Usuário e senha são obrigatórios'}), 400

    # Carrega os dados reais da planilha
    planilha = load_spreadsheet_data()
    employees = planilha.get('employees', [])

    # Procura o usuário pelo nome
    user = None
    for emp in employees:
        if emp.get('name') == username:
            user = emp
            break

    # Valida a senha
    if user and user.get('password') == password:
        session['logged_in'] = True
        session['username'] = username
        return jsonify({'success': True, 'username': username})
    else:
        return jsonify({'success': False, 'message': 'Usuário ou senha inválidos'}), 401

@user_bp.route('/logout', methods=['POST'])
def logout():
    """Encerra a sessão do usuário"""
    session.clear()
    return jsonify({'success': True})

@user_bp.route('/me', methods=['GET'])
def me():
    """Verifica se o usuário está logado"""
    if session.get('logged_in'):
        return jsonify({'logged_in': True, 'username': session.get('username')})
    else:
        return jsonify({'logged_in': False}), 401

# ================================
# NOVA ROTA: Atualizar senha de vendedores
# ================================
@user_bp.route('/users/password', methods=['PUT'])
def update_user_password():
    """Atualiza a senha de um vendedor. Apenas o usuário 'admin' pode fazer isso."""
    # Verifica se está logado e se é admin
    if not session.get('logged_in') or session.get('username') != 'admin':
        return jsonify({'success': False, 'message': 'Acesso negado. Apenas admin pode alterar senhas.'}), 403

    data = request.get_json()
    target_username = data.get('username')
    new_password = data.get('newPassword')

    if not target_username or not new_password:
        return jsonify({'success': False, 'message': 'Nome do usuário e nova senha são obrigatórios.'}), 400

    # Carrega os dados atuais
    planilha = load_spreadsheet_data()
    employees = planilha.get('employees', [])

    # Procura e atualiza a senha do vendedor
    user_found = False
    for emp in employees:
        if emp.get('name') == target_username:
            emp['password'] = new_password
            user_found = True
            break

    if not user_found:
        return jsonify({'success': False, 'message': f'Usuário "{target_username}" não encontrado.'}), 404

    # Salva de volta no arquivo JSON
    DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "database", "planilha_data.json")
    try:
        # Garante que o diretório exista
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(planilha, f, ensure_ascii=False, indent=2)
        return jsonify({'success': True, 'message': f'Senha de "{target_username}" atualizada com sucesso.'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao salvar no arquivo: {str(e)}'}), 500