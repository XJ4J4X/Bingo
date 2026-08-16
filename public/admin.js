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

let adminToken = null;
let adminRole = null;
let stateInterval = null;

const loginSection = document.getElementById('login-section');
const adminContent = document.getElementById('admin-content');
const adminInfo = document.getElementById('admin-info');
const adminPasswordInput = document.getElementById('admin-password');
const loginBtn = document.getElementById('login-btn');
const logoutBtn = document.getElementById('logout-btn');
const loginMessage = document.getElementById('login-message');

const startGameBtn = document.getElementById('start-game-btn');
const stopGameBtn = document.getElementById('stop-game-btn');
const timerDurationInput = document.getElementById('timer-duration');
const gameStatus = document.getElementById('game-status');
const timerDisplay = document.getElementById('timer-display');

const resetScoresBtn = document.getElementById('reset-scores-btn');
const createUserBtn = document.getElementById('create-user-btn');
const newUserPseudoInput = document.getElementById('new-user-pseudo');
const usersTableBody = document.getElementById('users-table-body');

const addPhraseBtn = document.getElementById('add-phrase-btn');
const newPhraseInput = document.getElementById('new-phrase-input');
const phrasesTableBody = document.getElementById('phrases-table-body');

const newAdminPasswordInput = document.getElementById('new-admin-password');
const createAdminBtn = document.getElementById('create-admin-btn');
const superadminSection = document.getElementById('superadmin-section');
const adminsTableBody = document.getElementById('admins-table-body');

loginBtn.addEventListener('click', async () => {
    const pwd = adminPasswordInput.value;
    try {
        const res = await fetch('/api/admin/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password: pwd })
        });
        const data = await res.json();
        
        if (res.ok && data.success) {
            adminToken = data.token;
            adminRole = data.role;
            localStorage.setItem('adminToken', adminToken);
            localStorage.setItem('adminRole', adminRole);
            loginSection.style.display = 'none';
            adminContent.style.display = 'block';
            adminInfo.classList.remove('hidden');
            initAdmin();
        } else {
            loginMessage.textContent = "Mot de passe incorrect.";
        }
    } catch (err) {
        loginMessage.textContent = "Erreur de connexion.";
    }
});

function logoutAdmin() {
    adminToken = null;
    adminRole = null;
    localStorage.removeItem('adminToken');
    localStorage.removeItem('adminRole');
    loginSection.style.display = 'block';
    adminContent.style.display = 'none';
    adminInfo.classList.add('hidden');
    adminPasswordInput.value = '';
    clearInterval(stateInterval);
}

logoutBtn.addEventListener('click', logoutAdmin);

async function fetchWithAuth(url, options = {}) {
    if (!options.headers) options.headers = {};
    options.headers['Authorization'] = `Bearer ${adminToken}`;
    const res = await fetch(url, options);
    if (res.status === 401 || res.status === 403) {
        logoutAdmin();
    }
    return res;
}

function initAdmin() {
    loadUsers();
    loadPhrases();
    loadProfiles();
    syncGameState();
    
    if (adminRole === 'superadmin') {
        superadminSection.style.display = 'block';
        loadAdmins();
    } else {
        superadminSection.style.display = 'none';
    }
    
    clearInterval(stateInterval);
    stateInterval = setInterval(syncGameState, 1000);
}

// Auto-login if token exists in localStorage
document.addEventListener('DOMContentLoaded', () => {
    const savedToken = localStorage.getItem('adminToken');
    const savedRole = localStorage.getItem('adminRole');
    if (savedToken && savedRole) {
        adminToken = savedToken;
        adminRole = savedRole;
        loginSection.style.display = 'none';
        adminContent.style.display = 'block';
        adminInfo.classList.remove('hidden');
        initAdmin();
    }
});

function formatTime(seconds) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

async function syncGameState() {
    try {
        const res = await fetch('/api/game/state');
        const data = await res.json();
        
        if (data.is_active) {
            if (data.is_locked) {
                gameStatus.textContent = "Verrouillé (Vérification)";
                gameStatus.style.color = "orange";
                document.getElementById('stop-game-btn').textContent = "Terminer & Valider les Scores";
                document.getElementById('stop-game-btn').className = "success-btn";
            } else {
                gameStatus.textContent = "En cours (Jeu)";
                gameStatus.style.color = "green";
                document.getElementById('stop-game-btn').textContent = "Arrêter le Live";
                document.getElementById('stop-game-btn').className = "danger-btn";
            }
            timerDisplay.textContent = formatTime(data.time_left);
            document.getElementById('live-control-section').style.display = 'block';
            loadLiveData();
        } else {
            gameStatus.textContent = "Hors ligne";
            gameStatus.style.color = "red";
            timerDisplay.textContent = "00:00";
            document.getElementById('live-control-section').style.display = 'none';
            document.getElementById('stop-game-btn').textContent = "Arrêter le Live";
            document.getElementById('stop-game-btn').className = "danger-btn";
        }
        loadUsers();
    } catch (err) {
        console.error("Erreur sync timer", err);
    }
}

