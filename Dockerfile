FROM python:3.10-slim

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 5000

# Inicia diretamente o Gunicorn — o main.py já cuida da inicialização do banco
CMD ["gunicorn", "main:application", "-b", "0.0.0.0:5000"]