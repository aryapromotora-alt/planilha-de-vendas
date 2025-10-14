FROM python:3.10-slim

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 5000

# Primeiro: executa init_db.py para garantir que o banco esteja pronto
# Depois: inicia o Gunicorn
CMD ["/bin/bash", "-c", "python3 init_db.py && gunicorn main:application -b 0.0.0.0:5000"]00"]