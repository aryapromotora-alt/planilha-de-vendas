from flask import Blueprint, jsonify, request, session
from models.user import User, db
from models.sales import Sale # Importar o modelo Sale
import json
import os

user_bp = Blueprint('user', __name__)

@user_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "")
    
    if not username or not password:
        return jsonify({"success": False, "message": "Usuário e senha são obrigatórios"}), 400
    
    # Verificar se é admin (usuário com role 'admin' no banco de dados)
    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        session['user'] = user.username
        session['is_admin'] = (user.role == 'admin')
        return jsonify({
            "success": True, 
            "user": user.username, 
            "is_admin": (user.role == 'admin')
        })
    
    return jsonify({"success": False, "message": "Usuário ou senha incorretos"}), 401

@user_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Logout realizado com sucesso"})

@user_bp.route('/check-session', methods=['GET'])
def check_session():
    if 'user' in session:
        return jsonify({
            "logged_in": True,
            "user": session['user'],
            "is_admin": session.get('is_admin', False)
        })
    return jsonify({"logged_in": False})

@user_bp.route('/change-employee-password', methods=['POST'])
def change_employee_password():
    # Verificar se o usuário é admin
    if not session.get('is_admin'):
        return jsonify({"success": False, "message": "Acesso negado"}), 403
    
    data = request.json
    employee_name = data.get("employee_name")
    new_password = data.get("new_password")
    
    if not employee_name or not new_password:
        return jsonify({"success": False, "message": "Nome do funcionário e nova senha são obrigatórios"}), 400
    
    user = User.query.filter_by(username=employee_name).first()
    
    if not user:
        return jsonify({"success": False, "message": "Funcionário não encontrado"}), 404
    
    # Atualizar senha
    user.set_password(new_password)
    db.session.commit()
    return jsonify({"success": True, "message": "Senha alterada com sucesso"})

@user_bp.route('/users', methods=['GET'])
def get_users():
    # Retorna apenas usuários com role 'user' para o painel de funcionários, ordenados
    users = User.query.filter_by(role='user').order_by(User.order.asc(), User.id.asc()).all()
    return jsonify([user.to_dict() for user in users])

@user_bp.route('/users', methods=['POST'])
def create_user():
    data = request.json
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "user") # Permite definir a role, padrão 'user'

    if not username or not password:
        return jsonify({"message": "Nome de usuário e senha são obrigatórios"}), 400
    
    # Email é opcional, mas se fornecido, deve ser único
    if email and User.query.filter_by(email=email).first():
        return jsonify({"message": "Email já existe"}), 409

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "Nome de usuário já existe"}), 409

    # Obter a maior ordem atual para colocar o novo usuário por último
    max_order = db.session.query(db.func.max(User.order)).scalar() or 0
    
    user = User(username=username, email=email, role=role, order=max_order + 1)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json
    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    user.role = data.get('role', user.role) # Permite atualizar a role
    db.session.commit()
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Excluir vendas associadas ao funcionário
    Sale.query.filter_by(employee_name=user.username).delete()
    
    db.session.delete(user)
    db.session.commit()
    return '', 204

@user_bp.route("/users/<int:user_id>/change_password", methods=["PUT"])
def change_password(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json
    new_password = data.get("new_password")

    if not new_password:
        return jsonify({"message": "Nova senha não fornecida"}), 400

    user.set_password(new_password)
    db.session.commit()
    return jsonify({"message": "Senha alterada com sucesso"}), 200

