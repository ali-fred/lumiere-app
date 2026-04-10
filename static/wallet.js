function checkBalance() {
    const username = prompt("Enter your username:");
    fetch(`/balance/${username}`)
        .then(res => res.json())
        .then(data => {
            if (data.balance !== undefined) {
                document.getElementById("balance").innerText = `Balance: ${data.balance} LDP`;
            } else {
                document.getElementById("balance").innerText = data.error;
            }
        });
}

function mine() {
    const username = prompt("Enter your username to mine:");
    fetch(`/mine/${username}`)
        .then(res => res.json())
        .then(data => {
            alert(data.message || data.error);
            checkBalance();
        });
}

function sendLDP() {
    const sender = document.getElementById("sender").value;
    const receiver = document.getElementById("receiver").value;
    const amount = document.getElementById("amount").value;

    fetch("/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sender, receiver, amount })
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message || data.error);
        checkBalance();
    });
}