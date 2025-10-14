import os
from app import create_app
from models.user import db, User
from werkzeug.security import generate_password_hash
from sqlalchemy import text

# Configurações do admin
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
ADMIN_ROLE = "admin"

# Cria a aplicação Flask
app = create_app()

with app.app_context():
    print("Iniciando a inicialização do banco de dados...")

    # 1. Cria todas as tabelas (se não existirem)
    try:
        db.create_all()
        print("✅ Tabelas criadas (se necessário).")
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        exit(1)

    # 2. Garante que a coluna 'password' exista
    try:
        result = db.session.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'user' AND column_name = 'password';
        """))
        if not result.fetchone():
            print("⚠️ Coluna 'password' não encontrada. Adicionando...")
            db.session.execute(text('ALTER TABLE "user" ADD COLUMN password VARCHAR(128) NOT NULL DEFAULT \'\';'))
            db.session.commit()
            print("✅ Coluna 'password' adicionada.")
        else:
            print("✅ Coluna 'password' já existe.")
    except Exception as e:
        print(f"❌ Erro ao verificar/criar coluna 'password': {e}")
        exit(1)

    # 3. Garante que a coluna 'role' exista
    try:
        result = db.session.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'user' AND column_name = 'role';
        """))
        if not result.fetchone():
            print("⚠️ Coluna 'role' não encontrada. Adicionando...")
            db.session.execute(text('ALTER TABLE "user" ADD COLUMN role VARCHAR(20) DEFAULT \'user\';'))
            db.session.commit()
            print("✅ Coluna 'role' adicionada.")
        else:
            print("✅ Coluna 'role' já existe.")
    except Exception as e:
        print(f"❌ Erro ao verificar/criar coluna 'role': {e}")
        exit(1)

    # 4. Cria o usuário admin se não existir
    admin_user = User.query.filter_by(username=ADMIN_USERNAME).first()
    if not admin_user:
        try:
            hashed_password = generate_password_hash(ADMIN_PASSWORD)
            new_admin = User(
                username=ADMIN_USERNAME,
                password=hashed_password,
                role=ADMIN_ROLE,
                email=""
            )
            db.session.add(new_admin)
            db.session.commit()
            print(f"✅ Usuário admin '{ADMIN_USERNAME}' criado.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao criar admin: {e}")
            exit(1)
    else:
        print(f"ℹ️ Usuário admin '{ADMIN_USERNAME}' já existe.")

    print("✅ Inicialização do banco concluída com sucesso.")