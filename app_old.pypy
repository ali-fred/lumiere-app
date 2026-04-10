from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime, timedelta
import hashlib
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Hindura kuri True niba HTTPS

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
    def decorated_function(*args, **kwargs):
        username = kwargs.get('username')
        if 'username' not in session or session['username'] != username:
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function

# ------------------------
# Routes - Menu
# ------------------------
@app.route('/quick_actions/<username>')
@login_required
def quick_actions(username):
    user = get_user(username)
    if not user:
        return "User not found", 404
    return render_template('quick_actions.html', user=user)

@app.route('/finance/<username>')
@login_required
def finance(username):
    user = get_user(username)
    if not user:
        return "User not found", 404
    return render_template('finance.html', user=user)

@app.route('/about/<username>')
@login_required
def about(username):
    return render_template('about.html', username=username)

@app.route('/contact/<username>')
@login_required
def contact(username):
    return render_template('contact.html', username=username)

@app.route('/privacy/<username>')
@login_required
def privacy(username):
    return render_template('privacy.html', username=username)

@app.route('/confidentialite/<username>')
@login_required
def confidentialite(username):
    return render_template('confidentialite.html', username=username)

@app.route('/settings/<username>', methods=['GET', 'POST'])
@login_required
def settings(username):
    user = get_user(username)
    if not user:
        return "User not found", 404

    if request.method == 'POST':
        new_username = request.form.get('username')
        new_password = request.form.get('password')

        conn = sqlite3.connect(DB)
        cursor = conn.cursor()

        if new_username:
            cursor.execute("UPDATE users SET username=? WHERE username=?", (new_username, username))
            username = new_username
            session['username'] = new_username

        if new_password:
            hashed = hash_password(new_password)
            cursor.execute("UPDATE users SET password=? WHERE username=?", (hashed, username))

        conn.commit()
        conn.close()
        return redirect(f'/dashboard/{username}')

    return render_template('settings.html', user=user)

# ------------------------
# Routes - User
# ------------------------
@app.route('/dashboard/<username>')
@login_required
def dashboard(username):
    user = get_user(username)
    if not user:
        return "User not found"
    return render_template('dashboard_full.html', user=user)

@app.route('/wallet/<username>')
@login_required
def wallet(username):
    user = get_user(username)
    if not user:
        return "User not found"
    return render_template('wallet.html', user=user)

@app.route('/send/<username>', methods=['GET', 'POST'])
@login_required
def send(username):
    user = get_user(username)
    if not user:
        return "User not found", 404

    if request.method == 'POST':
        receiver = request.form.get('receiver')
        amount = float(request.form.get('amount'))

        receiver_user = get_user(receiver)
        if not receiver_user:
            return "Receiver not found", 404
        if user['balance'] < amount:
            return "Insufficient balance", 400

        conn = sqlite3.connect(DB)
        cursor = conn.cursor()
        new_sender_balance = user['balance'] - amount
        cursor.execute("UPDATE users SET balance=? WHERE username=?", (new_sender_balance, username))
        new_receiver_balance = receiver_user['balance'] + amount
        cursor.execute("UPDATE users SET balance=? WHERE username=?", (new_receiver_balance, receiver))
        cursor.execute("INSERT INTO transactions (sender, receiver, amount, datetime) VALUES (?, ?, ?, ?)",
                       (username, receiver, amount, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return redirect(f'/dashboard/{username}')

    return render_template('send.html', user=user)

@app.route('/transactions/<username>')
@login_required
def transactions(username):
    user = get_user(username)
    if not user:
        return "User not found", 404
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions WHERE sender=? OR receiver=? ORDER BY datetime DESC", (username, username))
    txs = cursor.fetchall()
    conn.close()
    return render_template('transaction.html', user=user, transactions=txs)

@app.route('/mining/<username>', methods=['GET', 'POST'])
@login_required
def mining(username):
    user = get_user(username)
    if not user:
        return "User not found", 404

    last_mining = user.get('last_mining')
    now = datetime.now()

    if last_mining:
        last_time = datetime.fromisoformat(last_mining)
        diff = now - last_time
    else:
        diff = timedelta(hours=24)

    remaining = timedelta(hours=24) - diff

    if request.method == 'POST':
        if diff >= timedelta(hours=24):
            conn = sqlite3.connect(DB)
            cursor = conn.cursor()
            new_balance = user['balance'] + 2.4
            cursor.execute("UPDATE users SET balance=?, last_mining=? WHERE username=?",
                           (new_balance, now.isoformat(), username))
            conn.commit()
            conn.close()
            return redirect(f'/dashboard/{username}')

    hours = int(remaining.total_seconds() // 3600)
    minutes = int((remaining.total_seconds() % 3600) // 60)

    return render_template('mining.html', user=user, hours=hours, minutes=minutes)

# ------------------------
# Routes - Login/Register
# ------------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = get_user(username)

        if user and user['password'] == password:
            session['username'] = username
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
            cursor.execute("INSERT INTO users (username, password, balance) VALUES (?, ?, ?)",
                           (username, hashed, 1000))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "Username already exists!", 400
        conn.close()
        return redirect(f'/dashboard/{username}')
    return render_template('register.html')

@app.route('/qr/<username>')
@login_required
def generate_qr(username):
    user = get_user(username)
    if not user:
        return "User not found"
    data = f"User:{username},Wallet:{user['balance']}"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?data={data}&size=150x150"
    return render_template("qr.html", qr_url=qr_url, user=user)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

# ------------------------
# Main
# ------------------------
if __name__ == '__main__':
    app.run(debug=True, port=5000)
