import sqlite3
from datetime import datetime

DB_PATH = "database.db"

# -----------------------------
# DB connection helper
# -----------------------------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # dict-like access
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# -----------------------------
# Get user
# -----------------------------

def get_user(username):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cursor.fetchone()

    conn.close()

    if user:
        return {
            "id": user[0],
            "username": user[1],
            "balance": user[2],
            "wallet": user[3],
            "last_mining": user[4]
        }
    return None
# -----------------------------
# Wallet (from users table)
# -----------------------------
def wallet(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, username, balance, wallet, last_mining FROM users WHERE id=?", (user_id,))
        w = cursor.fetchone()
        return dict(w) if w else None
    finally:
        conn.close()

# -----------------------------
# Update balance
# -----------------------------
def update_balance(user_id, new_balance):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET balance=? WHERE id=?", (new_balance, user_id))
        conn.commit()
    finally:
        conn.close()

# -----------------------------
# Update last mining
# -----------------------------
def update_last_mining(user_id, timestamp):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET last_mining=? WHERE id=?", (timestamp, user_id))
        conn.commit()
    finally:
        conn.close()

# -----------------------------
# Add transaction (compatible na table transactions)
# -----------------------------
def add_transaction(sender, receiver, amount):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO transactions (sender, receiver, amount, date) VALUES (?, ?, ?, ?)",
            (sender, receiver, amount, datetime.now().isoformat())
        )
        conn.commit()
    finally:
        conn.close()

# -----------------------------
# Get transactions (compatible na table transactions)
# -----------------------------
def transactions(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT * FROM transactions WHERE sender=? OR receiver=? ORDER BY date DESC",
            (username, username)
        )
        txs = cursor.fetchall()
        return [dict(tx) for tx in txs] if txs else []
    finally:
        conn.close()
