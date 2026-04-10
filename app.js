// ===== WALLET =====
function generateWallet(){
    let wallet = localStorage.getItem("ldp_wallet");
    if(!wallet){
        wallet = "LDP" + Math.random().toString(36).substring(2,12).toUpperCase();
        localStorage.setItem("ldp_wallet", wallet);
    }
    document.getElementById("walletAddress").innerText = wallet;
}

// ===== COPY WALLET =====
function copyWallet(){
    let wallet = localStorage.getItem("ldp_wallet");
    navigator.clipboard.writeText(wallet);
    alert("Wallet copied");
}

// ===== BALANCE =====
function loadBalance(){
    let balance = localStorage.getItem("ldp_balance");
    if(!balance){
        balance = 2.4;
        localStorage.setItem("ldp_balance", balance);
    }
    document.getElementById("balance").innerText = parseFloat(balance).toFixed(6) + " LDP";
}

// ===== TOTAL SUPPLY =====
function loadSupply(){
    let supply = localStorage.getItem("ldp_supply");
    if(!supply){
        supply = 1000000000; // Total Supply nyayo
        localStorage.setItem("ldp_supply", supply);
    }
    document.getElementById("totalSupply").innerText = supply;
}

// ===== PRICE SIMULATION =====
function loadPrice(){
    let price = parseFloat(localStorage.getItem("ldp_price"));
    if(!price) price = 0.05;
    document.getElementById("ldpPrice").innerText = price.toFixed(2);
}

// ===== MINING =====
function mineLDP(){
    let lastMine = localStorage.getItem("ldp_last_mine");
    let now = Date.now();

    if(lastMine && now - lastMine < 86400000){
        alert("Mining available once every 24h");
        return;
    }

    let balance = parseFloat(localStorage.getItem("ldp_balance")) || 0;
    balance += 0.1; // mining reward
    localStorage.setItem("ldp_balance", balance);
    localStorage.setItem("ldp_last_mine", now);

    // Price simulation
    let price = parseFloat(localStorage.getItem("ldp_price")) || 0.05;
    price += Math.random() * 0.01; // izamuka gahoro
    localStorage.setItem("ldp_price", price);
    loadPrice();

    addTransaction("Mining reward", 0.1);
    loadBalance();
    startCooldown();
}

// ===== COOLDOWN TIMER =====
function startCooldown(){
    let lastMine = localStorage.getItem("ldp_last_mine");
    let timer = document.getElementById("cooldown");
    if(!lastMine || !timer) return;

    setInterval(function(){
        let now = Date.now();
        let diff = 86400000 - (now - lastMine);

        if(diff <= 0){
            timer.innerText = "Mining ready";
            return;
        }

        let hours = Math.floor(diff/3600000);
        let minutes = Math.floor((diff%3600000)/60000);
        let seconds = Math.floor((diff%60000)/1000);
        timer.innerText = hours+"h "+minutes+"m "+seconds+"s";
    },1000);
}

// ===== SEND LDP =====
function sendLDP(){
    let receiver = document.getElementById("sendAddress").value;
    let amount = parseFloat(document.getElementById("sendAmount").value);
    let balance = parseFloat(localStorage.getItem("ldp_balance")) || 0;

    if(!receiver || isNaN(amount) || amount<=0){
        alert("Invalid transaction");
        return;
    }
    if(amount > balance){
        alert("Insufficient balance");
        return;
    }

    balance -= amount;
    localStorage.setItem("ldp_balance", balance);
    addTransaction("Sent to "+receiver, -amount);
    loadBalance();
    alert("Transaction successful");
}

// ===== TRANSACTIONS =====
function addTransaction(type, amount){
    let txs = JSON.parse(localStorage.getItem("ldp_transactions")) || [];
    txs.push({ type:type, amount:amount, date:new Date().toLocaleString() });
    localStorage.setItem("ldp_transactions", JSON.stringify(txs));
    loadTransactions();
}

function loadTransactions(){
    let txs = JSON.parse(localStorage.getItem("ldp_transactions")) || [];
    let container = document.getElementById("transactions");
    if(!container) return;
    container.innerHTML = "";
    txs.slice().reverse().forEach(tx=>{
        let div = document.createElement("div");
        div.innerText = tx.date + " | " + tx.type + " | " + tx.amount + " LDP";
        container.appendChild(div);
    });
}

// ===== START APP =====
generateWallet();
loadBalance();
loadSupply();
loadPrice();
loadTransactions();
startCooldown();
