// Aminato si tu lis cette phrase j'ai galerer mdr
console.log('%c' + `
               _    __  __ ___ _  _    _ _____ ___  
             /_\\  |  \\/  |_ _| \\| |  /_\\_   _/ _ \\ 
            / _ \\ | |\\/| || || .' | / _ \\| || (_) |
           /_/ \\_\\|_|  |_|___|_|\\_|/_/ \\_\\_| \\___/ 
          .-----.
        /         \\
       |   O   O   |
       |           |
       |           |
       |           |
       '~~^~~^~~^~~'
`, "color: #ffffff; font-weight: bold; text-shadow: 0 0 10px #ffffff;");

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
const colorPickerSection = document.getElementById('color-picker-section');
const userColorPicker = document.getElementById('user-color-picker');
const saveColorBtn = document.getElementById('save-color-btn');

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
            localStorage.setItem('userPseudo', currentUser);
            localStorage.setItem('userPassword', currentPassword);
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
    localStorage.removeItem('userPseudo');
    localStorage.removeItem('userPassword');
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

// Auto-login for players
document.addEventListener('DOMContentLoaded', async () => {
    const savedPseudo = localStorage.getItem('userPseudo');
    const savedPassword = localStorage.getItem('userPassword');
    if (savedPseudo && savedPassword) {
        try {
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pseudo: savedPseudo, password: savedPassword })
            });
            if (res.ok) {
                currentUser = savedPseudo;
                currentPassword = savedPassword;
                startGame();
            } else {
                localStorage.removeItem('userPseudo');
                localStorage.removeItem('userPassword');
            }
        } catch(e) {
            console.error(e);
        }
    }
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
        const phraseText = phrasesToUse[i] || "Case Vide";
        cell.setAttribute('data-phrase', phraseText);
        cell.innerHTML = phraseText.replace(/J4X/gi, '<span class="j4x-highlight">$&</span>');
        
        cell.addEventListener('click', () => {
            if (!gridLocked) {
                if (!cell.classList.contains('checked')) {
                    const checkedCount = document.querySelectorAll('.bingo-cell.checked').length;
                    if (checkedCount >= 5) {
                        alert("Anti-triche : Vous ne pouvez cocher que 5 cases maximum !");
                        return;
                    }
                }
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

saveColorBtn.addEventListener('click', async () => {
    const color = userColorPicker.value;
    try {
        const res = await fetch('/api/user/color?t=' + Date.now(), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                color: color,
                pseudo: currentUser,
                password: currentPassword
            })
        });
        if (res.ok) {
            alert("Couleur sauvegardée avec succès !");
            colorPickerSection.classList.add('hidden');
            loadLeaderboard();
        } else {
            alert("Erreur lors de la sauvegarde de la couleur.");
        }
    } catch (e) {
        console.error(e);
    }
});

