import os
import json
from flask import Blueprint, jsonify, current_app, request, render_template
from datetime import datetime, timedelta
from .data import load_data, save_data

archive_bp = Blueprint('archive', __name__)

# Arquivo onde fica salvo o histórico
HISTORY_FILE = os.path.join(os.path.dirname(__file__), '..', 'database', 'weekly_history.json')


# ---------------------------
# Funções auxiliares
# ---------------------------
def load_history():
    """Carrega histórico do arquivo JSON"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_history(history):
    """Salva histórico no arquivo JSON"""
    try:
        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        return True
    except IOError:
        return False


# ---------------------------
# Rota para arquivar semana
# ---------------------------
@archive_bp.route('/api/weekly-archive', methods=['POST'])
def weekly_archive():
    """
    Fecha a semana:
    - Salva totais no histórico
    - Zera a planilha
    """
    # segurança opcional com secret key
    secret = current_app.config.get('WEEKLY_ARCHIVE_SECRET')
    header = request.headers.get('X-SECRET-KEY')
    if secret and header != secret:
        return jsonify({"error": "unauthorized"}), 401

    data = load_data()
    spreadsheet = data.get("spreadsheetData", {})

    # total por vendedor
    per_seller = []
    total = 0
    for nome, valores in spreadsheet.items():
        soma = sum([
            valores.get("monday", 0),
            valores.get("tuesday", 0),
            valores.get("wednesday", 0),
            valores.get("thursday", 0),
            valores.get("friday", 0),
        ])
        total += soma
        per_seller.append({"seller": nome, "total": soma})

    # intervalo da semana (seg a sex)
    now = datetime.utcnow()
    start = now - timedelta(days=now.weekday())   # segunda
    end = start + timedelta(days=4)               # sexta
    week_label = f"{start.date()} a {end.date()}"

    # salva histórico
    history = load_history()
    history.append({
        "week_label": week_label,
        "started_at": str(start.date()),
        "ended_at": str(end.date()),
        "total": total,
        "breakdown": per_seller,
        "created_at": datetime.utcnow().isoformat()
    })
    save_history(history)

    # zera planilha
    for nome, valores in spreadsheet.items():
        valores["monday"] = 0
        valores["tuesday"] = 0
        valores["wednesday"] = 0
        valores["thursday"] = 0
        valores["friday"] = 0
    save_data(data)

    return jsonify({"status": "ok", "week": week_label, "total": total})


# ---------------------------
# Rota para visualizar histórico no navegador
# ---------------------------
@archive_bp.route('/weekly', methods=['GET'])
def weekly_page():
    """
    Mostra o histórico semanal em uma página HTML
    """
    history = load_history()
    # ordena do mais recente para o mais antigo
    history = sorted(history, key=lambda x: x.get("created_at", ""), reverse=True)
    return render_template("weekly.html", history=history)
