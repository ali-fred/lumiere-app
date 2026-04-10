from functions import get_user, wallet, update_balance, update_last_mining, add_transaction, transactions
from datetime import datetime

# -----------------------------
# Test get_user
# -----------------------------
print("Testing get_user...")
user = get_user(user_id=1)  # Shyiramo user_id iri muri DB yawe
if user:
    print("User found:", user)
else:
    print("User ntahari")

# -----------------------------
# Test wallet
# -----------------------------
print("\nTesting wallet...")
w = wallet(1)
if w:
    print("Wallet found:", w)
else:
    print("Wallet ntihari")

# -----------------------------
# Test update_balance
# -----------------------------
print("\nTesting update_balance...")
if w:
    old_balance = w['balance']
    new_balance = old_balance + 10
    update_balance(1, new_balance)
    w_new = wallet(1)
    print(f"Balance updated from {old_balance} to {w_new['balance']}")

# -----------------------------
# Test update_last_mining
# -----------------------------
print("\nTesting update_last_mining...")
now = datetime.now().isoformat()
update_last_mining(1, now)
user_new = get_user(user_id=1)
print("New last_mining:", user_new.get('last_mining'))

# -----------------------------
# Test add_transaction
# -----------------------------
print("\nTesting add_transaction...")
# Shyiramo usernames ziri muri database yawe
add_transaction("Alfred", "SomeoneElse", 50)
txs = transactions("Alfred")
print("Most recent transaction:", txs[0] if txs else "No transactions")

# -----------------------------
# Test transactions
# -----------------------------
print("\nTesting transactions...")
all_tx = transactions("Alfred")
print(f"Total transactions for Alfred: {len(all_tx)}")
for tx in all_tx[:5]:  # Erekana 5 za mbere gusa
    print(tx)
