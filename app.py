# app.py - Servidor Flask do TaskFlow Web
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import task_manager
import habits_manager
import shopping_list_manager
import bill_reminder

app = Flask(__name__)
CORS(app)


# ── Tradutores de Modelos para o Frontend ─────────────────────────────────────

def _task_to_frontend(t):
    return {
        "id": int(t["id"]) if t["id"].isdigit() else t["id"],
        "title": t["title"],
        "due_date": t.get("due_date"),
        "reminder_time": t.get("reminder_time"),
        "advance_minutes": t.get("remind_before_minutes", 5),
        "is_completed": t.get("status") == "concluída",
        "created_at": t.get("created_at")
    }


def _habit_to_frontend(h):
    return {
        "id": int(h["id"]) if h["id"].isdigit() else h["id"],
        "name": h["title"],
        "interval_minutes": h["interval_minutes"],
        "last_notified_at": h.get("last_reminder_at")
    }


def _shopping_to_frontend(i):
    qty_str = i.get("quantity", "1").replace(",", ".")
    try:
        qty = float(qty_str)
        if qty.is_integer():
            qty = int(qty)
    except ValueError:
        qty = 1.0

    price_str = i.get("price", "0,00").replace(".", "").replace(",", ".")
    try:
        price = float(price_str)
    except ValueError:
        price = 0.0

    return {
        "id": int(i["id"]) if i["id"].isdigit() else i["id"],
        "item_name": i["name"],
        "quantity": qty,
        "price": price,
        "is_bought": bool(i.get("checked", False)),
        "created_at": i.get("created_at")
    }


def _bill_to_frontend(b):
    val_str = b.get("valor", "0.00").replace(",", ".")
    try:
        val = float(val_str)
    except ValueError:
        val = 0.0
    return {
        "id": int(b["id"]) if b.get("id", "").isdigit() else b.get("id"),
        "name": b["nome"],
        "value": val,
        "due_date": b["vencimento"]
    }


# ── Rotas do Frontend ─────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


# ── API de Tarefas ───────────────────────────────────────────────────────────

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    tasks = task_manager.list_tasks()
    return jsonify([_task_to_frontend(t) for t in tasks])


@app.route('/api/tasks', methods=['POST'])
def add_task():
    data = request.json
    t = task_manager.add_task(
        title=data['title'],
        due_date=data.get('due_date'),
        reminder_time=data.get('reminder_time'),
        remind_before_minutes=data.get('advance_minutes', 5)
    )
    return jsonify(_task_to_frontend(t)), 201


@app.route('/api/tasks/<task_id>/complete', methods=['POST'])
def complete_task(task_id):
    task_manager.complete_task(str(task_id))
    tasks = task_manager.list_tasks()
    for t in tasks:
        if t["id"] == str(task_id):
            return jsonify(_task_to_frontend(t))
    return jsonify({"error": "Task not found"}), 404


@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    task_manager.delete_task(str(task_id))
    return jsonify({'success': True})


# ── API de Hábitos ────────────────────────────────────────────────────────────

@app.route('/api/habits', methods=['GET'])
def get_habits():
    habits = habits_manager.list_habits()
    return jsonify([_habit_to_frontend(h) for h in habits])


@app.route('/api/habits', methods=['POST'])
def add_habit():
    data = request.json
    h = habits_manager.add_habit(
        title=data['name'],
        interval_minutes=data['interval_minutes']
    )
    return jsonify(_habit_to_frontend(h)), 201


@app.route('/api/habits/<habit_id>', methods=['DELETE'])
def delete_habit(habit_id):
    habits_manager.delete_habit(str(habit_id))
    return jsonify({'success': True})


@app.route('/api/habits/<habit_id>/remind', methods=['POST'])
def remind_habit(habit_id):
    habits_manager.send_habit_reminder_now(str(habit_id))
    return jsonify({'success': True})


# ── API de Compras ───────────────────────────────────────────────────────────

@app.route('/api/shopping', methods=['GET'])
def get_shopping():
    items = shopping_list_manager.list_items()
    return jsonify([_shopping_to_frontend(i) for i in items])


@app.route('/api/shopping', methods=['POST'])
def add_shopping_item():
    data = request.json
    qty = str(data.get('quantity', 1))
    price = f"{float(data.get('price', 0)):.2f}".replace(".", ",")
    item = shopping_list_manager.add_item(
        name=data['item_name'],
        quantity=qty,
        price=price
    )
    return jsonify(_shopping_to_frontend(item)), 201


@app.route('/api/shopping/<item_id>', methods=['PUT'])
def update_shopping_item(item_id):
    shopping_list_manager.toggle_item(str(item_id))
    items = shopping_list_manager.list_items()
    for i in items:
        if i["id"] == str(item_id):
            return jsonify(_shopping_to_frontend(i))
    return jsonify({"error": "Item not found"}), 404


@app.route('/api/shopping/<item_id>', methods=['DELETE'])
def delete_shopping_item(item_id):
    shopping_list_manager.delete_item(str(item_id))
    return jsonify({'success': True})


@app.route('/api/shopping/clear-bought', methods=['POST'])
def clear_bought():
    shopping_list_manager.clear_checked()
    return jsonify({'success': True})


# ── API de Contas ────────────────────────────────────────────────────────────

@app.route('/api/bills', methods=['GET'])
def get_bills():
    bills = bill_reminder._read_bills()
    return jsonify([_bill_to_frontend(b) for b in bills])


@app.route('/api/bills', methods=['POST'])
def add_bill():
    data = request.json
    val = f"{float(data['value']):.2f}"
    b = bill_reminder.add_bill(
        nome=data['name'],
        valor=val,
        vencimento=data['due_date']
    )
    return jsonify(_bill_to_frontend(b)), 201


@app.route('/api/bills/<bill_id>', methods=['DELETE'])
def delete_bill(bill_id):
    bill_reminder.delete_bill(str(bill_id))
    return jsonify({'success': True})


# ── Inicialização ─────────────────────────────────────────────────────────────

if __name__ == '__main__':
    # Sincronização inicial em background ao subir o servidor web
    print("[Supabase] Sincronizando com o Supabase antes de abrir o servidor...")
    task_manager.sync_with_supabase()
    habits_manager.sync_with_supabase()
    shopping_list_manager.sync_with_supabase()
    bill_reminder.sync_with_supabase()

    print("[Flask] TaskFlow Web iniciado!")
    print("[Flask] Acesse: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
