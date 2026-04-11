from flask import Flask, render_template, request, redirect, session
import sqlite3
import hashlib
import os
from functools import wraps
from datetime import datetime, timedelta
import time

mine_cooldown = {}

app = Flask(__name__)

users = {
    "Huruma": {"balance": 100}
}

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

        if not username or not password:
            return "Please provide both username and password", 400

        user = get_user(username)

        if user and user['password'] == hash_password(password):
            session['username'] = username
            session.permanent = True
            return redirect(f'/dashboard/{username}')
        else:
            return "Invalid User", 400

    return render_template('login.html')

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
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?data={data}&size=150x150"

    return render_template("dashboard_full.html", user=user, qr_url=qr_url)


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


@app.route('/send/<username>', methods=['GET', 'POST'])
@login_required
def send(username):
    user = get_user(username)

    if request.method == 'POST':
        receiver = request.form.get('receiver')

        # 🔐 VALIDATION MUST STAY INSIDE POST
        if not receiver or not request.form.get('amount'):
            return "Fill all fields", 400

        try:
            amount = float(request.form.get('amount'))
        except:
            return "Invalid amount", 400

        if amount <= 0:
            return "Amount must be greater than 0", 400

        if receiver == username:
            return "You cannot send money to yourself", 400

        receiver_user = get_user(receiver)
        if not receiver_user:
            return "Receiver not found", 404

        if user['balance'] < amount:
            return "Insufficient balance", 400

        conn = sqlite3.connect(DB)
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE users SET balance=? WHERE username=?",
            (user['balance'] - amount, username)
        )

        cursor.execute(
            "UPDATE users SET balance=? WHERE username=?",
            (receiver_user['balance'] + amount, receiver)
        )

        cursor.execute(
            "INSERT INTO transactions (sender, receiver, amount, datetime) VALUES (?, ?, ?, ?)",
            (username, receiver, amount, datetime.now().isoformat())
        )

        conn.commit()
        conn.close()

        return redirect(f'/dashboard/{username}')

    return render_template('send.html', user=user)

@app.route('/mine/<username>')
def mine(username):
    current_time = time.time()

    # cooldown 10 seconds
    if username in mine_cooldown:
        if current_time - mine_cooldown[username] < 10:
            return "⏳ Wait cooldown before mining again"

    mine_cooldown[username] = current_time

    # increase balance (example)
    user = users.get(username)
    if user:
        user['balance'] += 5

    return render_template("mine.html", username=username, balance=user['balance'])

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
