import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
import datetime

app = Flask(__name__)
CORS(app)
DATABASE = 'equipment_lending.db'

# -------------------- DB SETUP -------------------- #
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT,
        token TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS equipment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        category TEXT,
        cond TEXT,
        total_quantity INTEGER,
        available_quantity INTEGER
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        item_id INTEGER,
        status TEXT,
        request_date TEXT,
        approve_date TEXT,
        return_date TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(item_id) REFERENCES equipment(id)
    )""")
    conn.commit()
    # Seed default admin
    cur.execute("SELECT * FROM users WHERE email=?", ('2024tm93169@wilp.bits-pilani.ac.in',))
    admin = cur.fetchone()
    if admin is None:
        cur.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                    ('Admin User', '2024tm93169@wilp.bits-pilani.ac.in', 'admin', 'admin'))
        conn.commit()
    conn.close()

init_db()

# -------------------- AUTH HELPER -------------------- #
def authenticate():
    token = None
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ', 1)[1]
    if not token:
        return None
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name, email, LOWER(role) AS role FROM users WHERE token=?", (token,))
    user = cur.fetchone()
    conn.close()
    return user

# -------------------- AUTH ROUTES -------------------- #
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password') or not data.get('name'):
        return jsonify({'error': 'Name, email, and password are required'}), 400
    name = data['name']
    email = data['email']
    password = data['password']
    role = data.get('role', 'student')
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                    (name, email, password, role))
        conn.commit()
        user_id = cur.lastrowid
        conn.close()
        return jsonify({'message': 'Signup successful', 'user_id': user_id}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Email already registered'}), 409

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    email = data['email']
    password = data['password']
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name, email, role, password FROM users WHERE email=?", (email,))
    user = cur.fetchone()
    if user is None:
        conn.close()
        return jsonify({'error': 'Invalid credentials'}), 401
    user = dict(user)
    if password != user['password']:
        conn.close()
        return jsonify({'error': 'Invalid credentials'}), 401
    token = str(uuid.uuid4())
    cur.execute("UPDATE users SET token=? WHERE id=?", (token, user['id']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Login successful', 'token': token,
                    'user': {'id': user['id'], 'name': user['name'], 'email': user['email'], 'role': user['role']}})

# Aliases (for frontend using /api/auth/*)
@app.route('/api/auth/login', methods=['POST'])
def _alias_login():
    return login()

@app.route('/api/auth/signup', methods=['POST'])
def _alias_signup():
    return signup()

# -------------------- EQUIPMENT -------------------- #
@app.route('/api/equipment', methods=['GET'])
def list_equipment():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM equipment")
    rows = cur.fetchall()
    equipment_list = [dict(row) for row in rows]
    conn.close()
    return jsonify(equipment_list)

@app.route('/api/equipment', methods=['POST'])
def add_equipment():
    user = authenticate()
    if not user or user['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    required = ['name', 'category', 'cond', 'total_quantity']
    if not data or any(field not in data for field in required):
        return jsonify({'error': 'Missing fields'}), 400
    name = data['name']
    category = data['category']
    cond = data['cond']
    total = int(data['total_quantity'])
    avail = total
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO equipment (name, category, cond, total_quantity, available_quantity) VALUES (?, ?, ?, ?, ?)",
                (name, category, cond, total, avail))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return jsonify({'message': 'Equipment added', 'equipment_id': new_id}), 201

@app.route('/api/equipment/<int:item_id>', methods=['PUT'])
def update_equipment(item_id):
    user = authenticate()
    if not user or user['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    fields, values = [], []
    conn = get_db()
    cur = conn.cursor()
    if 'total_quantity' in data:
        cur.execute("SELECT total_quantity, available_quantity FROM equipment WHERE id=?", (item_id,))
        rec = cur.fetchone()
        if not rec:
            conn.close()
            return jsonify({'error': 'Item not found'}), 404
        old_total = rec['total_quantity']
        old_avail = rec['available_quantity']
        new_total = int(data['total_quantity'])
        diff = new_total - old_total
        new_avail = max(0, old_avail + diff)
        fields += ["total_quantity=?", "available_quantity=?"]
        values += [new_total, new_avail]
    for f in ['name', 'category', 'cond']:
        if f in data:
            fields.append(f"{f}=?")
            values.append(data[f])
    if not fields:
        conn.close()
        return jsonify({'error': 'No fields to update'}), 400
    cur.execute("UPDATE equipment SET " + ", ".join(fields) + " WHERE id=?", (*values, item_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Equipment updated'})

@app.route('/api/equipment/<int:item_id>', methods=['DELETE'])
def delete_equipment(item_id):
    user = authenticate()
    if not user or user['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM equipment WHERE id=?", (item_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Equipment deleted'})

# -------------------- REQUESTS -------------------- #
@app.route('/api/requests', methods=['POST'])
def create_request():
    user = authenticate()
    if not user or user['role'] not in ['student', 'staff']:
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    if not data or not data.get('item_id'):
        return jsonify({'error': 'Item ID required'}), 400
    item_id = data['item_id']
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT available_quantity FROM equipment WHERE id=?", (item_id,))
    item = cur.fetchone()
    if item is None:
        conn.close()
        return jsonify({'error': 'Item not found'}), 404
    if item['available_quantity'] <= 0:
        conn.close()
        return jsonify({'error': 'Item not available'}), 400
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("INSERT INTO requests (user_id, item_id, status, request_date) VALUES (?, ?, ?, ?)",
                (user['id'], item_id, 'PENDING', now))
    conn.commit()
    request_id = cur.lastrowid
    conn.close()
    return jsonify({'message': 'Request submitted', 'request_id': request_id}), 201

@app.route('/api/requests', methods=['GET'])
def get_requests():
    user = authenticate()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db()
    cur = conn.cursor()
    if user['role'] == 'admin':
        cur.execute("""
            SELECT r.id, UPPER(r.status) AS status, r.request_date, r.approve_date, r.return_date,
                   u.name AS user_name, u.email AS user_email,
                   e.name AS item_name
            FROM requests r
            JOIN users u ON r.user_id = u.id
            JOIN equipment e ON r.item_id = e.id
            ORDER BY r.id DESC
        """)
    else:
        cur.execute("""
            SELECT r.id, UPPER(r.status) AS status, r.request_date, r.approve_date, r.return_date,
                   e.name AS item_name
            FROM requests r
            JOIN equipment e ON r.item_id = e.id
            WHERE r.user_id = ?
            ORDER BY r.id DESC
        """, (user['id'],))
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(rows)

def update_request_status(req_id, new_status):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM requests WHERE id=?", (req_id,))
    req = cur.fetchone()
    if not req:
        conn.close()
        return None, {'error': 'Request not found'}
    req = dict(req)
    if new_status == 'APPROVED':
        if req['status'].upper() != 'PENDING':
            conn.close()
            return None, {'error': 'Request already processed'}
        cur.execute("SELECT available_quantity FROM equipment WHERE id=?", (req['item_id'],))
        item = cur.fetchone()
        if item and item['available_quantity'] <= 0:
            conn.close()
            return None, {'error': 'Item not available'}
        approve_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("UPDATE requests SET status=?, approve_date=? WHERE id=?", (new_status, approve_date, req_id))
        cur.execute("UPDATE equipment SET available_quantity = available_quantity - 1 WHERE id=?", (req['item_id'],))
        conn.commit()
        conn.close()
        return new_status, None
    elif new_status == 'REJECTED':
        if req['status'].upper() != 'PENDING':
            conn.close()
            return None, {'error': 'Request already processed'}
        cur.execute("UPDATE requests SET status=? WHERE id=?", (new_status, req_id))
        conn.commit()
        conn.close()
        return new_status, None
    elif new_status == 'RETURNED':
        if req['status'].upper() != 'APPROVED':
            conn.close()
            return None, {'error': 'Return not applicable'}
        return_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("UPDATE requests SET status=?, return_date=? WHERE id=?", (new_status, return_date, req_id))
        cur.execute("UPDATE equipment SET available_quantity = available_quantity + 1 WHERE id=?", (req['item_id'],))
        conn.commit()
        conn.close()
        return new_status, None
    else:
        conn.close()
        return None, {'error': 'Invalid status'}

@app.route('/api/requests/<int:req_id>/approve', methods=['POST'])
def approve_request(req_id):
    user = authenticate()
    if not user or user['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    status, error = update_request_status(req_id, 'APPROVED')
    if not status:
        return jsonify(error), 400
    return jsonify({'message': 'Request approved'})

@app.route('/api/requests/<int:req_id>/reject', methods=['POST'])
def reject_request(req_id):
    user = authenticate()
    if not user or user['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    status, error = update_request_status(req_id, 'REJECTED')
    if not status:
        return jsonify(error), 400
    return jsonify({'message': 'Request rejected'})

@app.route('/api/requests/<int:req_id>/return', methods=['POST'])
def return_request(req_id):
    user = authenticate()
    if not user or user['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    status, error = update_request_status(req_id, 'RETURNED')
    if not status:
        return jsonify(error), 400
    return jsonify({'message': 'Marked as returned'})

# -------------------- ANALYTICS -------------------- #
@app.route('/api/analytics', methods=['GET'])
def analytics():
    user = authenticate()
    if not user or user['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM equipment")
    total_equip = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE role!='admin'")
    total_users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM requests")
    total_requests = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM requests WHERE UPPER(status)='APPROVED'")
    active_loans = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM requests WHERE UPPER(status)='PENDING'")
    pending_requests = cur.fetchone()[0]
    cur.execute("SELECT e.name, COUNT(r.id) as cnt FROM requests r JOIN equipment e ON r.item_id = e.id GROUP BY r.item_id ORDER BY cnt DESC LIMIT 1")
    top = cur.fetchone()
    top_item = top['name'] if top else None
    conn.close()
    return jsonify({
        'total_equipment': total_equip,
        'total_users': total_users,
        'total_requests': total_requests,
        'active_loans': active_loans,
        'pending_requests': pending_requests,
        'most_requested_item': top_item
    })

# -------------------- DEBUG / HOME -------------------- #
@app.route('/api/debug/whoami', methods=['GET'])
def whoami():
    user = authenticate()
    if not user:
        return jsonify({'auth': False})
    return jsonify({'auth': True, 'id': user['id'], 'email': user['email'], 'role': user['role']})

@app.route('/')
def home():
    return "Backend running successfully!"

@app.route('/favicon.ico')
def favicon():
    return '', 204

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)
