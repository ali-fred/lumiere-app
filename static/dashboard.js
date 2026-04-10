// ===== LOAD DASHBOARD =====
async function loadDashboard(){
try{

// ===== WALLET =====
let w = await fetch("/wallet",{credentials:"include"});
if(w.status === 401){
alert("Login first");
window.location = "/";
return;
}

let wd = await w.json();

document.getElementById("username").innerText = wd.username;
document.getElementById("walletAddress").innerText = wd.wallet;
document.getElementById("balance").innerText = Number(wd.balance).toFixed(2);
document.getElementById("ref").innerText = wd.referral;

// ===== QR CODE =====
document.getElementById("qr").src =
"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=" + wd.wallet;

// ===== COUNTDOWN =====
if(wd.last_mined){
startCountdown(new Date(wd.last_mined));
}else{
document.getElementById("countdown").innerText = "Available now";
}

// ===== TOTAL SUPPLY =====
let t = await fetch("/total",{credentials:"include"});
let td = await t.json();

// SAFE DISPLAY
let totalEl = document.getElementById("totalSupply");
if(totalEl){
totalEl.innerText =
Number(td.total).toFixed(2) + " / " + td.max_supply.toLocaleString();
}

// SAFE PROGRESS BAR
let bar = document.getElementById("supplyBar");
if(bar){
let percent = (td.total / td.max_supply) * 100;
bar.style.width = percent + "%";
}

// ===== PROGRESS BAR =====
let percent = (td.total / td.max_supply) * 100;
document.getElementById("supplyBar").style.width = percent + "%";

// ===== USERS =====
let u = await fetch("/users",{credentials:"include"});
let users = await u.json();

let table = document.getElementById("usersTable");
table.innerHTML = "<tr><th>User</th><th>Balance</th></tr>";

users.forEach(x=>{
table.innerHTML += "<tr><td>"+x.username+"</td><td>"+Number(x.balance).toFixed(2)+"</td></tr>";
});

// ===== TRANSACTIONS =====
let tx = await fetch("/transactions",{credentials:"include"});
let txs = await tx.json();

let txTable = document.getElementById("transactionsTable");
txTable.innerHTML = "<tr><th>From</th><th>To</th><th>Amount</th><th>Date</th></tr>";

txs.forEach(x=>{
txTable.innerHTML += "<tr><td>"+x.sender+"</td><td>"+x.receiver+"</td><td>"+Number(x.amount).toFixed(2)+"</td><td>"+x.date+"</td></tr>";
});

}catch(e){
console.error(e);
alert("Error loading dashboard");
}
}

// ===== MINING =====
async function mine(){
let r = await fetch("/mine",{method:"POST",credentials:"include"});
let d = await r.json();
alert(d.message);
loadDashboard();
}

// ===== SEND =====
async function sendLDP(){
let receiver = prompt("Receiver username");
let amount = prompt("Amount");

let r = await fetch("/send",{
method:"POST",
headers:{"Content-Type":"application/json"},
credentials:"include",
body:JSON.stringify({receiver,amount})
});

let d = await r.json();
alert(d.message);
loadDashboard();
}

// ===== COUNTDOWN =====
function startCountdown(last){
let el = document.getElementById("countdown");

function update(){
let now = new Date();
let next = new Date(last.getTime() + 24*60*60*1000);
let diff = next - now;

if(diff <= 0){
el.innerText = "Available now";
return;
}

let h = Math.floor(diff/(1000*60*60));
let m = Math.floor((diff%(1000*60*60))/(1000*60));
let s = Math.floor((diff%(1000*60))/1000);

el.innerText = h+"h "+m+"m "+s+"s";
}

update();
setInterval(update,1000);
}

// ===== LOAD ON START =====
loadDashboard();