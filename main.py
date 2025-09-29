import os
import time
from sqlalchemy.exc import OperationalError
from app import create_app
from scheduler import start_scheduler
from models.user import db

# Cria a aplicação Flask
app = create_app()

# Garante que as tabelas sejam criadas com tolerância ao tempo de boot do banco
with app.app_context():
    for tentativa in range(10):  # tenta por até 10 vezes
        try:
            db.create_all()
            print("✅ Tabelas criadas com sucesso.")
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