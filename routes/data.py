from flask import Blueprint, jsonify, request, session
from flask_cors import cross_origin
from models.sales import Sale
from models.user import db
from routes.user import load_employees_data  # ← Importa os dados reais do JSON

data_bp = Blueprint('data', __name__)

def load_data_from_db():
    spreadsheetData = {}
    employees = load_employees_data()  # ← Carrega os funcionários do JSON
    for emp in employees:
        sales = Sale.query.filter_by(employee_name=emp["name"]).all()
        day_values = {sale.day: sale.value for sale in sales}
        spreadsheetData[emp["name"]] = {
            "monday": day_values.get("monday", 0),
            "tuesday": day_values.get("tuesday", 0),
            "wednesday": day_values.get("wednesday", 0),
            "thursday": day_values.get("thursday", 0),
            "friday": day_values.get("friday", 0),
        }
    return {
        "employees": employees,
        "spreadsheetData": spreadsheetData
    }

def save_data_to_db(data):
    try:
        for emp_name, days in data["spreadsheetData"].items():
            for day, value in days.items():
                if day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
                    sale = Sale.query.filter_by(employee_name=emp_name, day=day).first()
                    if sale:
                        sale.value = value
                    else:
                        sale = Sale(employee_name=emp_name, day=day, value=value)
                        db.session.add(sale)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao salvar: {e}")
        return False

# 🔑 FUNÇÕES PÚBLICAS PARA O archive.py
def load_data():
    return load_data_from_db()

def save_data(data):
    return save_data_to_db(data)

# Rotas da API
@data_bp.route('/data', methods=['GET'])
@cross_origin()
def get_data():
    try:
        return jsonify(load_data_from_db()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@data_bp.route('/data', methods=['POST'])
@cross_origin()
def save_data_endpoint():
    if 'user' not in session:
        return jsonify({"error": "Não autenticado"}), 401
    try:
        data = request.get_json()
        if not data or 'employees' not in data or 'spreadsheetData' not in data:
            return jsonify({"error": "Dados inválidos"}), 400
        if save_data_to_db(data):
            return jsonify({"message": "Dados salvos"}), 200
        else:
            return jsonify({"error": "Erro ao salvar"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500