async function loadLiveData() {
    try {
        const res = await fetchWithAuth('/api/admin/game/live_data');
        if (!res.ok) return;
        const data = await res.json();
        
        const grid = document.getElementById('admin-live-grid');
        
        // If empty, create the grid cells
        if (grid.children.length === 0) {
            data.active_phrases.forEach(phrase => {
                const cell = document.createElement('div');
                cell.className = 'bingo-cell';
                cell.id = 'chk-' + btoa(unescape(encodeURIComponent(phrase))).replace(/=/g, '');
                
                const highlighted = phrase.replace(/J4X/gi, '<span class="j4x-highlight">$&</span>');
                cell.innerHTML = highlighted;
                
                cell.addEventListener('click', () => {
                    const newlyChecked = !cell.classList.contains('checked');
                    cell.classList.toggle('checked');
                    toggleTick(phrase, newlyChecked);
                });
                
                grid.appendChild(cell);
            });
        }
        
        // Update their checked status without overwriting the DOM
        data.active_phrases.forEach(phrase => {
            const isChecked = data.admin_ticked.includes(phrase);
            const chkId = 'chk-' + btoa(unescape(encodeURIComponent(phrase))).replace(/=/g, '');
            const cell = document.getElementById(chkId);
            if (cell) {
                if (isChecked && !cell.classList.contains('checked')) {
                    cell.classList.add('checked');
                } else if (!isChecked && cell.classList.contains('checked')) {
                    cell.classList.remove('checked');
                }
            }
        });
    } catch (err) { console.error(err); }
}

window.toggleTick = async function(phrase, isChecked) {
    await fetchWithAuth('/api/admin/game/tick', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phrase: phrase, checked: isChecked })
    });
};


startGameBtn.addEventListener('click', async () => {
    const durationMins = parseInt(timerDurationInput.value, 10) || 10;
    const durationSecs = durationMins * 60;
    
    const lockDurationInput = document.getElementById('timer-lock-duration');
    const lockDurationMins = lockDurationInput ? (parseInt(lockDurationInput.value, 10) || 0) : 0;
    const lockDurationSecs = lockDurationMins * 60;
    
    const profileId = document.getElementById('profile-select').value;
    const verificationMode = document.getElementById('verification-mode').value;
    
    await fetchWithAuth('/api/admin/game/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            duration: durationSecs, 
            lock_duration: lockDurationSecs,
            profile_id: profileId, 
            verification_mode: verificationMode 
        })
    });
    syncGameState();
});

stopGameBtn.addEventListener('click', async () => {
    await fetchWithAuth('/api/admin/game/stop', { method: 'POST' });
    syncGameState();
});

async function loadUsers() {
    try {
        const res = await fetchWithAuth('/api/admin/users');
        if (!res.ok) return;
        const users = await res.json();
        
        usersTableBody.innerHTML = '';
        
        users.forEach(u => {
            const tr = document.createElement('tr');
            const pseudoHtml = u.pseudo.replace(/J4X/gi, '<span class="j4x-highlight">$&</span>');
            tr.innerHTML = `
                <td>${u.id}</td>
                <td><strong>${pseudoHtml}</strong></td>
                <td><code>${u.password}</code></td>
                <td><strong>${u.score}</strong></td>
                <td>
                    <button class="small-btn add-pts-btn success-btn" data-id="${u.id}">+10</button>
                    <button class="small-btn sub-pts-btn warning-btn" data-id="${u.id}">-10</button>
                </td>
                <td><button class="small-btn delete-btn danger-btn" data-id="${u.id}">Supprimer</button></td>
            `;
            usersTableBody.appendChild(tr);
        });
        
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                if (confirm('Vraiment supprimer ce joueur ?')) {
                    const id = e.target.getAttribute('data-id');
                    await fetchWithAuth('/api/admin/users/delete', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ id: id })
                    });
                    loadUsers();
                }
            });
        });
        
        document.querySelectorAll('.add-pts-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const id = e.target.getAttribute('data-id');
                await fetchWithAuth('/api/admin/users/points', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: id, points: 10 })
                });
                loadUsers();
            });
        });
        
        document.querySelectorAll('.sub-pts-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const id = e.target.getAttribute('data-id');
                await fetchWithAuth('/api/admin/users/points', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: id, points: -10 })
                });
                loadUsers();
            });
        });

    } catch (e) { console.error(e); }
}

