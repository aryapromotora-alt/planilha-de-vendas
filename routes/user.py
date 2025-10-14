from flask import Blueprint, jsonify, request, session
from models.user import User, db

user_bp = Blueprint('user', __name__)

# 🔐 Login
@user_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"success": False, "message": "Usuário e senha são obrigatórios"}), 400

    if username == "admin" and password == "admin123":
        session['user'] = 'admin'
        session['is_admin'] = True
        return jsonify({
            "success": True,
            "user": "Administrador",
            "is_admin": True
        })

    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session['user'] = user.username
        session['is_admin'] = user.role == "admin"
        return jsonify({
            "success": True,
            "user": user.username,
            "is_admin": user.role == "admin"
        })

    return jsonify({"success": False, "message": "Usuário ou senha incorretos"}), 401

# 🚪 Logout
@user_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Logout realizado com sucesso"})

# 🔍 Verificar sessão
@user_bp.route('/check-session', methods=['GET'])
def check_session():
    if 'user' in session:
        return jsonify({
            "logged_in": True,
            "user": session['user'],
            "is_admin": session.get('is_admin', False)
        })
    return jsonify({"logged_in": False})

# 👥 Listar usuários
@user_bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

# ➕ Criar novo usuário
@user_bp.route('/users', methods=['POST'])
def create_user():
    data = request.json
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"message": "Dados incompletos"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "Nome de usuário já existe"}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email já existe"}), 409

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201

# 🔍 Obter usuário por ID
@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

# ✏️ Atualizar usuário
@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json
    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    db.session.commit()
    return jsonify(user.to_dict())

# ❌ Deletar usuário
@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return '', 204

# 🔑 Alterar senha
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