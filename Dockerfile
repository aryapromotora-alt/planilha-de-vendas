FROM python:3.10-slim

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 5000

# Comando corrigido:
# 1. Executa o script de inicialização do banco de dados (cria tabelas e admin).
# 2. Se o script for bem-sucedido (&&), inicia o servidor Gunicorn.
CMD ["/bin/bash", "-c", "python3 init_db.py && gunicorn main:application -b 0.0.0.0:5000"]