async function syncState() {
    try {
        const res = await fetch('/api/game/state?t=' + Date.now());
        const data = await res.json();
        
        isGameActive = data.is_active;
        timeLeft = data.time_left;
        
        if (isGameActive) {
            timerDisplay.textContent = formatTime(timeLeft);
            
            if (data.is_locked) {
                gridLocked = true;
                document.getElementById('bingo-grid').classList.add('locked-grid');
                if(!hasSubmittedScore) {
                    validateGridBtn.disabled = true;
                    gameMessage.textContent = "VÉRIFICATION EN COURS...";
                    gameMessage.style.color = "orange";
                    gameMessage.style.fontWeight = "bold";
                }
            } else {
                gridLocked = false;
                document.getElementById('bingo-grid').classList.remove('locked-grid');
                if(!hasSubmittedScore) {
                    validateGridBtn.disabled = false;
                    gameMessage.textContent = "Live en cours... Cochez max 5 cases et validez !";
                    gameMessage.style.color = "blue";
                    gameMessage.style.fontWeight = "normal";
                }
            }
        } else {
            timerDisplay.textContent = "00:00 - HORS LIGNE";
            gridLocked = true;
            validateGridBtn.disabled = true;
            
            // Si le joueur a déjà soumis mais que la partie vient de se terminer, on actualise son score final
            if (hasSubmittedScore && window.wasGameActive && window.currentUser) {
                try {
                    const res = await fetch('/api/user_score', {
                        headers: { 'pseudo': currentUser, 'password': currentPassword }
                    });
                    if (res.ok) {
                        const data = await res.json();
                        gameMessage.style.color = "green";
                        gameMessage.textContent = `Grille validée ! Vous avez maintenant ${data.score} points.`;
                        
                        try {
                            const audio = new Audio('ting.mp3');
                            audio.play();
                        } catch (e) { }
                        
                        if (typeof confetti === 'function') {
                            confetti({
                                particleCount: 100,
                                spread: 70,
                                origin: { y: 0.6 },
                                colors: ['#00ff00', '#ffffff', '#ff0000']
                            });
                        }
                    }
                } catch(e) { console.error(e); }
            }
            // Auto validation when game ends or is stopped manually by Admin (if not submitted early)
            else if (!hasSubmittedScore && window.wasGameActive && window.currentUser) {
                gameMessage.textContent = "Fin du Live ! Validation automatique en cours...";
                gameMessage.style.color = "orange";
                validateGridBtn.disabled = false;
                validateGridBtn.click();
            }
            else if (!hasSubmittedScore && timeLeft === 0 && timerDisplay.textContent !== "00:00 - HORS LIGNE") {
               gameMessage.textContent = "Le Live est terminé.";
               gameMessage.style.color = "orange";
            } 
            else if (!hasSubmittedScore && timeLeft === 0) {
               gameMessage.textContent = "En attente du lancement du Live par l'administrateur.";
               gameMessage.style.color = "gray";
            }
        }
        
        window.wasGameActive = isGameActive;
        loadLeaderboard();
        loadUserStats();
        
        // Show color picker if user is the winner
        if (currentUser && data.color_choice_user_pseudo === currentUser) {
            colorPickerSection.classList.remove('hidden');
        } else if (colorPickerSection && !colorPickerSection.classList.contains('hidden')) {
            colorPickerSection.classList.add('hidden');
        }
        
    } catch (err) {
        console.error("Erreur sync game state", err);
    }
}

validateGridBtn.addEventListener('click', async () => {
    if (!currentUser || !currentPassword || hasSubmittedScore) return;
    
    const checkedCells = document.querySelectorAll('.bingo-cell.checked');
    const checkedPhrases = Array.from(checkedCells).map(c => c.getAttribute('data-phrase'));
    
    validateGridBtn.disabled = true;
    gridLocked = true;
    
    try {
        const res = await fetch('/api/score', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                pseudo: currentUser,
                password: currentPassword,
                checked_phrases: checkedPhrases
            })
        });
        
        const data = await res.json();
        if (res.ok) {
            hasSubmittedScore = true;
            if (data.pending) {
                gameMessage.style.color = "orange";
                gameMessage.textContent = "Grille envoyée ! En attente de la validation de l'administrateur à la fin du live...";
            } else {
                gameMessage.style.color = "green";
                gameMessage.textContent = `Grille validée ! Vous avez maintenant ${data.new_score} points.`;
                loadLeaderboard();
                
                // Effets de célébration
                try {
                    const audio = new Audio('ting.mp3');
                    audio.play();
                } catch (e) { console.error("Audio play failed:", e); }
                
                if (typeof confetti === 'function') {
                    confetti({
                        particleCount: 100,
                        spread: 70,
                        origin: { y: 0.6 },
                        colors: ['#00ff00', '#ffffff', '#ff0000']
                    });
                }
            }
        } else {
            gameMessage.style.color = "red";
            gameMessage.textContent = "Erreur lors de la validation.";
            validateGridBtn.disabled = false;
            gridLocked = false;
        }
    } catch (err) {
        gameMessage.style.color = "red";
        gameMessage.textContent = "Erreur de connexion au serveur.";
        validateGridBtn.disabled = false;
        gridLocked = false;
    }
});

let currentLeaderboardMode = 'score';
let leaderboardData = { top_score: [], top_wins: [] };

document.getElementById('btn-top-score')?.addEventListener('click', () => {
    currentLeaderboardMode = 'score';
    document.getElementById('btn-top-score').classList.add('active');
    document.getElementById('btn-top-wins').classList.remove('active');
    document.getElementById('leaderboard-value-header').textContent = 'Score';
    renderLeaderboard();
});

