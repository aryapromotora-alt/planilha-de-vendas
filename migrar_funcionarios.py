import os
import json
from app import create_app
from models.user import db, User

# Inicializa a aplicação Flask
app = create_app()

def migrar_funcionarios():
    # Caminho do arquivo JSON com os dados antigos
    DATA_FILE = os.path.join(os.path.dirname(__file__), "database", "planilha_data.json")
    if not os.path.exists(DATA_FILE):
        print("❌ Arquivo planilha_data.json não encontrado.")
        return

    with app.app_context():
        # Carrega os dados do JSON
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            employees = data.get("employees", [])

        # Itera sobre cada funcionário
        for emp in employees:
            nome = emp.get("name")
            senha = emp.get("password")
            email = f"{nome.lower()}@sistema.local"  # Email fictício obrigatório

            if not nome or not senha:
                print(f"⚠️ Funcionário inválido: {emp}")
                continue

            # Evita duplicatas
            if User.query.filter_by(username=nome).first():
                print(f"🔁 Usuário já existe: {nome}")
                continue

            # Cria e salva o usuário no banco
            novo_user = User(username=nome, email=email)
            novo_user.set_password(senha)
            db.session.add(novo_user)
            print(f"✅ Migrado: {nome}")

        db.session.commit()
        print("🎉 Migração concluída com sucesso.")

# Executa a função se o script for rodado diretamente
if __name__ == "__main__":
    migrar_funcionarios()