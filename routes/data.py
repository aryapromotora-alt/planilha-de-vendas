# routes/data.py
from flask import Blueprint, jsonify, request, session
from flask_cors import cross_origin
from models.sales import Sale
from models.user import User, db

data_bp = Blueprint('data', __name__)

def load_data_from_db(sheet_type='portabilidade'):
    spreadsheetData = {}
    employees = User.query.filter_by(role='user').all()
    for emp in employees:
        sales = Sale.query.filter_by(employee_name=emp.username, sheet_type=sheet_type).all()
        day_values = {sale.day: sale.value for sale in sales}
        spreadsheetData[emp.username] = {
            "monday": day_values.get("monday", 0),
            "tuesday": day_values.get("tuesday", 0),
            "wednesday": day_values.get("wednesday", 0),
            "thursday": day_values.get("thursday", 0),
            "friday": day_values.get("friday", 0),
        }
    return {
        "employees": [emp.to_dict() for emp in employees],
        "spreadsheetData": spreadsheetData
    }

def save_data_to_db(data, sheet_type='portabilidade'):
    try:
        spreadsheet_data = data.get("spreadsheetData", {})
        for emp_name, days in spreadsheet_data.items():
            for day, value in days.items():
                if day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
                    sale = Sale.query.filter_by(
                        employee_name=emp_name,
                        day=day,
                        sheet_type=sheet_type
                    ).first()
                    if sale:
                        sale.value = value
                    else:
                        sale = Sale(
                            employee_name=emp_name,
                            day=day,
                            value=value,
                            sheet_type=sheet_type
                        )
                        db.session.add(sale)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao salvar: {e}")
        return False

# 🔑 FUNÇÕES PÚBLICAS PARA COMPATIBILIDADE (ex: archive.py)
def load_data():
    return load_data_from_db('portabilidade')

def save_data(data):
    return save_data_to_db(data, 'portabilidade')

# === Nova função: salvar apenas uma célula ===
def save_cell_to_db(sheet_type, employee_name, day, value):
    """
    Salva ou atualiza APENAS uma célula no banco de dados.
    """
    try:
        # Validações básicas
        if sheet_type not in ['portabilidade', 'novo']:
            return False, "Tipo de planilha inválido"
        if day not in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
            return False, "Dia da semana inválido"
        if not isinstance(value, (int, float)):
            value = float(value) if value else 0.0

        # Busca ou cria o registro
        sale = Sale.query.filter_by(
            employee_name=employee_name,
            day=day,
            sheet_type=sheet_type
        ).first()

        if sale:
            sale.value = value
        else:
            sale = Sale(
                employee_name=employee_name,
                day=day,
                value=value,
                sheet_type=sheet_type
            )
            db.session.add(sale)

        db.session.commit()
        return True, "Célula salva com sucesso"
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao salvar célula: {e}")
        return False, str(e)

# === Rotas da API ===

@data_bp.route('/data', methods=['GET'])
@cross_origin()
def get_data():
    try:
        sheet_type = request.args.get('type', 'portabilidade')
        if sheet_type not in ['portabilidade', 'novo']:
            sheet_type = 'portabilidade'
        return jsonify(load_data_from_db(sheet_type)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@data_bp.route('/data', methods=['POST'])
@cross_origin()
def save_data_endpoint():
    if 'user' not in session:
        return jsonify({"error": "Não autenticado"}), 401
    try:
        data = request.get_json()
        if not data or 'spreadsheetData' not in data:
            return jsonify({"error": "Dados inválidos"}), 400
        
        sheet_type = data.get('sheet_type', 'portabilidade')
        if sheet_type not in ['portabilidade', 'novo']:
            sheet_type = 'portabilidade'

        if save_data_to_db(data, sheet_type):
            return jsonify({"message": "Dados salvos"}), 200
        else:
            return jsonify({"error": "Erro ao salvar"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === Nova rota: salvar uma única célula ===
@data_bp.route('/cell', methods=['POST'])
@cross_origin()
def save_cell_endpoint():
    if 'user' not in session:
        return jsonify({"error": "Não autenticado"}), 401

    try:
        data = request.get_json()
        sheet_type = data.get('sheet_type')
        employee = data.get('employee')
        day = data.get('day')
        value = data.get('value', 0)

        if not all([sheet_type, employee, day]):
            return jsonify({"error": "Dados incompletos"}), 400

        success, message = save_cell_to_db(sheet_type, employee, day, value)
        if success:
            return jsonify({"success": True, "message": message}), 200
        else:
            return jsonify({"error": message}), 500

    except Exception as e:
        print(f"Erro na rota /cell: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500