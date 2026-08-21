import re

# 1. Update index.html
with open('public/index.html', 'r') as f:
    html = f.read()

nav_old = '''<button id="nav-game-btn" class="nav-btn active" style="flex: 1;">Jeu</button>
                <button id="nav-stats-btn" class="nav-btn" style="flex: 1;">Statistiques</button>'''

nav_new = '''<button id="nav-game-btn" class="nav-btn active" style="flex: 1;">Jeu</button>
                <button id="nav-stats-btn" class="nav-btn" style="flex: 1;">Statistiques</button>
                <button id="nav-players-btn" class="nav-btn" style="flex: 1;">Joueurs</button>'''
html = html.replace(nav_old, nav_new)

players_section = '''
        <section id="players-section" class="hidden">
            <h2>Comptes Créés</h2>
            <p style="text-align: center; color: var(--text-muted);">Voici la liste de tous les joueurs inscrits au bingo :</p>
            <div id="all-players-list" style="display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; margin-top: 20px;">
                <!-- Les joueurs seront injectés ici -->
            </div>
        </section>
'''
html = html.replace('</main>', players_section + '\n    </main>')

with open('public/index.html', 'w') as f:
    f.write(html)


# 2. Update app.js
with open('public/app.js', 'r') as f:
    js = f.read()

nav_js = '''const navGameBtn = document.getElementById('nav-game-btn');
const navStatsBtn = document.getElementById('nav-stats-btn');
const gameSection = document.getElementById('game-section');
const statsSection = document.getElementById('stats-section');'''

nav_js_new = '''const navGameBtn = document.getElementById('nav-game-btn');
const navStatsBtn = document.getElementById('nav-stats-btn');
const navPlayersBtn = document.getElementById('nav-players-btn');
const gameSection = document.getElementById('game-section');
const statsSection = document.getElementById('stats-section');
const playersSection = document.getElementById('players-section');'''
js = js.replace(nav_js, nav_js_new)

nav_logic = '''navGameBtn.addEventListener('click', () => {
    gameSection.classList.remove('hidden');
    statsSection.classList.add('hidden');
    navGameBtn.classList.add('active');
    navStatsBtn.classList.remove('active');
});

navStatsBtn.addEventListener('click', () => {
    gameSection.classList.add('hidden');
    statsSection.classList.remove('hidden');
    navGameBtn.classList.remove('active');
    navStatsBtn.classList.add('active');
    loadUserStats();
});'''

nav_logic_new = '''navGameBtn.addEventListener('click', () => {
    gameSection.classList.remove('hidden');
    statsSection.classList.add('hidden');
    if (playersSection) playersSection.classList.add('hidden');
    navGameBtn.classList.add('active');
    navStatsBtn.classList.remove('active');
    if (navPlayersBtn) navPlayersBtn.classList.remove('active');
});

navStatsBtn.addEventListener('click', () => {
    gameSection.classList.add('hidden');
    statsSection.classList.remove('hidden');
    if (playersSection) playersSection.classList.add('hidden');
    navGameBtn.classList.remove('active');
    navStatsBtn.classList.add('active');
    if (navPlayersBtn) navPlayersBtn.classList.remove('active');
    loadUserStats();
});

if (navPlayersBtn) {
    navPlayersBtn.addEventListener('click', () => {
        gameSection.classList.add('hidden');
        statsSection.classList.add('hidden');
        playersSection.classList.remove('hidden');
        navGameBtn.classList.remove('active');
        navStatsBtn.classList.remove('active');
        navPlayersBtn.classList.add('active');
        loadAllPlayers();
    });
}

async function loadAllPlayers() {
    try {
        const res = await fetch('/api/users/all?t=' + Date.now());
        if (!res.ok) return;
        const users = await res.json();
        const container = document.getElementById('all-players-list');
        container.innerHTML = '';
        users.forEach(u => {
            const div = document.createElement('div');
            div.style = "background: var(--bg-secondary); padding: 10px 15px; border-radius: 20px; font-weight: bold; border: 1px solid rgba(255,255,255,0.1);";
            
            let pseudoDisplay = u.pseudo.replace(/J4X/gi, '<span class="j4x-highlight">$&</span>');
            if (u.pseudo.toLowerCase() === 'aminat0_') {
                div.classList.add('aminato-effect');
            }
            if (u.color) {
                div.style.color = u.color;
                div.style.textShadow = "1px 1px 2px rgba(0,0,0,0.3)";
            }
            
            div.innerHTML = pseudoDisplay;
            container.appendChild(div);
        });
    } catch (err) {
        console.error(err);
    }
}
'''
js = js.replace(nav_logic, nav_logic_new)

with open('public/app.js', 'w') as f:
    f.write(js)

# 3. Update server.py
with open('server.py', 'r') as f:
    server = f.read()

api_all = '''        if self.path == '/api/leaderboard':'''
api_all_new = '''        if self.path == '/api/users/all':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT pseudo, color FROM users ORDER BY pseudo COLLATE NOCASE ASC')
            all_users = [{'pseudo': row[0], 'color': row[1]} for row in c.fetchall()]
            conn.close()
            self.wfile.write(json.dumps(all_users).encode('utf-8'))
            return
            
        if self.path == '/api/leaderboard':'''
server = server.replace(api_all, api_all_new)

# Note: COLLATE NOCASE is sqlite specific. In Postgres we should use ORDER BY LOWER(pseudo) ASC.
# Let's fix that.
api_all_postgres_safe = '''        if self.path == '/api/users/all':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            conn = get_db_connection()
            c = conn.cursor()
            if IS_POSTGRES:
                c.execute('SELECT pseudo, color FROM users ORDER BY LOWER(pseudo) ASC')
            else:
                c.execute('SELECT pseudo, color FROM users ORDER BY pseudo COLLATE NOCASE ASC')
            all_users = [{'pseudo': row[0], 'color': row[1]} for row in c.fetchall()]
            conn.close()
            self.wfile.write(json.dumps(all_users).encode('utf-8'))
            return
            
        if self.path == '/api/leaderboard':'''
server = server.replace(api_all_new, api_all_postgres_safe)

with open('server.py', 'w') as f:
    f.write(server)