resetScoresBtn.addEventListener('click', async () => {
    if (confirm('Remettre tous les scores à 0 pour le prochain Live ?')) {
        await fetchWithAuth('/api/admin/users/reset', { method: 'POST' });
        loadUsers();
    }
});

createUserBtn.addEventListener('click', async () => {
    const pseudo = newUserPseudoInput.value.trim();
    if (pseudo) {
        const res = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pseudo })
        });
        if (res.ok) {
            newUserPseudoInput.value = '';
            loadUsers();
            alert('Joueur créé ! Son mot de passe est visible dans le tableau.');
        } else {
            alert('Erreur : Ce pseudo est peut-être déjà pris.');
        }
    }
});

async function loadPhrases() {
    try {
        const res = await fetch('/api/phrases');
        const phrases = await res.json();
        
        phrasesTableBody.innerHTML = '';
        phrases.forEach(p => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${p.id}</td>
                <td>${p.phrase}</td>
                <td><button class="small-btn delete-phrase-btn danger-btn" data-id="${p.id}">Supprimer</button></td>
            `;
            phrasesTableBody.appendChild(tr);
        });
        
        document.querySelectorAll('.delete-phrase-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                if (confirm('Vraiment supprimer cette phrase ?')) {
                    const id = e.target.getAttribute('data-id');
                    await fetchWithAuth('/api/admin/phrases/delete', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ id: id })
                    });
                    loadPhrases();
                }
            });
        });
    } catch (e) { console.error(e); }
}

addPhraseBtn.addEventListener('click', async () => {
    const phrase = newPhraseInput.value.trim();
    if (phrase) {
        await fetchWithAuth('/api/admin/phrases/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phrase })
        });
        newPhraseInput.value = '';
        loadPhrases();
    }
});

createAdminBtn.addEventListener('click', async () => {
    const newPwd = newAdminPasswordInput.value.trim();
    if (newPwd) {
        if (confirm("Voulez-vous créer ce nouveau mot de passe admin ?")) {
            const res = await fetchWithAuth('/api/admin/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password: newPwd })
            });
            
            if (res.ok) {
                alert("Nouveau compte administrateur créé avec succès !");
                newAdminPasswordInput.value = '';
                loadAdmins();
            } else {
                alert("Erreur (ce mot de passe existe peut-être déjà).");
            }
        }
    } else {
        alert("Veuillez taper un mot de passe valide.");
    }
});

async function loadAdmins() {
    if (adminRole !== 'superadmin') return;
    try {
        const res = await fetchWithAuth('/api/admin/list_admins');
        if (!res.ok) return;
        const admins = await res.json();
        
        adminsTableBody.innerHTML = '';
        admins.forEach(a => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${a.id}</td>
                <td><code>${a.password}</code></td>
                <td><strong>${a.role}</strong></td>
                <td>
                    ${a.role !== 'superadmin' ? `<button class="small-btn delete-admin-btn danger-btn" data-id="${a.id}">Supprimer</button>` : ''}
                </td>
            `;
            adminsTableBody.appendChild(tr);
        });
        
        document.querySelectorAll('.delete-admin-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                if (confirm('Vraiment supprimer cet administrateur ?')) {
                    const id = e.target.getAttribute('data-id');
                    await fetchWithAuth('/api/admin/delete_admin', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ id: id })
                    });
                    loadAdmins();
                }
            });
        });
    } catch (e) { console.error(e); }
}

