from flask import Flask, render_template, request, redirect, session
import sqlite3
import hashlib
import os
from functools import wraps
from datetime import datetime, timedelta
import time

app = Flask(__name__)

# -------- USERS --------
users = {
    "Huruma": {
        "password": "1234",
        "balance": 100,
        "wallet": "LDP-HURUMA-001"
    },
    "Alfred": {
        "password": "1234",
        "balance": 500,
        "wallet": "LDP-ALFRED-001"
    }
}

# -------- MINING SETTINGS --------
MAX_SUPPLY = 1000000000
TOTAL_MINED = 0

MINE_RATE_PER_DAY = 2.4
MINE_PER_CLICK = MINE_RATE_PER_DAY / 24

# -------- COOLDOWN --------
mine_cooldown = {}
send_cooldown = {}

app.secret_key = os.environ.get("SECRET_KEY", "mysecret123")
app.permanent_session_lifetime = timedelta(minutes=30)

DB = 'database.db'

# ------------------------
# INIT DB
# ------------------------
def init_db():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        balance REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        amount REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ------------------------
# HELPERS
# ------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user(username):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            return redirect('/')
        return f(*args, **kwargs)
    return decorated

# ------------------------
# LOGIN
# ------------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = get_user(username)

        if user:
            if user['password'] == hash_password(password):
                session['username'] = username
                return redirect(f'/dashboard/{username}')
            else:
                return "Wrong password"

        return "User not found"

    return render_template("login.html")

# ------------------------
# REGISTER
# ------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        hashed = hash_password(password)

        conn = sqlite3.connect(DB)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, password, balance) VALUES (?, ?, ?)",
                (username, hashed, 1000)
            )
            conn.commit()
        except:
            conn.close()
            return "Username already exists"

        conn.close()
        session['username'] = username
        return redirect(f'/dashboard/{username}')

    return render_template('register.html')

# ------------------------
# DASHBOARD
# ------------------------
@app.route('/dashboard/<username>')
@login_required
def dashboard(username):
    if session['username'] != username:
        return "Access denied", 403

    user = get_user(username)
    if not user:
        return "User not found", 404

    success = request.args.get('success')

    data = f"User:{username},Balance:{user['balance']}"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?data={data}"

    return render_template(
        "dashboard_full.html",
        username=username,
        user=user,
        qr_url=qr_url,
        success=success
    )

# ------------------------
# WALLET
# ------------------------
@app.route('/wallet/<username>')
@login_required
def wallet(username):
    user = get_user(username)
    wallet_address = f"LDP-{username}-001"
    return render_template('wallet.html', user=user, wallet=wallet_address)

# ------------------------
# TRANSACTIONS
# ------------------------
@app.route('/transactions/<username>')
@login_required
def transactions(username):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT sender, receiver, amount, timestamp
        FROM transactions
        WHERE sender=? OR receiver=?
        ORDER BY id DESC
    """, (username, username))

    txs = cursor.fetchall()
    conn.close()

    return render_template('transactions.html', txs=txs, username=username)

# ------------------------
# SEND
# ------------------------
@app.route('/send/<username>', methods=['GET', 'POST'])
@login_required
def send(username):
    if request.method == 'POST':
        receiver = request.form.get('receiver')
        amount = float(request.form.get('amount'))

        sender_data = get_user(username)
        receiver_data = get_user(receiver)

        if not receiver_data:
            return "Receiver not found"

        if sender_data['balance'] < amount:
            return "Insufficient balance"

        conn = sqlite3.connect(DB)
        cursor = conn.cursor()

        cursor.execute("UPDATE users SET balance = balance - ? WHERE username=?", (amount, username))
        cursor.execute("UPDATE users SET balance = balance + ? WHERE username=?", (amount, receiver))

        cursor.execute(
            "INSERT INTO transactions (sender, receiver, amount) VALUES (?, ?, ?)",
            (username, receiver, amount)
        )

        conn.commit()
        conn.close()

        return redirect(f'/dashboard/{username}?success=1')

    return render_template("send.html", username=username)

# ------------------------
# MINE
# ------------------------
@app.route('/mine/<username>')
def mine(username):
    global TOTAL_MINED

    now = time.time()

    if username in mine_cooldown:
        if now - mine_cooldown[username] < 86400:
            return "⏳ Subira hanyuma"

    mine_cooldown[username] = now

    if TOTAL_MINED >= MAX_SUPPLY:
        return "⛔ Max supply reached"

    reward = MINE_PER_CLICK

    if username in users:
        users[username]["balance"] += reward

    TOTAL_MINED += reward

    return render_template(
        "mine.html",
        username=username,
        balance=users[username]["balance"],
        mined=TOTAL_MINED,
        max_supply=MAX_SUPPLY
    )

# ------------------------
# QR
# ------------------------
@app.route('/qr/<username>')
@login_required
def qr(username):
    user = get_user(username)
    data = f"User:{username},Balance:{user['balance']}"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?data={data}"
    return render_template("qr.html", qr_url=qr_url)

# ------------------------
# SETTINGS + PAGES
# ------------------------
@app.route('/settings/<username>')
@login_required
def settings(username):
    return render_template('settings.html', user=get_user(username))

@app.route('/quick_actions/<username>')
@login_required
def quick_actions(username):
    return render_template('quick_actions.html', user=get_user(username))

@app.route('/finance/<username>')
@login_required
def finance(username):
    return render_template('finance.html', user=get_user(username))

@app.route('/about/<username>')
@login_required
def about(username):
    return render_template('about.html', user=get_user(username))

@app.route('/contact/<username>')
@login_required
def contact(username):
    return render_template('contact.html', user=get_user(username))

@app.route('/privacy/<username>')
@login_required
def privacy(username):
    return render_template('privacy.html', user=get_user(username))

@app.route('/confidentialite/<username>')
@login_required
def confidentialite(username):
    return render_template('confidentialite.html', user=get_user(username))

# ------------------------
# RECEIVE
# ------------------------
@app.route('/receive/<username>', methods=['GET', 'POST'])
def receive(username):
    if request.method == 'POST':
        from_user = request.form.get('from_user')
        amount = float(request.form.get('amount'))

        sender = get_user(from_user)
        receiver = get_user(username)

        if not sender or not receiver:
            return "User not found"

        if sender['balance'] < amount:
            return "Not enough balance"

        conn = sqlite3.connect(DB)
        cursor = conn.cursor()

        cursor.execute("UPDATE users SET balance = balance - ? WHERE username=?", (amount, from_user))
        cursor.execute("UPDATE users SET balance = balance + ? WHERE username=?", (amount, username))

        cursor.execute(
            "INSERT INTO transactions (sender, receiver, amount) VALUES (?, ?, ?)",
            (from_user, username, amount)
        )

        conn.commit()
        conn.close()

        return f"✅ Received {amount} LDP from {from_user}"

    return render_template("receive.html", username=username)

# ------------------------
# LOGOUT
# ------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ------------------------
# RESET
# ------------------------
@app.route('/reset')
def reset():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users")
    cursor.execute("DELETE FROM transactions")

    conn.commit()
    conn.close()

    return "Database cleared"

# ------------------------
# RUN
# ------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
