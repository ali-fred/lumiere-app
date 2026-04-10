from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime, timedelta
import qrcode
from io import BytesIO
import base64
import hashlib

def hash_password(password):
    """
    Hano turahindura password mu SHA-256 hash.
    Ibi bituma password itabikwa mu buryo busomeka.
    """
    return hashlib.sha256(password.encode()).hexdigest()

app = Flask(__name__)

DB = 'database.db'

# ------------------------
# Helper functions
# ------------------------
def get_user(username):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def update_last_mining(username):
    now = datetime.now().isoformat()
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET last_mining=? WHERE username=?", (now, username))
    conn.commit()
    conn.close()
    return now

# ------------------------
# Routes - Menu
# ------------------------

@app.route('/quick_actions/<username>')
def quick_actions(username):
    user = get_user(username)
    if not user:
        return "User not found", 404
    return render_template('quick_actions.html', user=user)

@app.route('/finance/<username>')
def finance(username):
    user = get_user(username)
    if not user:
        return "User not found", 404
    return render_template('finance.html', user=user)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/confidentialite')
def confidentialite():
    return render_template('confidentialite.html')

@app.route('/settings/<username>', methods=['GET', 'POST'])
def settings(username):
    user = get_user(username)
    if not user:
        return "User not found", 404

    if request.method == 'POST':
        new_username = request.form.get('username')
        new_password = request.form.get('password')

        conn = sqlite3.connect(DB)
        cursor = conn.cursor()

        # Update username
        if new_username:
            cursor.execute("UPDATE users SET username=? WHERE username=?", (new_username, username))
            username = new_username  # update session variable

        # Update password
        if new_password:
            cursor.execute("UPDATE users SET password=? WHERE username=?", (new_password, username))

        conn.commit()
        conn.close()

        return redirect(f'/dashboard/{username}')

    return render_template('settings.html', user=user)

# Routes - User
# ------------------------
@app.route('/dashboard/<username>')
def dashboard(username):
    user = get_user(username)
    if not user:
        return "User not found"

    data = f"User:{username},Wallet:{user['wallet']}"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={data}"

    return render_template("dashboard_full.html", user=user, qr_url=qr_url)


@app.route('/wallet/<username>')
def wallet(username):
    user = get_user(username)
    if not user:
        return "Wallet not found", 404
    return render_template('wallet.html', user=user)


@app.route('/send/<username>', methods=['GET', 'POST'])
def send(username):
    # Fata user
    user = get_user(username)
    if not user:
        return "User not found", 404

    if request.method == 'POST':
        receiver = request.form.get('receiver')
        amount = float(request.form.get('amount'))

        # Fata receiver user
        receiver_user = get_user(receiver)
        if not receiver_user:
            return "Receiver not found", 404

        # Reba balance
        if user['balance'] < amount:
            return "Insufficient balance", 400

        # Connect DB
        conn = sqlite3.connect(DB)
        cursor = conn.cursor()

        # Subtract from sender
        new_sender_balance = user['balance'] - amount
        cursor.execute(
            "UPDATE users SET balance=? WHERE username=?",
            (new_sender_balance, username)
        )

        # Add to receiver
        new_receiver_balance = receiver_user['balance'] + amount
        cursor.execute(
            "UPDATE users SET balance=? WHERE username=?",
            (new_receiver_balance, receiver)
        )

        # Save transaction
        cursor.execute(
            "INSERT INTO transactions (sender, receiver, amount, date) VALUES (?, ?, ?, ?)",
            (username, receiver, amount, datetime.now())
        )

        conn.commit()
        conn.close()

        # Redirect kuri dashboard ya sender
        return redirect(f'/dashboard/{username}')

    # GET request → render form
    return render_template('send.html', user=user)


@app.route('/transactions/<username>')
def transactions(username):
    user = get_user(username)
    if not user:
        return "User not found", 404
    # fetch transactions from db
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions WHERE sender=? OR receiver=? ORDER BY id DESC", (username, username))
    txs = cursor.fetchall()
    conn.close()
    return render_template('transaction.html', user=user, transactions=txs)


@app.route('/mining/<username>', methods=['GET', 'POST'])
def mining(username):
    user = get_user(username)
    if not user:
        return "User not found", 404

    last_mining = user['last_mining']
    now = datetime.now()

    # igihe gishize kuva last mining
    if last_mining:
        last_time = datetime.fromisoformat(last_mining)
        diff = now - last_time
    else:
        diff = timedelta(hours=24)

    remaining = timedelta(hours=24) - diff

    # POST → gukora mining
    if request.method == 'POST':
        if diff >= timedelta(hours=24):
            conn = sqlite3.connect(DB)
            cursor = conn.cursor()

            new_balance = user['balance'] + 2.4

            cursor.execute(
                "UPDATE users SET balance=?, last_mining=? WHERE username=?",
                (new_balance, now.isoformat(), username)
            )

            conn.commit()
            conn.close()

            return redirect(f'/dashboard/{username}')
        else:
            # ntibiremewe
            pass

    # format time isigaye
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
        user = get_user(username)
        if user:
            return redirect(f'/dashboard/{username}')
        else:
            return "User not found. Please register first.", 404
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        conn = sqlite3.connect(DB)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, balance, wallet, last_mining) VALUES (?, ?, ?, ?)",
                           (username, 1000, f'LDP{username}001', datetime.now().isoformat()))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "Username already exists!", 400
        conn.close()
        return redirect(f'/dashboard/{username}')
    return render_template('register.html')

@app.route('/qr/<username>')
def generate_qr(username):
    user = get_user(username)
    if not user:
        return "User not found"

    data = f"User:{username},Wallet:{user['wallet']}"

    # QR online (nta Pillow)
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={data}"

    return render_template("qr.html", qr_url=qr_url, username=username)
# ------------------------
# Main
# ------------------------
if __name__ == '__main__':
    app.run(debug=True, port=5000)
