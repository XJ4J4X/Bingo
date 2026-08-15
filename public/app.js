console.log('%c' + `
      ██╗██╗  ██╗██╗  ██╗    ████████╗███████╗██████╗ ██╗  ██╗
      ██║██║  ██║╚██╗██╔╝    ╚══██╔══╝██╔════╝██╔══██╗██║  ██║
      ██║███████║ ╚███╔╝        ██║   █████╗  ██║  ██║███████║
 ██   ██║╚════██║ ██╔██╗        ██║   ██╔══╝  ██║  ██║██╔══██║
 ╚█████╔╝     ██║██╔╝ ██╗       ██║   ███████╗██████╔╝██║  ██║
  ╚════╝      ╚═╝╚═╝  ╚═╝       ╚═╝   ╚══════╝╚═════╝ ╚═╝  ╚═╝
`, "color: #00ff00; font-weight: bold; text-shadow: 0 0 10px #00ff00, 0 0 20px #00ff00;");

let currentUser = null;
let currentPassword = null;
let stateInterval = null;
let timeLeft = 0;
let isGameActive = false;
let gridLocked = true;
let hasSubmittedScore = false;

let BINGO_PHRASES = [];

const authSection = document.getElementById('auth-section');
const gameSection = document.getElementById('game-section');
const userInfo = document.getElementById('user-info');
const currentPseudoSpan = document.getElementById('current-pseudo');
const logoutBtn = document.getElementById('logout-btn');

const pseudoInput = document.getElementById('pseudo-input');
const passwordGroup = document.getElementById('password-group');
const passwordInput = document.getElementById('password-input');
const loginBtn = document.getElementById('login-btn');
const registerBtn = document.getElementById('register-btn');
const authMessage = document.getElementById('auth-message');
const generatedPasswordDiv = document.getElementById('generated-password');
const passwordDisplay = document.getElementById('password-display');
const continueToGameBtn = document.getElementById('continue-to-game-btn');
const switchToLogin = document.getElementById('switch-to-login');
const switchToRegister = document.getElementById('switch-to-register');

const bingoGrid = document.getElementById('bingo-grid');
const timerDisplay = document.getElementById('timer');
const validateGridBtn = document.getElementById('validate-grid-btn');
const gameMessage = document.getElementById('game-message');

const leaderboardBody = document.getElementById('leaderboard-body');

async function init() {
    loadLeaderboard();
    await fetchPhrases();
}

async function fetchPhrases() {
    try {
        const res = await fetch('/api/phrases');
        const data = await res.json();
        BINGO_PHRASES = data.map(item => item.phrase);
    } catch (err) {
        console.error("Erreur chargement phrases", err);
    }
}

function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
}

function formatTime(seconds) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

switchToLogin.addEventListener('click', (e) => {
    e.preventDefault();
    passwordGroup.classList.remove('hidden');
    loginBtn.classList.remove('hidden');
    registerBtn.classList.add('hidden');
    switchToLogin.classList.add('hidden');
    switchToRegister.classList.remove('hidden');
    authMessage.textContent = "";
});

switchToRegister.addEventListener('click', (e) => {
    e.preventDefault();
    passwordGroup.classList.add('hidden');
    loginBtn.classList.add('hidden');
    registerBtn.classList.remove('hidden');
    switchToLogin.classList.remove('hidden');
    switchToRegister.classList.add('hidden');
    authMessage.textContent = "";
});

registerBtn.addEventListener('click', async () => {
    const pseudo = pseudoInput.value.trim();
    if (!pseudo) {
        authMessage.textContent = "Veuillez entrer un pseudo.";
        return;
    }

    try {
        const res = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pseudo })
        });
        
        const data = await res.json();
        
        if (res.ok) {
            authMessage.textContent = "";
            passwordDisplay.textContent = data.password;
            generatedPasswordDiv.classList.remove('hidden');
            registerBtn.disabled = true;
            
            currentUser = pseudo;
            currentPassword = data.password;
        } else {
            authMessage.textContent = data.error || "Erreur lors de l'inscription.";
        }
    } catch (err) {
        authMessage.textContent = "Erreur de connexion au serveur.";
    }
});

loginBtn.addEventListener('click', async () => {
    const pseudo = pseudoInput.value.trim();
    const password = passwordInput.value.trim();
    
    if (!pseudo || !password) {
        authMessage.textContent = "Veuillez remplir tous les champs.";
        return;
    }

    try {
        const res = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pseudo, password })
        });
        
        if (res.ok) {
            currentUser = pseudo;
            currentPassword = password;
            startGame();
        } else {
            const data = await res.json();
            authMessage.textContent = data.error || "Identifiants incorrects.";
        }
    } catch (err) {
        authMessage.textContent = "Erreur de connexion au serveur.";
    }
});

