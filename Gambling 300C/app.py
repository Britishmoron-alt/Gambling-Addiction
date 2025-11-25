import os
from flask import Flask, jsonify, request, session, send_from_directory, redirect, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.secret_key = "somerandomsecret"

users = {}  # username -> cash
GAMES = [
    {
        "name": "Slots",
        "file": "slots.html",
        "title": "Competitive Online Slots",
        "description": "Try your luck and compete for a place on the leaderboard!"
    },
    # Add more games here (name, file, title, description)
]

GAMES_DIR = "games"
if not os.path.exists(GAMES_DIR):
    os.makedirs(GAMES_DIR)

# ---- File Templates ----

SLOTS_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Competitive Online Slots</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
/* ... same CSS as before (shortened for brevity)... */
body { font-family: sans-serif; display: flex; flex-direction: column; align-items: center;
  justify-content: center; height: 100vh; background: #f0f0f0; margin: 0; }
.slot-machine { display: flex; justify-content: center; gap: 10px; margin-bottom: 20px;}
.reel { width: 80px; height: 100px; background: #fff; border: 2px solid #333;
  border-radius: 5px; overflow: hidden; position: relative;}
.symbol-list { position: absolute; width: 100%; text-align: center; font-size: 40px;
  line-height: 100px; margin: 0; padding: 0; transform: translateY(0);
  transition: transform 0.5s ease-out;}
.controls { text-align: center; } button { padding: 10px 20px; font-size: 16px;
  cursor: pointer; }
#result-message { margin-top: 10px; font-size: 18px; font-weight: bold; color: #333;}
.money-area { margin-top: 15px; font-size: 16px;}
#money-display { font-weight: bold; color: green;}
#bet-amount { width: 50px; padding: 5px; font-size: 16px;}
@keyframes spinReel { 0% { transform: translateY(0); } 100% { transform: translateY(-500px);}
}
.spinning { animation: spinReel 0.1s linear infinite; }
</style>
</head>
<body>
<h1>Competitive Online Slots</h1>
<div id="user-area">
    <input type="text" id="username-input" placeholder="Your username">
    <button id="login-btn">Login</button>
    <button id="register-btn">Register</button>
    <span id="user-message"></span>
</div>
<div class="slot-machine" style="display:none;" id="slot-machine">
    <div class="reel" id="reel1"><div class="symbol-list" id="list1"></div></div>
    <div class="reel" id="reel2"><div class="symbol-list" id="list2"></div></div>
    <div class="reel" id="reel3"><div class="symbol-list" id="list3"></div></div>
</div>
<div class="controls" id="controls" style="display:none;">
    <div class="money-area"> Money: <span id="money-display">$?</span> </div>
    <div class="money-area"> Bet: <input type="number" id="bet-amount" value="1" min="1"> </div>
    <button id="spin-button">Spin</button>
    <p id="result-message"></p>
</div>
<div id="leaderboard-area" style="margin-top:30px;">
    <h3>Leaderboard</h3>
    <ul id="leaderboard-list"></ul>
</div>
<script>
const symbols = ['%', '$', '#', '@', '!'];
const displaySymbols = [...symbols, ...symbols];
const reelLists = [document.getElementById('list1'), document.getElementById('list2'), document.getElementById('list3')];
const spinButton = document.getElementById('spin-button');
const resultMessage = document.getElementById('result-message');
const moneyDisplay = document.getElementById('money-display');
const betAmountInput = document.getElementById('bet-amount');
const loginBtn = document.getElementById('login-btn');
const registerBtn = document.getElementById('register-btn');
const usernameInput = document.getElementById('username-input');
const userMessage = document.getElementById('user-message');
const userArea = document.getElementById('user-area');
const slotMachine = document.getElementById('slot-machine');
const controls = document.getElementById('controls');
const leaderboardList = document.getElementById('leaderboard-list');
let spinning = false;
function populateReels() { reelLists.forEach(list => { list.innerHTML = '';
    displaySymbols.forEach(symbol => { const span = document.createElement('span'); span.textContent = symbol; span.style.display = 'block'; list.appendChild(span); });
});}
populateReels();
spinButton.addEventListener('click', spin);
loginBtn.onclick = login;
registerBtn.onclick = register;
function updateMoneyDisplay(cash) {
    moneyDisplay.textContent = `$${cash}`;
}
function showGameUI(show) {
    slotMachine.style.display = show ? '' : 'none';
    controls.style.display = show ? '' : 'none';
    userArea.style.display = show ? 'none' : '';
}
function login() {
    const username = usernameInput.value.trim();
    if (!username) { userMessage.textContent = "Enter a username"; return; }
    fetch('/api/login', {method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({username})})
    .then(r => r.json().then(d => [r.status, d]))
    .then(([status, data]) => { if (status == 200) { updateMoneyDisplay(data.cash); showGameUI(true); }
        else { userMessage.textContent = 'User not found. Try Register?'; } refreshLeaderboard();
    });
}
function register() {
    const username = usernameInput.value.trim();
    if (!username) { userMessage.textContent = "Enter a username"; return; }
    fetch('/api/register', {method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({username})})
    .then(r => r.json().then(d => [r.status, d]))
    .then(([status, data]) => { if (status == 200) { updateMoneyDisplay(data.cash); showGameUI(true); }
        else { userMessage.textContent = 'Username taken or invalid.'; } refreshLeaderboard();
    });
}
function getCash() {
    fetch('/api/cash')
    .then(r => r.json())
    .then(data => {
        if (data.cash !== undefined) {
            updateMoneyDisplay(data.cash);
            showGameUI(true);
        }
    });
}
function spin() {
    if (spinning) return;
    const bet = parseInt(betAmountInput.value, 10);
    if (isNaN(bet) || bet <= 0) {
        resultMessage.textContent = "Please enter a valid bet amount.";
        return;
    }
    fetch('/api/play', {method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({bet})})
    .then(r => r.json())
    .then(data => {
        if (data.error) { resultMessage.textContent = "Error: " + data.error; return; }
        doSpin(data.result, bet, data.win, data.cash);
    });
}
function doSpin(resultSymbols, bet, win, newCash) {
    spinning = true; spinButton.disabled = true; betAmountInput.disabled = true; resultMessage.textContent = "Spinning...";
    const stopPositions = resultSymbols.map(s => symbols.indexOf(s));
    reelLists.forEach((list, index) => {
        list.classList.add('spinning');
        setTimeout(() => { stopReel(list, stopPositions[index], index === 2, bet, stopPositions, win, newCash); }, 2000 + (index * 100));
    });
}
function stopReel(list, finalSymbolIndex, isLastReel, bet, stopPositions, win, newCash) {
    list.classList.remove('spinning');
    const symbolHeight = 100;
    const targetY = -(finalSymbolIndex * symbolHeight + symbols.length * symbolHeight);
    list.style.transform = `translateY(${targetY}px)`;
    if (isLastReel) {
        setTimeout(() => {
            if (win >= bet * 10) resultMessage.textContent = `JACKPOT! 3 matching: you won $${win}`;
            else if (win) resultMessage.textContent = `Two matching: you won $${win}`;
            else resultMessage.textContent = "No win";
            updateMoneyDisplay(newCash); spinning = false; spinButton.disabled = false; betAmountInput.disabled = false; resetReelPositions(); refreshLeaderboard();
        }, 500);
    }
}
function resetReelPositions() {
    reelLists.forEach(list => { list.style.transition = 'none'; list.style.transform = 'translateY(0)'; void list.offsetWidth; list.style.transition = 'transform 0.5s ease-out'; });
}
function refreshLeaderboard() {
    fetch('/api/leaderboard')
    .then(r => r.json())
    .then(data => {
        leaderboardList.innerHTML = data.leaderboard.map(
            entry => `<li>${entry.username} — $${entry.cash}</li>`
        ).join('');
    });
}
refreshLeaderboard();
getCash();
</script>
</body>
</html>
"""

# ---- HTML FILE AUTO-GENERATOR ----

def ensure_game_files():
    for g in GAMES:
        fullpath = os.path.join(GAMES_DIR, g["file"])
        if not os.path.exists(fullpath):
            with open(fullpath, "w", encoding="utf-8") as f:
                # Only slot for now; add more templates and map here!
                if g["file"] == "slots.html":
                    f.write(SLOTS_HTML)
                else:
                    f.write(f"<h1>{g['title']}</h1><p>{g['description']}</p>")
ensure_game_files()

# ---- ROUTES ----

@app.route("/")
def homepage():
    # Home: List of games
    html = """<!DOCTYPE html>
<html lang="en"><head>
<title>Casino Homepage</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body { font-family:sans-serif; background:#222; color:#fff; min-height:100vh; margin:0; }
h1 { margin-top:40px; }
.game-list { display:flex; flex-wrap:wrap; gap:2em; margin:2em 0;}
.game-card { background:#333; border-radius:10px; padding:1.5em; min-width:200px; box-shadow:2px 2px 8px #0007;}
.game-card a { color:#00e; text-decoration:none; font-weight:bold; font-size:1.15em;}
.game-card p { margin-top:10px; color:#ccc; }
</style></head>
<body>
<h1>Welcome to the Casino!</h1>
<div class="game-list">
"""
    for g in GAMES:
        html += f"""<div class="game-card">
<a href="/games/{g['file']}">{g['title']}</a>
<p>{g['description']}</p>
</div>
"""
    html += """</div></body></html>"""
    return html

@app.route("/games/<filename>")
def serve_game(filename):
    return send_from_directory(GAMES_DIR, filename)

@app.route('/api/register', methods=['POST'])
def register():
    username = request.json.get('username', '').strip()
    if not username:
        return jsonify({'error': 'empty'}), 400
    if username in users:
        return jsonify({'error':'exists'}), 400
    users[username] = 1000
    session['username'] = username
    return jsonify({'cash':users[username]})

@app.route('/api/login', methods=['POST'])
def login():
    username = request.json.get('username', '').strip()
    if not username or username not in users:
        return jsonify({'error':'notfound'}), 404
    session['username'] = username
    return jsonify({'cash':users[username]})

@app.route('/api/cash', methods=['GET'])
def cash():
    username = session.get('username')
    if not username:
        return jsonify({'error':'notloggedin'}), 401
    return jsonify({'cash':users[username]})

@app.route('/api/play', methods=['POST'])
def play():
    username = session.get('username')
    if not username:
        return jsonify({'error':'notloggedin'}), 401
    bet = int(request.json.get('bet', 0))
    if bet <= 0 or bet > users[username]:
        return jsonify({'error':'badbet'}), 400
    import random
    symbols = ['%', '$', '#', '@', '!']
    result = [random.choice(symbols) for _ in range(3)]
    win = 0
    if result[0] == result[1] == result[2]:
        win = bet * 10
    elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
        win = bet * 2
    users[username] -= bet
    users[username] += win
    return jsonify({'result': result, 'win': win, 'cash': users[username]})

@app.route('/api/leaderboard', methods=['GET'])
def leaderboard():
    top = sorted(users.items(), key=lambda x: x[1], reverse=True)[:10]
    return jsonify({'leaderboard': [{'username': u, 'cash': c} for u, c in top]})

if __name__ == "__main__":
    ensure_game_files()
    app.run(debug=True)