async function loadProfiles() {
    try {
        const res = await fetchWithAuth('/api/admin/profiles');
        if (!res.ok) return;
        const profiles = await res.json();
        
        const select = document.getElementById('profile-select');
        select.innerHTML = '<option value="random">Aléatoire (BDD)</option>';
        
        const tbody = document.getElementById('profiles-table-body');
        tbody.innerHTML = '';
        
        profiles.forEach(p => {
            select.innerHTML += `<option value="${p.id}">${p.name}</option>`;
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${p.id}</td>
                <td><strong>${p.name}</strong></td>
                <td><button class="small-btn danger-btn delete-profile-btn" data-id="${p.id}">Supprimer</button></td>
            `;
            tbody.appendChild(tr);
        });
        
        document.querySelectorAll('.delete-profile-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                if (confirm('Supprimer ce profil ?')) {
                    const id = e.target.getAttribute('data-id');
                    await fetchWithAuth('/api/admin/profiles/delete', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ id: id })
                    });
                    loadProfiles();
                }
            });
        });
    } catch (e) { console.error(e); }
}

const addProfileBtn = document.getElementById('add-profile-btn');
if (addProfileBtn) {
    addProfileBtn.addEventListener('click', async () => {
        const name = document.getElementById('new-profile-name').value.trim();
        const text = document.getElementById('new-profile-phrases').value.trim();
        if (name && text) {
            await fetchWithAuth('/api/admin/profiles/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: name, phrases_text: text })
            });
            document.getElementById('new-profile-name').value = '';
            document.getElementById('new-profile-phrases').value = '';
            loadProfiles();
        }
    });
}

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

// --- STATS LOGIC ---
const navMainBtn = document.getElementById('nav-main-btn');
const navStatsBtn = document.getElementById('nav-stats-btn');
const mainAdminPanel = document.getElementById('main-admin-panel');
const statsSection = document.getElementById('stats-section');
const statsUsersContainer = document.getElementById('stats-users-container');
const statsPhrasesContainer = document.getElementById('stats-phrases-container');

if (navMainBtn && navStatsBtn) {
    navMainBtn.addEventListener('click', function() {
        mainAdminPanel.style.display = 'block';
        statsSection.style.display = 'none';
        navMainBtn.className = 'success-btn';
        navStatsBtn.className = '';
        navStatsBtn.style.backgroundColor = '#3498db';
        navStatsBtn.style.color = 'white';
        navMainBtn.style.backgroundColor = '';
        navMainBtn.style.color = '';
    });
    
    navStatsBtn.addEventListener('click', function() {
        mainAdminPanel.style.display = 'none';
        statsSection.style.display = 'block';
        navStatsBtn.className = 'success-btn';
        navMainBtn.className = '';
        navMainBtn.style.backgroundColor = '#ccc';
        navMainBtn.style.color = '#333';
        navStatsBtn.style.backgroundColor = '';
        navStatsBtn.style.color = '';
        loadStats();
    });
}

async function loadStats() {
    try {
        const response = await fetchWithAuth('/api/admin/stats');
        const data = await response.json();
        
        statsUsersContainer.innerHTML = '';
        if (data.users.length === 0) {
            statsUsersContainer.innerHTML = '<p>Aucune donnée disponible.</p>';
        } else {
            const maxScore = Math.max(...data.users.map(u => u.score), 100);
            data.users.forEach(user => {
                const percentage = Math.min((user.score / maxScore) * 100, 100);
                statsUsersContainer.innerHTML += `
                    <div style="margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                            <strong>${user.pseudo}</strong>
                            <span>${user.score} pts</span>
                        </div>
                        <div style="background-color: #ecf0f1; border-radius: 4px; height: 16px; width: 100%; overflow: hidden;">
                            <div style="background-color: #3498db; width: ${percentage}%; height: 100%; transition: width 0.5s ease-out;"></div>
                        </div>
                    </div>
                `;
            });
        }
        
        statsPhrasesContainer.innerHTML = '';
        if (data.phrases.length === 0) {
            statsPhrasesContainer.innerHTML = '<p>Aucune donnée disponible.</p>';
        } else {
            const maxCount = Math.max(...data.phrases.map(p => p.count), 5);
            data.phrases.forEach(item => {
                const percentage = Math.min((item.count / maxCount) * 100, 100);
                statsPhrasesContainer.innerHTML += `
                    <div style="margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 0.9em;">
                            <strong>${item.phrase}</strong>
                            <span>${item.count} fois</span>
                        </div>
                        <div style="background-color: #ecf0f1; border-radius: 4px; height: 16px; width: 100%; overflow: hidden;">
                            <div style="background-color: #2ecc71; width: ${percentage}%; height: 100%; transition: width 0.5s ease-out;"></div>
                        </div>
                    </div>
                `;
            });
        }
        
    } catch(err) {
        console.error("Erreur de chargement des stats:", err);
    }
}
