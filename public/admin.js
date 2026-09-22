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
const timerLockDurationInput = document.getElementById('timer-lock-duration');
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
            adminContent.style.display = 'flex'; adminContent.classList.remove('hidden');
            if(adminInfo) adminInfo.classList.remove('hidden');
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

async function initAdmin() {

    const hour = new Date().getHours();
    let greeting = 'Bonjour';
    if (hour >= 5 && hour < 12) greeting = 'Bon matin';
    else if (hour >= 12 && hour < 18) greeting = 'Bonjour';
    else if (hour >= 18 && hour < 22) greeting = 'Bonsoir';
    else greeting = 'Bon stream';
    
    const roleName = adminRole === 'superadmin' ? 'Boss' : 'Admin';
    const greetingEl = document.getElementById('admin-greeting');
    if (greetingEl) {
        greetingEl.textContent = `${greeting}, ${roleName} 👑 👻`;
    }

    await loadCustomFonts();
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
        adminContent.style.display = 'flex'; adminContent.classList.remove('hidden');
        if(adminInfo) adminInfo.classList.remove('hidden');
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
        
        const toggleRulesBtn = document.getElementById('toggle-rules-btn');
        if (toggleRulesBtn && data.rules_enabled !== undefined) {
            toggleRulesBtn.textContent = data.rules_enabled ? 'Désactiver Règlement: ON' : 'Activer Règlement: OFF';
            if(data.rules_enabled) {
                toggleRulesBtn.classList.remove('warning-btn');
                toggleRulesBtn.classList.add('success-btn');
            } else {
                toggleRulesBtn.classList.remove('success-btn');
                toggleRulesBtn.classList.add('warning-btn');
            }
        }
        
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
            const lcs = document.getElementById('live-control-section'); if(lcs) { lcs.style.display = 'block'; lcs.classList.remove('hidden'); }
            loadLiveData();
        } else {
            gameStatus.textContent = "Hors ligne";
            gameStatus.style.color = "red";
            timerDisplay.textContent = "00:00";
            const lcs2 = document.getElementById('live-control-section'); if(lcs2) { lcs2.style.display = 'none'; lcs2.classList.add('hidden'); }
            document.getElementById('stop-game-btn').textContent = "Arrêter le Live";
            document.getElementById('stop-game-btn').className = "danger-btn";
        }
    } catch (err) {
        console.error("Erreur sync timer", err);
    }
}

