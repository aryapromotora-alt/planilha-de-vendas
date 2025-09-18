import os
from app import create_app
from scheduler import start_scheduler
from models.user import db

# Cria a aplicação Flask
app = create_app()

# Garante que as tabelas sejam criadas
with app.app_context():
    db.create_all()

# Inicia o agendador de tarefas
start_scheduler(app)

# Executa o servidor local (útil para testes)
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)

# Exporta a aplicação para uso com Gunicorn
application = app