continueToGameBtn.addEventListener('click', () => {
    startGame();
});

logoutBtn.addEventListener('click', () => {
    currentUser = null;
    currentPassword = null;
    clearInterval(stateInterval);
    
    authSection.classList.remove('hidden');
    gameSection.classList.add('hidden');
    userInfo.classList.add('hidden');
    
    pseudoInput.value = "";
    passwordInput.value = "";
    generatedPasswordDiv.classList.add('hidden');
    registerBtn.disabled = false;
    authMessage.textContent = "";
});

function startGame() {
    authSection.classList.add('hidden');
    gameSection.classList.remove('hidden');
    userInfo.classList.remove('hidden');
    currentPseudoSpan.textContent = currentUser;
    
    hasSubmittedScore = false;
    gameMessage.textContent = "";
    validateGridBtn.disabled = true;
    
    generateGrid();
    startStateSync();
}

function generateGrid() {
    bingoGrid.innerHTML = '';
    
    let phrasesToUse = [...BINGO_PHRASES];
    shuffleArray(phrasesToUse);
    
    for (let i = 0; i < 16; i++) {
        const cell = document.createElement('div');
        cell.className = 'bingo-cell';
        cell.textContent = phrasesToUse[i] || "Case Vide";
        
        cell.addEventListener('click', () => {
            if (!gridLocked) {
                cell.classList.toggle('checked');
            }
        });
        
        bingoGrid.appendChild(cell);
    }
}

function startStateSync() {
    clearInterval(stateInterval);
    syncState();
    stateInterval = setInterval(syncState, 1000);
}

async function syncState() {
    try {
        const res = await fetch('/api/game/state');
        const data = await res.json();
        
        isGameActive = data.is_active;
        timeLeft = data.time_left;
        
        if (isGameActive) {
            timerDisplay.textContent = formatTime(timeLeft);
            gridLocked = false;
            validateGridBtn.disabled = true;
            
            if(!hasSubmittedScore) {
                gameMessage.textContent = "Live en cours... Cochez les cases !";
                gameMessage.style.color = "blue";
            }
        } else {
            timerDisplay.textContent = "00:00 - HORS LIGNE";
            gridLocked = true;
            
            if (!hasSubmittedScore && timeLeft === 0 && timerDisplay.textContent !== "00:00 - HORS LIGNE") {
               validateGridBtn.disabled = false;
               gameMessage.textContent = "Le Live est terminé, validez votre grille !";
               gameMessage.style.color = "orange";
            } 
            else if (!hasSubmittedScore && timeLeft === 0) {
               validateGridBtn.disabled = true;
               gameMessage.textContent = "En attente du lancement du Live par l'administrateur.";
               gameMessage.style.color = "gray";
            }
        }
        
        if (!isGameActive && timeLeft === 0 && !hasSubmittedScore && document.querySelectorAll('.bingo-cell.checked').length > 0) {
            validateGridBtn.disabled = false;
        }

    } catch (err) {
        console.error("Erreur sync game state", err);
    }
}

validateGridBtn.addEventListener('click', async () => {
    if (!currentUser || !currentPassword || hasSubmittedScore) return;
    
    const checkedCount = document.querySelectorAll('.bingo-cell.checked').length;
    const score = checkedCount * 10;
    
    validateGridBtn.disabled = true;
    
    try {
        const res = await fetch('/api/score', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                pseudo: currentUser,
                password: currentPassword,
                score: score
            })
        });
        
        if (res.ok) {
            gameMessage.style.color = "green";
            gameMessage.textContent = `Grille validée ! Vous avez gagné ${score} points.`;
            hasSubmittedScore = true;
            loadLeaderboard();
        } else {
            gameMessage.style.color = "red";
            gameMessage.textContent = "Erreur lors de la validation.";
            validateGridBtn.disabled = false;
        }
    } catch (err) {
        gameMessage.style.color = "red";
        gameMessage.textContent = "Erreur de connexion au serveur.";
        validateGridBtn.disabled = false;
    }
});

async function loadLeaderboard() {
    try {
        const res = await fetch('/api/leaderboard');
        const data = await res.json();
        
        leaderboardBody.innerHTML = '';
        
        if (data.length === 0) {
            leaderboardBody.innerHTML = '<tr><td colspan="3" style="text-align: center;">Aucun score pour le moment.</td></tr>';
            return;
        }
        
        data.forEach((user, index) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>#${index + 1}</td>
                <td>${user.pseudo}</td>
                <td>${user.score} pts</td>
            `;
            leaderboardBody.appendChild(tr);
        });
    } catch (err) {
        console.error("Erreur chargement classement", err);
    }
}

init();
