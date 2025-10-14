import os
import time
from sqlalchemy.exc import OperationalError
from app import create_app
from scheduler import start_scheduler
from models.user import db
from sqlalchemy import text  # ← adicionado para rodar SQL diretamente

# Cria a aplicação Flask
app = create_app()

# Garante que as tabelas sejam criadas e que a coluna 'password' exista
with app.app_context():
    for tentativa in range(10):  # tenta por até 10 vezes
        try:
            # Primeiro, cria as tabelas se não existirem
            db.create_all()
            
            # Depois, garante que a coluna 'password' exista na tabela 'user'
            try:
                result = db.session.execute(text("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'user' AND column_name = 'password';
                """))
                if not result.fetchone():
                    # Adiciona a coluna se não existir
                    db.session.execute(text('ALTER TABLE "user" ADD COLUMN password VARCHAR(128) NOT NULL DEFAULT \'\';'))
                    db.session.commit()
                    print("✅ Coluna 'password' adicionada à tabela 'user'.")
                else:
                    print("✅ Coluna 'password' já existe.")
            except Exception as col_err:
                print(f"⚠️ Erro ao verificar/criar coluna 'password': {col_err}")
            
            print("✅ Tabelas e colunas verificadas com sucesso.")
            break
        except OperationalError as e:
            print(f"⚠️ Tentativa {tentativa + 1}: banco ainda não está pronto. Aguardando...")
            time.sleep(3)
    else:
        print("❌ Erro: banco não respondeu após múltiplas tentativas.")

# Inicia o agendador de tarefas
try:
    start_scheduler(app)
    print("🕒 Agendador iniciado com sucesso.")
except Exception as e:
    print(f"⚠️ Erro ao iniciar scheduler: {e}")

# Executa o servidor local (útil para testes)
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)

# Exporta a aplicação para uso com Gunicorn
application = app