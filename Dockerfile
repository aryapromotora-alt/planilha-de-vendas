FROM python:3.10-slim

# Define diretório de trabalho
WORKDIR /app

# Copia dependências primeiro (melhora cache)
COPY requirements.txt .

# Instala dependências
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código
COPY . .

# Expõe a porta (precisa bater com a do Northflank)
EXPOSE 5000

# Comando de inicialização (Gunicorn)
# main:app -> significa arquivo main.py com variável "app"
CMD ["gunicorn", "-b", "0.0.0.0:5000", "main:app"]