async function loadLiveData() {
    try {
        const res = await fetchWithAuth('/api/admin/game/live_data');
        if (!res.ok) return;
        const data = await res.json();
        
        const grid = (document.getElementById('admin-live-grid')||{});
        
        // If empty, create the grid cells
        if (grid.children.length === 0) {
            data.active_phrases.forEach(phrase => {
                const cell = document.createElement('div');
                cell.className = 'bingo-cell';
                cell.id = 'chk-' + btoa(unescape(encodeURIComponent(phrase))).replace(/=/g, '');
                
                const highlighted = phrase;
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


if(startGameBtn) startGameBtn.addEventListener('click', async () => {
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

if(stopGameBtn) stopGameBtn.addEventListener('click', async () => {
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
            tr.style.borderBottom = "1px solid #eee";
            
            const fontClass = u.font_family || '';
            let pseudoClass = fontClass;
            if (u.pseudo.toLowerCase() === 'aminat0_') {
                pseudoClass += ' aminato-effect';
            }
            
            tr.innerHTML = `
                <td style="padding: 10px;">
                    <strong class="font-preview ${pseudoClass}" id="font-preview-${u.id}" style="font-size:1.2em;">${u.pseudo}</strong>
                </td>
                <td style="padding: 10px; color: #7f8c8d;"><code>${u.password}</code></td>
                <td style="padding: 10px; font-weight: bold; font-size:1.1em;">${u.score}</td>
                <td style="padding: 10px;">
                    <select class="font-select" data-id="${u.id}" style="padding: 5px; border-radius: 4px; border: 1px solid #ccc; background:#fff;">
                        <option value="" ${fontClass === '' ? 'selected' : ''}>Standard</option>
                        <option value="font-bangers" ${fontClass === 'font-bangers' ? 'selected' : ''}>Bangers (Fun)</option>
                        <option value="font-pixel" ${fontClass === 'font-pixel' ? 'selected' : ''}>Pixel (Rétro)</option>
                        <option value="font-pacifico" ${fontClass === 'font-pacifico' ? 'selected' : ''}>Pacifico (Élégant)</option>
                        <option value="font-creepster" ${fontClass === 'font-creepster' ? 'selected' : ''}>Creepster (Spooky)</option>
                        <option value="font-orbitron" ${fontClass === 'font-orbitron' ? 'selected' : ''}>Orbitron (Néon)</option>
                        ${customFonts.map(f => {
                            const name = f.split('.')[0];
                            const cName = 'font-custom-' + name;
                            return `<option value="${cName}" ${fontClass === cName ? 'selected' : ''}>${name} (Perso)</option>`;
                        }).join('')}
                    </select>
                </td>
                <td style="padding: 10px; white-space: nowrap;">
                    <button class="small-btn add-pts-btn success-btn" data-id="${u.id}" style="padding:4px 8px;">+10</button>
                    <button class="small-btn sub-pts-btn warning-btn" data-id="${u.id}" style="padding:4px 8px;">-10</button>
                </td>
                <td style="padding: 10px;">
                    <button class="small-btn grant-color-btn" style="background:#9b59b6; color:white; border:none; cursor:pointer; padding:4px 8px;" data-id="${u.id}" title="Donner la couleur">🎨</button>
                    <button class="small-btn delete-btn danger-btn" data-id="${u.id}" style="padding:4px 8px;">🗑️</button>
                </td>
            `;
            usersTableBody.appendChild(tr);
        });
        
        // Add listeners for font select
        document.querySelectorAll('.font-select').forEach(select => {
            select.addEventListener('change', (e) => {
                const id = e.target.getAttribute('data-id');
                const fontClass = e.target.value;
                const preview = document.getElementById(`font-preview-${id}`);
                // Keep aminato effect if it's there
                let finalClass = `font-preview ${fontClass}`;
                if (preview.classList.contains('aminato-effect')) {
                    finalClass += ' aminato-effect';
                }
                preview.className = finalClass;
                updateUserFont(id, fontClass);
            });
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
        
        document.querySelectorAll('.grant-color-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                if (confirm("Voulez-vous donner l'accès à la roue de couleur à ce joueur ?")) {
                    const id = e.target.getAttribute('data-id');
                    const res = await fetchWithAuth('/api/admin/game/grant_color', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ user_id: id })
                    });
                    if (res.ok) alert("Accès donné avec succès !");
                    else alert("Erreur");
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

if(resetScoresBtn) resetScoresBtn.addEventListener('click', async () => {
    if (confirm('Remettre tous les scores à 0 pour le prochain Live ?')) {
        await fetchWithAuth('/api/admin/users/reset', { method: 'POST' });
        loadUsers();
    }
});

if(createUserBtn) createUserBtn.addEventListener('click', async () => {
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

if(addPhraseBtn) addPhraseBtn.addEventListener('click', async () => {
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

if(createAdminBtn) createAdminBtn.addEventListener('click', async () => {
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

let editingProfileId = null;

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
                <td>
                    <button class="small-btn edit-profile-btn" data-id="${p.id}" style="background-color: #f39c12; color: white;">Éditer</button>
                    <button class="small-btn danger-btn delete-profile-btn" data-id="${p.id}">Supprimer</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
        
        document.querySelectorAll('.edit-profile-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = e.target.getAttribute('data-id');
                const profile = profiles.find(pr => pr.id == id);
                if (profile) {
                    editingProfileId = id;
                    document.getElementById('new-profile-name').value = profile.name;
                    document.getElementById('new-profile-phrases').value = profile.phrases;
                    document.getElementById('add-profile-btn').textContent = 'Mettre à jour Profil';
                    document.getElementById('cancel-edit-profile-btn').style.display = 'block';
                    document.getElementById('new-profile-name').scrollIntoView({behavior: 'smooth', block: 'center'});
                }
            });
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
const cancelEditProfileBtn = document.getElementById('cancel-edit-profile-btn');

function resetProfileForm() {
    editingProfileId = null;
    document.getElementById('new-profile-name').value = '';
    document.getElementById('new-profile-phrases').value = '';
    document.getElementById('add-profile-btn').textContent = 'Sauvegarder Profil';
    cancelEditProfileBtn.style.display = 'none';
    document.getElementById('csv-upload').value = '';
}

if (cancelEditProfileBtn) {
    cancelEditProfileBtn.addEventListener('click', resetProfileForm);
}

if (addProfileBtn) {
    addProfileBtn.addEventListener('click', async () => {
        const name = document.getElementById('new-profile-name').value.trim();
        const text = document.getElementById('new-profile-phrases').value.trim();
        if (name && text) {
            const url = editingProfileId ? '/api/admin/profiles/update' : '/api/admin/profiles/add';
            const payload = { name: name, phrases_text: text };
            if (editingProfileId) {
                payload.id = editingProfileId;
            }
            
            try {
                const res = await fetchWithAuth(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                if (res.ok) {
                    resetProfileForm();
                    loadProfiles();
                    alert("Profil sauvegardé avec succès !");
                } else {
                    alert("Erreur lors de la sauvegarde (nom déjà pris ?)");
                }
            } catch (err) {
                alert("Erreur réseau: " + err);
            }
        } else {
            alert("⚠️ Veuillez entrer un nom de profil ET coller au moins une phrase.");
        }
    });
}

let pendingBulkProfiles = [];

const csvUpload = document.getElementById('csv-upload');
if (csvUpload) {
    csvUpload.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = function(evt) {
            const content = evt.target.result;
            let separator = content.includes(';') ? ';' : ',';
            
            // Parse lines
            const lines = content.split(/\r?\n/).map(l => l.trim()).filter(l => l.length > 0);
            
            if (lines.length === 0) {
                alert("⚠️ Le fichier CSV est vide.");
                return;
            }
            
            pendingBulkProfiles = [];
            
            // Extract profiles row by row
            // Each row: ProfileName, Phrase1, Phrase2, ... Phrase16
            for (let i = 0; i < lines.length; i++) {
                const cols = lines[i].split(separator).map(c => {
                    let text = c.trim();
                    if (text.startsWith('"') && text.endsWith('"')) text = text.substring(1, text.length - 1);
                    return text;
                });
                
                if (cols.length > 1) {
                    const name = cols[0];
                    const phrases = cols.slice(1).filter(p => p.length > 0);
                    if (name && phrases.length > 0) {
                        pendingBulkProfiles.push({ name: name, phrases: phrases });
                    }
                }
            }
            
            if (pendingBulkProfiles.length === 0) {
                alert("⚠️ Aucun profil valide trouvé dans le CSV. Chaque ligne doit contenir : Nom du Profil, Phrase 1, Phrase 2...");
                return;
            }
            
            // Show preview
            const previewContainer = document.getElementById('csv-preview-content');
            previewContainer.innerHTML = '';
            
            pendingBulkProfiles.forEach(p => {
                const box = document.createElement('div');
                box.style.border = '1px solid #3498db';
                box.style.borderRadius = '5px';
                box.style.padding = '10px';
                box.style.flex = '1 1 200px';
                box.style.minWidth = '200px';
                box.style.background = '#f7f9fc';
                
                let html = `<h4 style="margin-top:0; color:#2980b9;">${p.name} <span style="font-size:0.8em; color:#7f8c8d;">(${p.phrases.length} phrases)</span></h4>`;
                html += `<ul style="margin:0; padding-left:20px; font-size:0.85em; max-height:150px; overflow-y:auto;">`;
                p.phrases.forEach(phrase => {
                    html += `<li>${phrase}</li>`;
                });
                html += `</ul>`;
                
                box.innerHTML = html;
                previewContainer.appendChild(box);
            });
            
            const modal = document.getElementById('csv-preview-modal');
            modal.style.display = 'flex';
            modal.classList.remove('hidden');
        };
        reader.onerror = function() {
            alert("⚠️ Impossible de lire le fichier.");
        };
        reader.readAsText(file);
    });
}

document.getElementById('csv-cancel-btn')?.addEventListener('click', () => {
    document.getElementById('csv-preview-modal').style.display = 'none';
    document.getElementById('csv-preview-modal').classList.add('hidden');
    if (csvUpload) csvUpload.value = '';
});

document.getElementById('csv-confirm-btn')?.addEventListener('click', async () => {
    const btn = document.getElementById('csv-confirm-btn');
    btn.textContent = "Importation...";
    btn.disabled = true;
    
    let successCount = 0;
    
    for (const profile of pendingBulkProfiles) {
        try {
            const res = await fetchWithAuth('/api/admin/profiles/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: profile.name, phrases_text: profile.phrases.join('\n') })
            });
            if (res.ok) successCount++;
        } catch (e) {
            console.error("Erreur ajout profil", profile.name, e);
        }
    }
    
    document.getElementById('csv-preview-modal').style.display = 'none';
    document.getElementById('csv-preview-modal').classList.add('hidden');
    if (csvUpload) csvUpload.value = '';
    
    btn.textContent = "Confirmer et Importer";
    btn.disabled = false;
    
    alert(`✅ Importation terminée ! ${successCount} profil(s) ajouté(s).`);
    loadProfiles();
});

const backupBtn = document.getElementById('backup-btn');
if (backupBtn) {
    backupBtn.addEventListener('click', async () => {
        try {
            const res = await fetchWithAuth('/api/admin/backup');
            if (!res.ok) {
                alert("Erreur lors de la sauvegarde.");
                return;
            }
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `bingo_sauvegarde_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        } catch (e) {
            console.error("Backup failed", e);
            alert("Erreur lors du téléchargement.");
        }
    });
}



// --- TABS LOGIC ---
const navMainBtn = document.getElementById('nav-main-btn');
const navStatsBtn = document.getElementById('nav-stats-btn');
const navAccountsBtn = document.getElementById('nav-accounts-btn');
const navRulesBtn = document.getElementById('nav-rules-btn');
const mainAdminPanel = document.getElementById('main-admin-panel');
const statsSection = document.getElementById('stats-section');
const accountsSection = document.getElementById('accounts-section');
const rulesSection = document.getElementById('rules-section');
const statsUsersContainer = document.getElementById('stats-users-container');
const statsPhrasesContainer = document.getElementById('stats-phrases-container');

function resetNavBtns() {
    navMainBtn.style.backgroundColor = '#3498db';
    navMainBtn.style.color = 'white';
    navMainBtn.className = '';
    
    navStatsBtn.style.backgroundColor = '#3498db';
    navStatsBtn.style.color = 'white';
    navStatsBtn.className = '';
    
    if (navAccountsBtn) {
        navAccountsBtn.style.backgroundColor = '#3498db';
        navAccountsBtn.style.color = 'white';
        navAccountsBtn.className = '';
    }
    if (navRulesBtn) {
        navRulesBtn.style.backgroundColor = '#3498db';
        navRulesBtn.style.color = 'white';
        navRulesBtn.className = '';
    }
    
    mainAdminPanel.style.display = 'none';
    statsSection.style.display = 'none';
    if (accountsSection) accountsSection.style.display = 'none';
    if (rulesSection) rulesSection.style.display = 'none';
}

if (navMainBtn && navStatsBtn) {
    navMainBtn.addEventListener('click', function() {
        resetNavBtns();
        mainAdminPanel.style.display = 'block';
        navMainBtn.className = 'success-btn';
        navMainBtn.style.backgroundColor = '';
        navMainBtn.style.color = '';
    });
    
    navStatsBtn.addEventListener('click', function() {
        resetNavBtns();
        statsSection.style.display = 'block';
        navStatsBtn.className = 'success-btn';
        navStatsBtn.style.backgroundColor = '';
        navStatsBtn.style.color = '';
        loadStats();
    });
    
    if (navAccountsBtn) {
        navAccountsBtn.addEventListener('click', function() {
            resetNavBtns();
            if (accountsSection) accountsSection.style.display = 'block';
            navAccountsBtn.className = 'success-btn';
            navAccountsBtn.style.backgroundColor = '';
            navAccountsBtn.style.color = '';
        });
    }

    if (navRulesBtn) {
        navRulesBtn.addEventListener('click', function() {
            resetNavBtns();
            if (rulesSection) rulesSection.style.display = 'block';
            navRulesBtn.className = 'success-btn';
            navRulesBtn.style.backgroundColor = '';
            navRulesBtn.style.color = '';
        });
    }
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

window.grantColorChoice = async function(userId) {
    if(!confirm("Voulez-vous donner l'accès à la roue de couleur à ce joueur ?")) return;
    try {
        const res = await fetch('/api/admin/game/grant_color', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${adminToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ user_id: userId })
        });
        if (res.ok) {
            alert("Accès donné avec succès !");
        } else {
            alert("Erreur");
        }
    } catch (e) {
        console.error(e);
    }
}

document.getElementById('toggle-rules-btn')?.addEventListener('click', async () => {
    const btn = document.getElementById('toggle-rules-btn');
    const isCurrentlyOn = btn.textContent.includes('ON');
    try {
        const res = await fetchWithAuth('/api/admin/rules/toggle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled: !isCurrentlyOn })
        });
        if (res.ok) {
            const data = await res.json();
            btn.textContent = data.rules_enabled ? 'Désactiver Règlement: ON' : 'Activer Règlement: OFF';
            if(data.rules_enabled) {
                btn.classList.remove('warning-btn');
                btn.classList.add('success-btn');
            } else {
                btn.classList.remove('success-btn');
                btn.classList.add('warning-btn');
            }
            syncGameState();
        }
    } catch(e) { console.error(e); }
});

document.getElementById('reset-rules-btn')?.addEventListener('click', async () => {
    if(!confirm("Êtes-vous sûr de vouloir remettre à zéro toutes les validations du règlement ? Tous les joueurs devront le relire.")) return;
    try {
        const res = await fetchWithAuth('/api/admin/rules/reset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        if(res.ok) {
            alert("Règlement réinitialisé pour tous les joueurs !");
            loadUsers();
        }
    } catch(e) { console.error(e); }
});


// Gestion de la navigation latérale (Dashboard)
document.querySelectorAll('.admin-nav-item').forEach(item => {
    item.addEventListener('click', () => {
        document.querySelectorAll('.admin-nav-item').forEach(nav => nav.classList.remove('active'));
        item.classList.add('active');
        
        document.querySelectorAll('.admin-section').forEach(sec => sec.classList.remove('active'));
        const target = item.getAttribute('data-target');
        const targetEl = document.getElementById(target);
        if(targetEl) targetEl.classList.add('active');
        
        if(target === 'users') {
            loadUsers();
        } else if(target === 'profiles') {
            loadProfiles();
        } else if(target === 'stats') {
            loadStats();
        } else if(target === 'settings') {
            loadAdmins();
        }
    });
});

async function updateUserFont(userId, font_family) {
    try {
        const res = await fetch('/api/admin/user/font', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': adminToken },
            body: JSON.stringify({ user_id: userId, font_family: font_family })
        });
        if (!res.ok) {
            alert('Erreur lors de la sauvegarde de la police');
        }
    } catch (err) {
        console.error(err);
    }
}

window.changeUserFont = function(userId, fontClass) {
    const preview = document.getElementById(`font-preview-${userId}`);
    preview.className = `font-preview ${fontClass}`;
    updateUserFont(userId, fontClass);
};

// GESTION UPLOAD ET CHARGEMENT POLICES PERSONNALISÉES
let customFonts = [];

async function loadCustomFonts() {
    try {
        const res = await fetch('/api/fonts');
        if (res.ok) {
            const data = await res.json();
            customFonts = data.fonts;
            
            // Inject CSS
            let style = document.getElementById('custom-fonts-style');
            if (!style) {
                style = document.createElement('style');
                style.id = 'custom-fonts-style';
                document.head.appendChild(style);
            }
            let css = '';
            customFonts.forEach(f => {
                const name = f.split('.')[0];
                const fontClass = 'font-custom-' + name;
                css += `@font-face { font-family: '${name}'; src: url('fonts/${f}'); }
`;
                css += `.${fontClass} { font-family: '${name}', sans-serif; }
`;
            });
            style.innerHTML = css;
        }
    } catch (e) { console.error(e); }
}

document.getElementById('upload-font-btn')?.addEventListener('click', async () => {
    const fileInput = document.getElementById('font-upload-input');
    const status = document.getElementById('font-upload-status');
    if (!fileInput.files.length) {
        status.textContent = 'Veuillez sélectionner un fichier.';
        status.style.color = 'red';
        return;
    }
    
    const formData = new FormData();
    formData.append('font_file', fileInput.files[0]);
    
    status.textContent = 'Envoi en cours...';
    status.style.color = 'orange';
    
    try {
        const res = await fetch('/api/admin/fonts/upload', {
            method: 'POST',
            headers: { 'Authorization': adminToken },
            body: formData
        });
        
        if (res.ok) {
            const data = await res.json();
            status.textContent = `Succès ! Polices ajoutées : ${data.saved.join(', ')}`;
            status.style.color = 'green';
            fileInput.value = '';
            
            // Reload fonts
            await loadCustomFonts();
            // Re-render users to update selects
            if (document.getElementById('users').classList.contains('active')) {
                loadUsers();
            }
        } else {
            status.textContent = "Erreur lors de l'upload.";
            status.style.color = 'red';
        }
    } catch (e) {
        status.textContent = 'Erreur serveur.';
        status.style.color = 'red';
    }
});

// Appel initial
loadCustomFonts();

// Admin Theme toggle logic
document.addEventListener('DOMContentLoaded', () => {
    const themeBtn = document.getElementById('admin-theme-toggle');
    const currentTheme = localStorage.getItem('admin_theme');
    if (currentTheme === 'dark') {
        document.body.classList.add('admin-dark-mode');
        if (themeBtn) themeBtn.textContent = '☀️ Mode Clair';
    }
    
    if (themeBtn) {
        themeBtn.addEventListener('click', () => {
            document.body.classList.toggle('admin-dark-mode');
            if (document.body.classList.contains('admin-dark-mode')) {
                localStorage.setItem('admin_theme', 'dark');
                themeBtn.textContent = '☀️ Mode Clair';
            } else {
                localStorage.setItem('admin_theme', 'light');
                themeBtn.textContent = '🌙 Mode Sombre';
            }
        });
    }
});