document.getElementById('btn-top-wins')?.addEventListener('click', () => {
    currentLeaderboardMode = 'wins';
    document.getElementById('btn-top-wins').classList.add('active');
    document.getElementById('btn-top-score').classList.remove('active');
    document.getElementById('leaderboard-value-header').textContent = 'Victoires';
    renderLeaderboard();
});

async function loadLeaderboard() {
    try {
        const res = await fetch('/api/leaderboard?t=' + Date.now());
        leaderboardData = await res.json();
        renderLeaderboard();
    } catch (err) {
        console.error("Erreur classement:", err);
    }
}

function renderLeaderboard() {
    leaderboardBody.innerHTML = '';
    const data = currentLeaderboardMode === 'score' ? leaderboardData.top_score : leaderboardData.top_wins;
    
    if (!data || data.length === 0) {
        leaderboardBody.innerHTML = '<tr><td colspan="3" style="text-align: center;">Aucun score pour le moment.</td></tr>';
        return;
    }
    
    data.forEach((user, index) => {
        const tr = document.createElement('tr');
        
        let pseudoDisplay = user.pseudo.replace(/J4X/gi, '<span class="j4x-highlight">$&</span>');
        let pseudoClass = '';
        let pseudoStyle = '';
        
        if (user.pseudo.toLowerCase() === 'aminat0_') {
            pseudoClass = 'aminato-effect';
        }
        
        if (user.color) {
            pseudoStyle = `color: ${user.color}; font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);`;
        } else if (currentUser && user.pseudo === currentUser) {
            pseudoStyle = 'font-weight: bold;';
        }
        
        if (currentUser && user.pseudo === currentUser) {
            tr.style.backgroundColor = 'var(--bg-tertiary)'; // Highlight
        }
        
        const val = currentLeaderboardMode === 'score' ? `${user.score} pts` : `${user.wins} victoires`;
        
        tr.innerHTML = `
            <td>#${index + 1}</td>
            <td class="${pseudoClass}" style="${pseudoStyle}">${pseudoDisplay}</td>
            <td>${val}</td>
        `;
        leaderboardBody.appendChild(tr);
    });
}

async function loadUserStats() {
    if (!currentUser || !currentPassword) return;
    try {
        const res = await fetch('/api/user_stats', {
            headers: {
                'pseudo': currentUser,
                'password': currentPassword
            }
        });
        if (res.ok) {
            const data = await res.json();
            document.getElementById('stats-section').classList.remove('hidden');
            
            document.getElementById('my-score').textContent = data.score || 0;
            document.getElementById('my-wins').textContent = data.wins || 0;
            document.getElementById('my-participations').textContent = data.lives_participated || 0;
            
            let accuracy = 0;
            if (data.boxes_checked > 0) {
                accuracy = Math.round((data.boxes_correct / data.boxes_checked) * 100);
            }
            document.getElementById('my-accuracy').textContent = accuracy;
            document.getElementById('accuracy-progress').style.width = accuracy + '%';
            
            const phrasesList = document.getElementById('top-phrases-list');
            phrasesList.innerHTML = '';
            if (data.top_phrases && data.top_phrases.length > 0) {
                data.top_phrases.forEach(p => {
                    const li = document.createElement('li');
                    li.textContent = `${p.phrase} (${p.count} fois)`;
                    phrasesList.appendChild(li);
                });
            } else {
                phrasesList.innerHTML = '<li>Aucune donnée pour le moment.</li>';
            }
        }
    } catch (e) {
        console.error('Erreur stats', e);
    }
}

init();

// Theme toggle logic
document.addEventListener('DOMContentLoaded', () => {
    const themeBtn = document.getElementById('theme-toggle');
    const currentTheme = localStorage.getItem('theme');
    if (currentTheme === 'dark') {
        document.body.classList.add('dark-mode');
        if (themeBtn) themeBtn.textContent = '☀️';
    }
    
    if (themeBtn) {
        themeBtn.addEventListener('click', () => {
            document.body.classList.toggle('dark-mode');
            if (document.body.classList.contains('dark-mode')) {
                localStorage.setItem('theme', 'dark');
                themeBtn.textContent = '☀️';
            } else {
                localStorage.setItem('theme', 'light');
                themeBtn.textContent = '🌙';
            }
        });
    }
});
