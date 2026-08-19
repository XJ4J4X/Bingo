with open('public/admin.js', 'r') as f:
    content = f.read()

# 1. Tab Logic
tab_logic_old = """    navMainBtn.addEventListener('click', () => {
        document.getElementById('main-admin-panel').style.display = 'block';
        document.getElementById('stats-section').style.display = 'none';
        navMainBtn.style.backgroundColor = '#2ecc71';
        navStatsBtn.style.backgroundColor = '#3498db';
    });

    navStatsBtn.addEventListener('click', () => {
        document.getElementById('main-admin-panel').style.display = 'none';
        document.getElementById('stats-section').style.display = 'block';
        navStatsBtn.style.backgroundColor = '#2ecc71';
        navMainBtn.style.backgroundColor = '#3498db';
        fetchStats();
    });"""

tab_logic_new = """    const navAccountsBtn = document.getElementById('nav-accounts-btn');
    
    function resetNavBtns() {
        navMainBtn.style.backgroundColor = '#3498db';
        navStatsBtn.style.backgroundColor = '#3498db';
        if (navAccountsBtn) navAccountsBtn.style.backgroundColor = '#3498db';
        
        document.getElementById('main-admin-panel').style.display = 'none';
        document.getElementById('stats-section').style.display = 'none';
        document.getElementById('accounts-section').style.display = 'none';
    }

    navMainBtn.addEventListener('click', () => {
        resetNavBtns();
        document.getElementById('main-admin-panel').style.display = 'block';
        navMainBtn.style.backgroundColor = '#2ecc71';
    });

    navStatsBtn.addEventListener('click', () => {
        resetNavBtns();
        document.getElementById('stats-section').style.display = 'block';
        navStatsBtn.style.backgroundColor = '#2ecc71';
        fetchStats();
    });
    
    if (navAccountsBtn) {
        navAccountsBtn.addEventListener('click', () => {
            resetNavBtns();
            document.getElementById('accounts-section').style.display = 'block';
            navAccountsBtn.style.backgroundColor = '#2ecc71';
        });
    }"""
content = content.replace(tab_logic_old, tab_logic_new)

# 2. Add color button to users table
users_render_old = """                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${user.id}</td>
                    <td>${user.pseudo}</td>
                    <td>${user.password_words}</td>
                    <td><strong>${user.score}</strong></td>
                    <td>
                        <button class="small-btn warning-btn" onclick="addScore(${user.id}, -1)">-1</button>
                        <button class="small-btn success-btn" onclick="addScore(${user.id}, 1)">+1</button>
                    </td>
                    <td><button class="small-btn danger-btn" onclick="deleteUser(${user.id})">Supprimer</button></td>
                `;
                usersTableBody.appendChild(tr);"""
users_render_new = """                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${user.id}</td>
                    <td>${user.pseudo}</td>
                    <td>${user.password_words}</td>
                    <td><strong>${user.score}</strong></td>
                    <td>
                        <button class="small-btn warning-btn" onclick="addScore(${user.id}, -1)">-1</button>
                        <button class="small-btn success-btn" onclick="addScore(${user.id}, 1)">+1</button>
                    </td>
                    <td>
                        <button class="small-btn" style="background:#9b59b6; color:white; border:none; cursor:pointer;" onclick="grantColorChoice(${user.id})" title="Donner la roue de couleur">🎨</button>
                        <button class="small-btn danger-btn" onclick="deleteUser(${user.id})">Supprimer</button>
                    </td>
                `;
                usersTableBody.appendChild(tr);"""
content = content.replace(users_render_old, users_render_new)

# 3. Add grantColorChoice function to global scope
grant_func = """
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
"""
content = content + grant_func

with open('public/admin.js', 'w') as f:
    f.write(content)
