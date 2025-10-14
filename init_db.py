import os
from app import create_app
from models.user import db, User
from werkzeug.security import generate_password_hash

# Configurações do admin
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
ADMIN_ROLE = "admin"

# Cria a aplicação Flask
app = create_app()

with app.app_context():
    print("Iniciando a criação das tabelas no banco de dados...")
    
    # 1. Cria todas as tabelas
    try:
        db.create_all()
        print("✅ Todas as tabelas criadas com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        exit(1)

    # 2. Cria o usuário admin se ele não existir
    admin_user = User.query.filter_by(username=ADMIN_USERNAME).first()
    
    if not admin_user:
        try:
            # O campo 'email' é opcional no modelo, mas o banco pode ter restrição NOT NULL.
            # Usamos uma string vazia para garantir a compatibilidade.
            hashed_password = generate_password_hash(ADMIN_PASSWORD)
            
            new_admin = User(
                username=ADMIN_USERNAME,
                password=hashed_password,
                role=ADMIN_ROLE,
                email="" # Garante que o campo não seja NULL
            )
            
            db.session.add(new_admin)
            db.session.commit()
            print(f"✅ Usuário admin ('{ADMIN_USERNAME}') criado com sucesso.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao criar usuário admin: {e}")
            exit(1)
    else:
        print(f"ℹ️ Usuário admin ('{ADMIN_USERNAME}') já existe. Ignorando criação.")

    print("Processo de inicialização do banco de dados concluído.")
