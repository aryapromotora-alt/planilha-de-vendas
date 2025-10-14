from flask import Blueprint, jsonify, request, session
from flask_cors import cross_origin
from models.sales import Sale
from models.user import db
from routes.user import load_employees_data
from datetime import date

data_bp = Blueprint('data', __name__)

# 🔄 Carrega dados do banco para o frontend
def load_data_from_db():
    spreadsheetData = {}
    employees = load_employees_data()

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

# 💾 Salva dados recebidos no banco
def save_data_to_db(data):
    try:
        today = date.today()

        for emp_name, days in data.get("spreadsheetData", {}).items():
            for day, value in days.items():
                if day not in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
                    continue

                # Se estiver usando reference_date no modelo Sale:
                sale = Sale.query.filter_by(
                    employee_name=emp_name,
                    day=day,
                    reference_date=today  # ← só se esse campo existir
                ).first() if hasattr(Sale, "reference_date") else Sale.query.filter_by(
                    employee_name=emp_name,
                    day=day
                ).first()

                if sale:
                    sale.value = value
                else:
                    sale = Sale(
                        employee_name=emp_name,
                        day=day,
                        value=value,
                        reference_date=today if hasattr(Sale, "reference_date") else None
                    )
                    db.session.add(sale)

        db.session.commit()
        return True

    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao salvar no banco: {e}")
        return False

# 🔓 Funções públicas para outros módulos
def load_data():
    return load_data_from_db()

def save_data(data):
    return save_data_to_db(data)

# 📥 Rota GET para carregar dados
@data_bp.route('/data', methods=['GET'])
@cross_origin()
def get_data():
    try:
        return jsonify(load_data_from_db()), 200
    except Exception as e:
        return jsonify({"error": f"Erro ao carregar dados: {str(e)}"}), 500

# 📤 Rota POST para salvar dados
@data_bp.route('/data', methods=['POST'])
@cross_origin()
def save_data_endpoint():
    if 'user' not in session:
        return jsonify({"error": "Não autenticado"}), 401

    try:
        data = request.get_json()
        if not data or 'spreadsheetData' not in data:
            return jsonify({"error": "Dados inválidos"}), 400

        if save_data_to_db(data):
            return jsonify({"message": "Dados salvos com sucesso"}), 200
        else:
            return jsonify({"error": "Erro ao salvar no banco"}), 500

    except Exception as e:
        return jsonify({"error": f"Exceção: {str(e)}"}), 500