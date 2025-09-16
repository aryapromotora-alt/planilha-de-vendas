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

if __name__ == '__main__':
    import os
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)), debug=True)

