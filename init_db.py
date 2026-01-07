import os
from app import create_app
from models.user import db, User
from models.sales import Sale  # Importante para garantir que a tabela 'sales' seja criada
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

    # 2. Garante que a coluna 'password' exista e tenha tamanho suficiente (256)
    try:
        result = db.session.execute(text("""
            SELECT column_name, character_maximum_length
            FROM information_schema.columns 
            WHERE table_name = 'user' AND column_name = 'password';
        """))
        row = result.fetchone()
        if not row:
            print("⚠️ Coluna 'password' não encontrada. Adicionando...")
            db.session.execute(text('ALTER TABLE "user" ADD COLUMN password VARCHAR(256) NOT NULL DEFAULT \'\';'))
            db.session.commit()
            print("✅ Coluna 'password' adicionada com tamanho 256.")
        else:
            current_length = row[1]
            if current_length < 256:
                print(f"⚠️ Coluna 'password' tem tamanho {current_length}. Aumentando para 256...")
                db.session.execute(text('ALTER TABLE "user" ALTER COLUMN password TYPE VARCHAR(256);'))
                db.session.commit()
                print("✅ Tamanho da coluna 'password' atualizado para 256.")
            else:
                print("✅ Coluna 'password' já existe com tamanho adequado.")
    except Exception as e:
        print(f"❌ Erro ao verificar/ajustar coluna 'password': {e}")
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

    # 3.1 Garante que a coluna 'order' exista
    try:
        result = db.session.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'user' AND column_name = 'order';
        """))
        if not result.fetchone():
            print("⚠️ Coluna 'order' não encontrada. Adicionando...")
            db.session.execute(text('ALTER TABLE "user" ADD COLUMN "order" INTEGER DEFAULT 0;'))
            db.session.commit()
            print("✅ Coluna 'order' adicionada.")
        else:
            print("✅ Coluna 'order' já existe.")
    except Exception as e:
        print(f"❌ Erro ao verificar/criar coluna 'order': {e}")
        exit(1)

    # 4. Garante que a coluna 'sheet_type' exista na tabela 'sales'
    sheet_type_exists = False
    try:
        # Tenta verificar via information_schema (PostgreSQL/MySQL)
        result = db.session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'sales' AND column_name = 'sheet_type';
        """))
        if result.fetchone():
            sheet_type_exists = True
            print("✅ Coluna 'sheet_type' já existe na tabela 'sales'.")
    except Exception as e_info:
        # Se falhar (ex: SQLite), tenta acessar diretamente
        try:
            db.session.execute(text("SELECT sheet_type FROM sales LIMIT 1;"))
            sheet_type_exists = True
            print("✅ Coluna 'sheet_type' já existe na tabela 'sales'.")
        except:
            sheet_type_exists = False

    if not sheet_type_exists:
        try:
            print("⚠️ Coluna 'sheet_type' não encontrada. Adicionando...")
            db.session.execute(text("ALTER TABLE sales ADD COLUMN sheet_type VARCHAR(20) DEFAULT 'portabilidade';"))
            db.session.commit()
            print("✅ Coluna 'sheet_type' adicionada à tabela 'sales'.")
        except Exception as e_alter:
            print(f"❌ Erro ao adicionar coluna 'sheet_type': {e_alter}")
            # Não sai do script — continua mesmo se falhar (ex: coluna já existe por outro motivo)
    else:
        print("✅ Coluna 'sheet_type' já está presente.")

    # 5. Cria o usuário admin se não existir
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