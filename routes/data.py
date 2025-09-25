import os
import json
from flask import Blueprint, jsonify, request
from flask_cors import cross_origin

data_bp = Blueprint('data', __name__)

# Caminho para o arquivo de dados
DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'database', 'planilha_data.json')

def load_data():
    """Carrega os dados do arquivo JSON"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)

                # Gerar campo 'ordem' com base na posição dos nomes em employees
                ordem_map = {emp["name"]: i for i, emp in enumerate(data.get("employees", []), start=1)}
                for nome, valores in data.get("spreadsheetData", {}).items():
                    valores["ordem"] = ordem_map.get(nome, 999)

                return data
        except (json.JSONDecodeError, IOError):
            pass

    # Dados padrão se o arquivo não existir ou estiver corrompido
    default_employees = [
        {"name": "admin", "password": "minha_senha_secreta"},
        {"name": "Anderson", "password": "123"},
        {"name": "Vitoria", "password": "123"},
        {"name": "Jemima", "password": "123"},
        {"name": "Maiany", "password": "123"},
        {"name": "Fernanda", "password": "123"},
        {"name": "Nadia", "password": "123"},
        {"name": "Giovana", "password": "123"}
    ]

    spreadsheet = {
        emp["name"]: {
            "monday": 0,
            "tuesday": 0,
            "wednesday": 0,
            "thursday": 0,
            "friday": 0,
            "ordem": i + 1
        }
        for i, emp in enumerate(default_employees)
    }

    return {
        "employees": default_employees,
        "spreadsheetData": spreadsheet
    }

def save_data(data):
    """Salva os dados no arquivo JSON"""
    try:
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except IOError:
        return False

@data_bp.route('/data', methods=['GET'])
@cross_origin()
def get_data():
    """Retorna todos os dados da planilha"""
    try:
        data = load_data()
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@data_bp.route('/data', methods=['POST'])
@cross_origin()
def save_data_endpoint():
    """Salva os dados da planilha"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Nenhum dado fornecido"}), 400

        # Validar estrutura básica dos dados
        if 'employees' not in data or 'spreadsheetData' not in data:
            return jsonify({"error": "Estrutura de dados inválida"}), 400

        # Recalcular campo 'ordem' com base na nova lista de employees
        ordem_map = {emp["name"]: i for i, emp in enumerate(data.get("employees", []), start=1)}
        for nome, valores in data.get("spreadsheetData", {}).items():
            valores["ordem"] = ordem_map.get(nome, 999)

        if save_data(data):
            return jsonify({"message": "Dados salvos com sucesso"}), 200
        else:
            return jsonify({"error": "Erro ao salvar dados"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500