from flask import Blueprint, jsonify, request, session
from flask_cors import cross_origin
from models.sales import Sale
from models.user import db

data_bp = Blueprint('data', __name__)

# Lista fixa de funcionários (pode ser movida para tabela depois)
EMPLOYEES = [
    {"name": "Anderson", "password": "123"},
    {"name": "Vitoria", "password": "123"},
    {"name": "Jemima", "password": "123"},
    {"name": "Maiany", "password": "123"},
    {"name": "Fernanda", "password": "123"},
    {"name": "Nadia", "password": "123"},
    {"name": "Giovana", "password": "123"}
]

def load_data_from_db():
    spreadsheetData = {}
    for emp in EMPLOYEES:
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
        "employees": EMPLOYEES,
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

@data_bp.route('/data', methods=['GET'])
@cross_origin()
def get_data():
    try:
        data = load_data_from_db()
        return jsonify(data), 200
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