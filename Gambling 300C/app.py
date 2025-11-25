import os
import json
from flask import Flask, jsonify, request, session, send_from_directory

app = Flask(__name__)
app.secret_key = "somerandomsecret"

DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
GAMES_DIR = "games"

GAMES = [
    {
        "name": "Slots",
        "file": "slots.html",
        "title": "Competitive Online Slots",
        "description": "Try your luck and compete for a place on the leaderboard!",
        "template": "slots"
    },
    {
        "name": "Pac-Man Challenge",
        "file": "pacman.html",
        "title": "Pac-Man Challenge",
        "description": "Eat all dots, dodge ghosts, win big cash based on remaining lives!",
        "template": "pacman"
    },
    {
        "name": "Super Gamble",
        "file": "gambleall.html",
        "title": "Super Gamble: Double or Nothing",
        "description": "Wager your entire balance on a 50/50 shot to double it — or lose it all instantly!",
        "template": "gambleall"
    }
]

# ========== Game HTML Templates ==========

SLOTS_HTML = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8">
<title>Competitive Online Slots</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
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


PACMAN_HTML = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8">
<title>Pac-Man Challenge</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body { font-family:sans-serif; background:#222; color:#fff; text-align:center; }
#game { margin:40px auto; width: 320px; }
#board { background:#111; border:5px solid #fd0; width:320px; height:320px; position:relative; }
.cell { width:32px; height:32px; float:left; box-sizing:border-box; }
.wall { background:#444; }
.dot { background:#555; border-radius:50%; margin:12px; width:8px; height:8px; display:inline-block; }
.pacman { background:yellow; border-radius:50%; }
.ghost { background: #f03; border-radius:50%; }
#stats { font-size:1.2em; margin-top:18px; }
#gameover, #win { font-size:1.5em; color:#fd0; font-weight:bold; margin:1em; }
button { margin-top:12px; font-size:1em; padding:7px 20px; }
</style>
</head>
<body>
<h1>Pac-Man Challenge</h1>
<div id="user-area">
    <input type="text" id="username-input" placeholder="Your username">
    <button id="login-btn">Login</button>
    <button id="register-btn">Register</button>
    <span id="user-message"></span>
</div>
<div id="stats"></div>
<div id="game" style="display:none;">
  <div id="board"></div>
  <div id="gameover" style="display:none;"></div>
  <div id="win" style="display:none;"></div>
  <button id="restart" style="display:none;">Restart</button>
</div>
<div id="leaderboard-area" style="margin-top:30px;">
    <h3>Leaderboard</h3>
    <ul id="leaderboard-list"></ul>
</div>
<script>
let username = null;
function setUser(u){
    username = u;
    document.getElementById("user-area").style.display = "none";
    document.getElementById("game").style.display = "";
    getCash();
    refreshLeaderboard();
}
const loginBtn = document.getElementById('login-btn');
const registerBtn = document.getElementById('register-btn');
const usernameInput = document.getElementById('username-input');
const userMessage = document.getElementById('user-message');
loginBtn.onclick = login;
registerBtn.onclick = register;
function login() {
    const u = usernameInput.value.trim();
    if (!u) { userMessage.textContent = "Enter a username"; return; }
    fetch('/api/login', {method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({username:u})})
    .then(r => r.json().then(d => [r.status, d]))
    .then(([status, data]) => { if(status===200){ setUser(u); }else{ userMessage.textContent='User not found. Try Register?'; } });
}
function register() {
    const u = usernameInput.value.trim();
    if (!u) { userMessage.textContent = "Enter a username"; return; }
    fetch('/api/register', {method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({username:u})})
    .then(r => r.json().then(d => [r.status, d]))
    .then(([status, data]) => { if(status===200){ setUser(u); }else{ userMessage.textContent='Username taken or invalid.'; } });
}
function getCash(){
    fetch('/api/cash').then(r=>r.json()).then(data=>{
        if(data.cash!==undefined)
            document.getElementById('stats').textContent = `Cash: $${data.cash}`;
    });
}

function refreshLeaderboard() {
    fetch('/api/leaderboard')
    .then(r => r.json())
    .then(data => {
        document.getElementById('leaderboard-list').innerHTML = data.leaderboard.map(
            entry => `<li>${entry.username} — $${entry.cash}</li>`
        ).join('');
    });
}

const rows = 10, cols = 10;
const boardElem = document.getElementById('board');
const statsElem = document.getElementById('stats');
const gameoverElem = document.getElementById('gameover');
const winElem = document.getElementById('win');
const restartBtn = document.getElementById('restart');
let cells = [], pac = {r:1, c:1}, ghosts = [], dots=0, lives = 4, gameActive=true;
const wallmap = [
  "WWWWWWWWWW",
  "W........W",
  "W.WWW.WW.W",
  "W.W.....GW",
  "W.WWWW.W.W",
  "W...W....W",
  "WWWWWW.WWW",
  "W.....W..W",
  "WGW.W...GW",
  "WWWWWWWWWW",
];
function resetGame() {
  boardElem.innerHTML = "";
  gameoverElem.style.display = winElem.style.display = restartBtn.style.display = 'none';
  pac = {r:1, c:1};
  lives = 4;
  dots = 0;
  ghosts = [];
  gameActive = true;
  for (let r=0;r<rows;r++) for(let c=0;c<cols;c++) {
    let cell = document.createElement('div');
    cell.classList.add('cell');
    if (wallmap[r][c]=='W') cell.classList.add('wall');
    else if (wallmap[r][c]=='.') {
      let dot=document.createElement('div');dot.className='dot';
      cell.appendChild(dot); dots++;
    }
    else if (wallmap[r][c]=='G') ghosts.push({r:r,c:c,dir:Math.random()<.5?1:-1});
    cells.push(cell);
    boardElem.appendChild(cell);
  }
  render();
  updateStats();
}
function getCell(r,c) { return cells[r*cols+c]; }
function render() {
  cells.forEach(e=>{e.classList.remove('pacman','ghost');});
  getCell(pac.r,pac.c).classList.add('pacman');
  ghosts.forEach(g=>{ getCell(g.r,g.c).classList.add('ghost'); });
}
function updateStats() { statsElem.textContent = `Lives: ${lives} | Dots Left: ${dots}`; }
function isWall(r,c){ return wallmap[r][c]=="W"; }
function move(dx,dy){
  if(!gameActive) return;
  let nr=pac.r+dx,nc=pac.c+dy;
  if(nr<0||nr>=rows||nc<0||nc>=cols||isWall(nr,nc)) return;
  pac.r=nr; pac.c=nc;
  let idx=nr*cols+nc;
  let cell=cells[idx];
  if(cell.querySelector('.dot')) { cell.removeChild(cell.querySelector('.dot')); dots--; }
  ghosts.forEach(g=>{ if(g.r==pac.r&&g.c==pac.c) loseLife(); });
  render();
  updateStats();
  if(dots==0) winGame();
}
function moveGhosts(){
  if(!gameActive) return;
  ghosts.forEach(g=>{
    let tryr=g.r,tryc=g.c+g.dir;
    if(isWall(tryr,tryc) || tryc<0 || tryc>=cols) g.dir*=-1;
    else { g.c+=g.dir; }
    if(g.r==pac.r && g.c==pac.c) loseLife();
  });
  render();
}
function loseLife(){
  lives--;
  updateStats();
  if(lives<=0){
    gameActive=false;
    gameoverElem.textContent = "Game Over!";
    gameoverElem.style.display = restartBtn.style.display = 'block';
    submitPacmanResult(false);
  } else {
    gameoverElem.textContent = "Caught! Lives left: "+lives;
    gameoverElem.style.display = 'block';
    setTimeout(()=>{gameoverElem.style.display='none';},1000);
  }
}
function winGame(){
  gameActive=false;
  winElem.textContent = `You win! Prize: $${lives*50}`;
  winElem.style.display = restartBtn.style.display = 'block';
  submitPacmanResult(true, lives);
}
restartBtn.onclick=()=>{ location.reload(); };

resetGame();
window.addEventListener('keydown',e=>{
  if(!gameActive) return;
  if(e.key=='ArrowLeft') move(0,-1);
  if(e.key=='ArrowRight') move(0,1);
  if(e.key=='ArrowUp') move(-1,0);
  if(e.key=='ArrowDown') move(1,0);
});
setInterval(moveGhosts,500);
function submitPacmanResult(win, lives=0){
  fetch('/api/pacman_result',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({win:win,lives:lives})
  })
  .then(r=>r.json())
  .then(data=>{ if(data.cash!==undefined){
    winElem.textContent += ` | New Balance: $${data.cash}`;
    gameoverElem.textContent += ` | New Balance: $${data.cash}`;
    refreshLeaderboard();
  } });
}
</script>
</body>
</html>
"""

GAMBLEALL_HTML = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8">
<title>Super Gamble: Double or Nothing</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body{font-family:sans-serif;background:#200;color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;}
#game {margin:40px auto;max-width:400px;text-align:center;}
button {padding:13px 28px;font-size:23px; border-radius:7px;margin:26px auto;background:#fd0; color:#200; font-weight:bold; border:none;cursor:pointer;}
#msg{font-size:1.3em; margin:15px;}
#leaderboard-area {margin-top:30px;}
</style>
</head>
<body>
<h1>Super Gamble: Double or Nothing</h1>
<div id="user-area">
    <input type="text" id="username-input" placeholder="Your username">
    <button id="login-btn">Login</button>
    <button id="register-btn">Register</button>
    <span id="user-message"></span>
</div>
<div id="game" style="display:none;">
  <div id="cash"></div>
  <button id="gambleallbtn">Gamble All!</button>
  <div id="msg"></div>
</div>
<div id="leaderboard-area" style="margin-top:30px;">
    <h3>Leaderboard</h3>
    <ul id="leaderboard-list"></ul>
</div>
<script>
let username=null;
function setUser(u){
    username=u;document.getElementById("user-area").style.display="none";
    document.getElementById('game').style.display="";
    getCash();refreshLeaderboard();
}
const loginBtn = document.getElementById('login-btn');
const registerBtn = document.getElementById('register-btn');
const usernameInput = document.getElementById('username-input');
const userMessage = document.getElementById('user-message');
loginBtn.onclick = login;
registerBtn.onclick = register;
function login(){
    const u=usernameInput.value.trim();
    if(!u){userMessage.textContent="Enter a username";return;}
    fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u})})
    .then(r=>r.json().then(d=>[r.status,d]))
    .then(([status,data])=>{if(status===200){setUser(u);}else{userMessage.textContent="User not found. Try Register?";}});
}
function register(){
    const u=usernameInput.value.trim();
    if(!u){userMessage.textContent="Enter a username";return;}
    fetch('/api/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u})})
    .then(r=>r.json().then(d=>[r.status,d]))
    .then(([status,data])=>{if(status===200){setUser(u);}else{userMessage.textContent="Username taken or invalid.";}});
}
function getCash(){
    fetch('/api/cash').then(r=>r.json()).then(data=>{
        if(data.cash!==undefined)
            document.getElementById('cash').textContent = `Your cash: $${data.cash}`;
    });
}
function refreshLeaderboard() {
    fetch('/api/leaderboard')
    .then(r => r.json())
    .then(data => {
        document.getElementById('leaderboard-list').innerHTML = data.leaderboard.map(
            entry => `<li>${entry.username} — $${entry.cash}</li>`
        ).join('');
    });
}
document.getElementById('gambleallbtn').onclick=function(){
    fetch('/api/gambleall',{method:'POST',headers:{'Content-Type':'application/json'}})
    .then(r=>r.json())
    .then(data=>{
        let msg="";
        if("error" in data){
            msg="You need money to play!";
        }else if(data.win){
            msg=`Congratulations! You WON and now have $${data.cash}`;
        }else{
            msg=`Unlucky! You lost it all and now have $${data.cash}`;
        }
        document.getElementById('msg').textContent=msg;
        getCash();refreshLeaderboard();
    });
}
</script>
</body>
</html>
"""

# ==================== Ensure Game & Data Files Exist ====================

def ensure_dirs_and_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(GAMES_DIR, exist_ok=True)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump({}, f)
    for g in GAMES:
        fullpath = os.path.join(GAMES_DIR, g["file"])
        if not os.path.exists(fullpath):
            with open(fullpath, "w", encoding="utf-8") as f:
                if g["template"] == "slots":
                    f.write(SLOTS_HTML)
                elif g["template"] == "pacman":
                    f.write(PACMAN_HTML)
                elif g["template"] == "gambleall":
                    f.write(GAMBLEALL_HTML)
                else:
                    f.write(f"<h1>{g['title']}</h1><p>{g['description']}</p>")

ensure_dirs_and_files()

# ==================== User Functions ====================

def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

# ==================== Routes ====================

@app.route("/")
def homepage():
    html = """<!DOCTYPE html>
<html lang="en"><head>
<title>Casino Homepage</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body { font-family:sans-serif; background:#222; color:#fff; min-height:100vh; margin:0; }
h1 { margin-top:40px; }
.game-list { display:flex; flex-wrap:wrap; gap:2em; margin:2em 0;}
.game-card { background:#333; border-radius:10px; padding:1.5em; min-width:200px; box-shadow:2px 2px 8px #0007;}
.game-card a { color:#fd0; text-decoration:none; font-weight:bold; font-size:1.15em;}
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
    users = load_users()
    username = request.json.get('username', '').strip()
    if not username:
        return jsonify({'error': 'empty'}), 400
    if username in users:
        return jsonify({'error':'exists'}), 400
    users[username] = 1000
    save_users(users)
    session['username'] = username
    return jsonify({'cash':users[username]})

@app.route('/api/login', methods=['POST'])
def login():
    users = load_users()
    username = request.json.get('username', '').strip()
    if not username or username not in users:
        return jsonify({'error':'notfound'}), 404
    session['username'] = username
    return jsonify({'cash':users[username]})

@app.route('/api/cash', methods=['GET'])
def cash():
    users = load_users()
    username = session.get('username')
    if not username or username not in users:
        return jsonify({'error':'notloggedin'}), 401
    return jsonify({'cash':users[username]})

@app.route('/api/play', methods=['POST'])
def play():
    users = load_users()
    username = session.get('username')
    if not username or username not in users:
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
    save_users(users)
    return jsonify({'result': result, 'win': win, 'cash': users[username]})

@app.route('/api/leaderboard', methods=['GET'])
def leaderboard():
    users = load_users()
    top = sorted(users.items(), key=lambda x: x[1], reverse=True)[:10]
    return jsonify({'leaderboard': [{'username': u, 'cash': c} for u, c in top]})

@app.route('/api/pacman_result', methods=['POST'])
def pacman_result():
    users = load_users()
    username = session.get('username')
    if not username or username not in users:
        return jsonify({'error':'notloggedin'}), 401
    win = bool(request.json.get('win'))
    lives_left = int(request.json.get('lives', 0))
    if win:
        gain = lives_left * 50
        users[username] += gain
    else:
        loss = 100
        users[username] -= loss
        if users[username]<0: users[username]=0
    save_users(users)
    return jsonify({'cash':users[username]})

@app.route('/api/gambleall', methods=['POST'])
def gambleall():
    import random
    users = load_users()
    username = session.get('username')
    if not username or username not in users:
        return jsonify({'error':'notloggedin'}), 401
    cash = users[username]
    if cash < 1: return jsonify({'error':'nocash'})
    win = random.choice([True, False])
    if win:
        users[username] *= 2
    else:
        users[username] = 0
    save_users(users)
    return jsonify({'win':win, 'cash':users[username]})

if __name__ == "__main__":
    ensure_dirs_and_files()
    app.run(debug=True)
