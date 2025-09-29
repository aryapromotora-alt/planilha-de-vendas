import os
import time
from sqlalchemy.exc import OperationalError
from flask import request, abort
from flask_login import current_user

from __init__ import create_app  # Corrigido: importa da raiz, não da pasta 'app'
from scheduler import start_scheduler
from models.user import db

# Cria a aplicação Flask
app = create_app()

# 🔐 Restrição de acesso externo: só admin pode acessar fora da empresa
@app.before_request
def restringir_acesso_externo():
    # Captura o IP real do visitante, mesmo atrás de proxy
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    ip = ip.split(",")[0].strip()  # pega o primeiro IP da lista

    # Verifica se o IP é da rede interna da empresa
    ip_interno = (
        ip.startswith("192.168.") or
        ip.startswith("10.") or
        ip.startswith("172.")
    )

    # Se estiver fora da empresa e não for admin, bloqueia
    if not ip_interno:
        if not current_user.is_authenticated or getattr(current_user, "role", "") != "admin":
            print(f"[BLOQUEIO] Acesso externo negado para IP {ip}")
            abort(403)

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