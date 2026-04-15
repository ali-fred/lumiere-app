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
    "Huruma": {"password": "1234", "balance": 100}
}

# -------- MINING SETTINGS --------
MAX_SUPPLY = 1000000000  # max LDPs
TOTAL_MINED = 0

MINE_RATE_PER_DAY = 2.4
MINE_PER_CLICK = MINE_RATE_PER_DAY / 24  # 0.1 LDP per hour

# -------- COOLDOWN --------
mine_cooldown = {}
send_cooldown = {}


app.secret_key = os.environ.get("SECRET_KEY", "mysecret123")
app.permanent_session_lifetime = timedelta(minutes=30)

DB = 'database.db'

# ------------------------
# Helper functions
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
# Routes
# ------------------------

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # debug (optional)
        print("USERS:", users)

        if username in users:
            if users[username]["password"] == password:
                session['username'] = username
                return redirect(f'/dashboard/{username}')
            else:
                return "Wrong password"

        return "User Not Found"

    return render_template("login.html")
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return "Please provide both username and password", 400

        hashed = hash_password(password)

        conn = sqlite3.connect(DB)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password, balance) VALUES (?, ?, ?)",
                (username, hashed, 1000)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "Username already exists!", 400

        conn.close()
        session['username'] = username
        return redirect(f'/dashboard/{username}')

    return render_template('register.html')


@app.route('/dashboard/<username>')
@login_required
def dashboard(username):
    if session['username'] != username:
        return "Access denied", 403

    user = get_user(username)
    if not user:
        return "User not found", 404

    data = f"User:{username},Balance:{user['balance']}"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?data={data}"

    return render_template(
        "dashboard_full.html",
        username=username,
        user=user,
        qr_url=qr_url
    )

@app.route('/wallet/<username>')
@login_required
def wallet(username):
    user = get_user(username)
    return render_template('wallet.html', user=user)


@app.route('/transactions/<username>')
@login_required
def transactions(username):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions WHERE sender=? OR receiver=?", (username, username))
    txs = cursor.fetchall()
    conn.close()

    return render_template('transaction.html', txs=txs, user={'username': username})

@app.route('/send/<username>')
def send(username):
    import time

    now = time.time()

    if username in send_cooldown:
        if now - send_cooldown[username] < 10:
            return "⏳ Rindira gato imbere yo gusubira kohereza"

    send_cooldown[username] = now

    return render_template("send.html", username=username)

@app.route('/mine/<username>')
def mine(username):
    global TOTAL_MINED

    import time
    now = time.time()

    if username not in users:
        return "User not found"

    if "balance" not in users[username]:
        users[username]["balance"] = 0

    if username not in mine_cooldown:
        mine_cooldown[username] = 0

    if now - mine_cooldown[username] < 5:
        return "⏳ Cooldown active"

    mine_cooldown[username] = now

    if TOTAL_MINED >= MAX_SUPPLY:
        return "⛔ Max supply reached"

    reward = MINE_PER_CLICK

    users[username]["balance"] += reward
    TOTAL_MINED += reward

    return render_template(
        "mine.html",
        username=username,
        balance=users[username]["balance"],
        mined=TOTAL_MINED,
        max_supply=MAX_SUPPLY
    )

@app.route('/qr/<username>')
@login_required
def qr(username):
    user = get_user(username)
    data = f"User:{username},Balance:{user['balance']}"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?data={data}&size=150x150"
    return render_template("qr.html", qr_url=qr_url)


@app.route('/settings/<username>')
@login_required
def settings(username):
    user = get_user(username)
    return render_template('settings.html', user=user)

@app.route('/quick_actions/<username>')
@login_required
def quick_actions(username):
    user = get_user(username)
    return render_template('quick_actions.html', user=user)
@app.route('/finance/<username>')
@login_required
def finance(username):
    user = get_user(username)
    return render_template('finance.html', user=user)

@app.route('/about/<username>')
@login_required
def about(username):
    user = get_user(username)
    return render_template('about.html', user=user)

@app.route('/contact/<username>')
@login_required
def contact(username):
    user = get_user(username)
    return render_template('contact.html', user=user)

@app.route('/privacy/<username>')
@login_required
def privacy(username):
    user = get_user(username)
    return render_template('privacy.html', user=user)

@app.route('/confidentialite/<username>')
@login_required
def confidentialite(username):
    user = get_user(username)
    return render_template('confidentialite.html', user=user)

# -------- RECEIVE --------
@app.route('/receive/<username>')
def receive(username):
    return render_template("receive.html", username=username)
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')


# ------------------------
# Run
# ------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
# FORCE UPDATE
