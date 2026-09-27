# Aminato si tu lis cette phrase j'ai galerer mdr -- J4X
import http.server
import socketserver
import json
import sqlite3
import random
import os
import urllib.parse


try:
    import psycopg
except ImportError as e:
    psycopg = None
    print('DEBUG IMPORT ERROR:', e)

DATABASE_URL = os.environ.get("DATABASE_URL")
IS_POSTGRES = DATABASE_URL and DATABASE_URL.startswith("postgres")

def get_db_connection():
    if IS_POSTGRES:
        if not psycopg:
            raise RuntimeError("psycopg is not installed but DATABASE_URL is set.")
        conn = psycopg.connect(DATABASE_URL)
        original_cursor = conn.cursor
        class CursorWrapper:
            def __init__(self, cursor):
                self._cursor = cursor
            def execute(self, query, params=()):
                q = query.replace('?', '%s').replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
                return self._cursor.execute(q, params)
            def __getattr__(self, name):
                return getattr(self._cursor, name)
                
        def patched_cursor(*args, **kwargs):
            return CursorWrapper(original_cursor(*args, **kwargs))
        conn.cursor = patched_cursor
        return conn
    return sqlite3.connect(DB_FILE)

DBIntegrityError = psycopg.IntegrityError if IS_POSTGRES and psycopg else sqlite3.IntegrityError
import time

PORT = int(os.environ.get('PORT', 8080))
DB_FILE = 'database.sqlite'

WORDS = ["fantome", "esprit", "spectre", "vampire", "zombie", "manoir", "tombe", "squelette", "monstre", "loup-garou",
         "citrouille", "sorciere", "chaudron", "cimetiere", "chauve-souris", "demon", "cauchemar", "ombre", "tenebres",
         "pomme", "chaise", "nuage", "soleil", "lune", "ordinateur", "bouteille", "clavier", "souris", "fenetre",
         "table", "livre", "stylo", "papier", "voiture", "maison", "arbre", "fleur", "chat", "chien", "oiseau", "poisson",
         "mer", "montagne", "riviere", "route", "chemin", "pont", "porte", "mur", "toit", "ciel", "terre"]

DEFAULT_PHRASES = [
    "Aminato crie fort", "Aminato rage sur un jeu", "Aminato boit de l'eau", "Aminato lit un don",
    "Aminato rigole à une blague nulle", "Aminato lance une pub", "Aminato dit 'Let's go !'", "Aminato parle de nourriture",
    "Aminato ban quelqu'un du chat", "Aminato met une musique hype", "Aminato fail lamentablement", "Aminato fait une win",
    "Aminato remercie un sub", "Aminato regarde son téléphone", "Aminato bug (connexion)", "Aminato dit 'Incroyable'"
]

game_state = {
    "is_active": False,
    "is_locked": False,
    "is_test": False,
    "start_time": None,
    "duration": 600,
    "lock_duration": 0,
    "lock_start_time": None,
    "verification_mode": "strict",
    "active_phrases": [],
    "admin_ticked": [],
    "color_choice_user_pseudo": None,
    "rules_enabled": False,
    "submissions_count": 0,
    "late_session": {
        "is_active": False,
        "start_time": None,
        "duration": 300
    }
}

_leaderboard_cache = {"data": None, "timestamp": 0}
_users_all_cache = {"data": None, "timestamp": 0}

def init_db():
    global game_state
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pseudo TEXT UNIQUE,
            password_words TEXT,
            score INTEGER DEFAULT 0,
            submitted_grid TEXT,
            color TEXT,
            wins INTEGER DEFAULT 0,
            lives_participated INTEGER DEFAULT 0,
            boxes_checked INTEGER DEFAULT 0,
            boxes_correct INTEGER DEFAULT 0,
            score_live INTEGER DEFAULT 0
        )
    ''')
    
    if IS_POSTGRES:
        c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users'")
        columns = [col[0] for col in c.fetchall()]
    else:
        c.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in c.fetchall()]
        
    if 'submitted_grid' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN submitted_grid TEXT")
    if 'color' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN color TEXT")
    if 'wins' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN wins INTEGER DEFAULT 0")
    if 'lives_participated' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN lives_participated INTEGER DEFAULT 0")
    if 'boxes_checked' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN boxes_checked INTEGER DEFAULT 0")
    if 'boxes_correct' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN boxes_correct INTEGER DEFAULT 0")
    if 'score_live' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN score_live INTEGER DEFAULT 0")
    if 'has_accepted_rules' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN has_accepted_rules INTEGER DEFAULT 0")
    if 'current_streak' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN current_streak INTEGER DEFAULT 0")
    if 'max_streak' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN max_streak INTEGER DEFAULT 0")
    if 'font_family' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN font_family TEXT DEFAULT ''")
    if 'last_live_id' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN last_live_id INTEGER DEFAULT 0")
    if 'is_late' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN is_late INTEGER DEFAULT 0")
    if 'submitted_at' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN submitted_at REAL DEFAULT 0")

    c.execute('''
        CREATE TABLE IF NOT EXISTS lives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('SELECT MAX(id) FROM lives')
    max_live = c.fetchone()[0]
    game_state['current_live_id'] = max_live if max_live else 0

    c.execute('''
        CREATE TABLE IF NOT EXISTS phrases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phrase TEXT UNIQUE
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            password TEXT UNIQUE,
            role TEXT DEFAULT 'admin'
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            phrases_text TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS phrase_stats (
            phrase TEXT PRIMARY KEY,
            count INTEGER DEFAULT 0
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS live_participations (
            user_id INTEGER,
            live_id INTEGER,
            PRIMARY KEY (user_id, live_id)
        )
    ''')
    try:
        c.execute('SELECT id, last_live_id FROM users WHERE last_live_id > 0')
        for uid, lid in c.fetchall():
            c.execute('SELECT 1 FROM live_participations WHERE user_id = ? AND live_id = ?', (uid, lid))
            if not c.fetchone():
                c.execute('INSERT INTO live_participations (user_id, live_id) VALUES (?, ?)', (uid, lid))
    except Exception:
        pass
    
    c.execute('SELECT COUNT(*) FROM phrases')
    if c.fetchone()[0] == 0:
        for phrase in DEFAULT_PHRASES:
            c.execute('INSERT INTO phrases (phrase) VALUES (?)', (phrase,))
            
    c.execute('SELECT COUNT(*) FROM admins')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO admins (password, role) VALUES (?, ?)', ("Xz7!Kj9$Lm2@Qw1", "superadmin"))
        c.execute('INSERT INTO admins (password, role) VALUES (?, ?)', ("Admin$1Bng", "admin"))
        c.execute('INSERT INTO admins (password, role) VALUES (?, ?)', ("Aminato2!Live", "admin"))
        c.execute('INSERT INTO admins (password, role) VALUES (?, ?)', ("Bingo#Mod3", "admin"))
    conn.commit()
    conn.close()

def check_admin(headers):
    auth_header = headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    provided_password = auth_header.split("Bearer ")[1]
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT id, role FROM admins WHERE password = ?', (provided_password,))
    admin = c.fetchone()
    conn.close()
    
    if admin:
        return {'id': admin[0], 'role': admin[1]}
    return None

def get_eff_streak_checker(c):
    is_active = game_state.get('is_active', False) and not game_state.get('is_test', False)
    try:
        c.execute('SELECT DISTINCT live_id FROM live_participations ORDER BY live_id DESC LIMIT 2')
        recent_lives = [r[0] for r in c.fetchall()]
    except Exception:
        recent_lives = []

    def eff_streak(streak, last_live):
        if not streak or not last_live:
            return 0
        if not recent_lives:
            return streak
        if is_active:
            if last_live in recent_lives:
                return streak
        else:
            if last_live >= recent_lives[0]:
                return streak
        return 0

    return eff_streak

class MyRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="public", **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        super().end_headers()

    def do_GET(self):
        url_path = self.path.split('?')[0]
        
        if url_path == '/roue' or url_path == '/roue/' or url_path == '/roue.html':
            try:
                with open('public/roue.html', 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                self.send_error(404, "File not found")
            return
            
        if url_path == '/roue.css' or url_path == '/roue.js':
            try:
                with open(f'public{url_path}', 'rb') as f:
                    content = f.read()
                self.send_response(200)
                if url_path.endswith('.css'):
                    self.send_header('Content-type', 'text/css; charset=utf-8')
                else:
                    self.send_header('Content-type', 'application/javascript; charset=utf-8')
                self.end_headers()
                self.wfile.write(content)
            except Exception:
                self.send_error(404, "File not found")
            return

        if url_path in ('/obs', '/obs/', '/obs.html'):
            try:
                with open('public/obs.html', 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(content)
            except Exception:
                self.send_error(404, "File not found")
            return

        if url_path in ('/validations', '/validations/', '/validations.html', '/dock', '/dock/'):
            try:
                with open('public/validations.html', 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(content)
            except Exception:
                self.send_error(404, "File not found")
            return
            
        if url_path == '/api/users/all':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            now = time.time()
            if _users_all_cache["data"] and (now - _users_all_cache["timestamp"] < 20):
                self.wfile.write(_users_all_cache["data"])
                return
            conn = get_db_connection()
            c = conn.cursor()
            eff_streak = get_eff_streak_checker(c)
            c.execute('SELECT pseudo, color, wins, score, current_streak, max_streak, font_family, last_live_id FROM users ORDER BY LOWER(pseudo) ASC')
            all_users = [{
                'pseudo': row[0],
                'color': row[1],
                'wins': row[2] or 0,
                'score': row[3] or 0,
                'streak': eff_streak(row[4] or 0, row[7] or 0),
                'max_streak': row[5] or 0,
                'font_family': row[6] or ''
            } for row in c.fetchall()]
            conn.close()
            resp = json.dumps(all_users).encode('utf-8')
            _users_all_cache["data"] = resp
            _users_all_cache["timestamp"] = now
            self.wfile.write(resp)
            return
            
        if url_path == '/api/leaderboard':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            now = time.time()
            if _leaderboard_cache["data"] and (now - _leaderboard_cache["timestamp"] < 15):
                self.wfile.write(_leaderboard_cache["data"])
                return

            conn = get_db_connection()
            c = conn.cursor()
            eff_streak = get_eff_streak_checker(c)
            c.execute('SELECT pseudo, score, color, current_streak, font_family, last_live_id FROM users ORDER BY score DESC LIMIT 50')
            top_score = [{'pseudo': row[0], 'score': row[1], 'color': row[2], 'streak': eff_streak(row[3], row[5]), 'font_family': row[4]} for row in c.fetchall()]
            
            c.execute('SELECT pseudo, wins, color, current_streak, font_family, last_live_id FROM users ORDER BY wins DESC LIMIT 50')
            top_wins = [{'pseudo': row[0], 'wins': row[1], 'color': row[2], 'streak': eff_streak(row[3], row[5]), 'font_family': row[4]} for row in c.fetchall()]
            
            c.execute('SELECT pseudo, score_live, color, current_streak, font_family, last_live_id FROM users WHERE score_live > 0 ORDER BY score_live DESC LIMIT 50')
            top_live = [{'pseudo': row[0], 'score_live': row[1], 'color': row[2], 'streak': eff_streak(row[3], row[5]), 'font_family': row[4]} for row in c.fetchall()]
            
            c.execute('SELECT pseudo, max_streak, color, current_streak, font_family, last_live_id FROM users WHERE max_streak > 0 ORDER BY max_streak DESC LIMIT 50')
            top_streaks = [{'pseudo': row[0], 'max_streak': row[1], 'color': row[2], 'streak': eff_streak(row[3], row[5]), 'font_family': row[4]} for row in c.fetchall()]
            
            conn.close()
            resp = json.dumps({"top_score": top_score, "top_wins": top_wins, "top_live": top_live, "top_streaks": top_streaks}).encode('utf-8')
            _leaderboard_cache["data"] = resp
            _leaderboard_cache["timestamp"] = now
            self.wfile.write(resp)
            
        elif url_path == '/api/user_stats':
            pseudo = urllib.parse.unquote(self.headers.get('pseudo', '').strip())
            password = urllib.parse.unquote(self.headers.get('password', '').strip())
            if not pseudo or not password:
                self.send_error(401)
                return
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT score, wins, lives_participated, boxes_checked, boxes_correct, has_accepted_rules, current_streak, font_family, last_live_id FROM users WHERE pseudo = ? AND password_words = ?', (pseudo, password))
            user = c.fetchone()
            
            c.execute('SELECT phrase, count FROM phrase_stats ORDER BY count DESC LIMIT 5')
            phrs = [{"phrase": p[0], "count": p[1]} for p in c.fetchall()]
            if user:
                eff_streak = get_eff_streak_checker(c)
                current_streak_val = eff_streak(user[6] or 0, user[8] or 0)
                c.execute('SELECT max_streak FROM users WHERE pseudo = ?', (pseudo,))
                max_streak_val = c.fetchone()[0] or 0

                c.execute('SELECT COUNT(*) FROM lives')
                total_lives = c.fetchone()[0] or 0

                c.execute('SELECT COUNT(*) FROM users')
                total_users = c.fetchone()[0] or 0

                conn.close()

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                stats = {
                    "score": user[0],
                    "wins": user[1],
                    "lives_participated": user[2],
                    "boxes_checked": user[3],
                    "boxes_correct": user[4],
                    "has_accepted_rules": bool(user[5]),
                    "current_streak": current_streak_val,
                    "font_family": user[7] or '',
                    "max_streak": max_streak_val,
                    "total_lives": total_lives,
                    "total_users": total_users,
                    "top_phrases": phrs
                }
                self.wfile.write(json.dumps(stats).encode('utf-8'))
            else:
                conn.close()
                self.send_error(401)
            
        elif url_path == '/api/fonts':
            import os
            font_dir = os.path.join('public', 'fonts')
            fonts = []
            if os.path.exists(font_dir):
                for f in os.listdir(font_dir):
                    if f.endswith(('.ttf', '.otf', '.woff', '.woff2')):
                        fonts.append(f)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'fonts': fonts}).encode('utf-8'))
            
        elif url_path == '/api/phrases':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            if game_state["is_active"] and game_state["active_phrases"]:
                phrases_to_send = [{'id': i, 'phrase': p} for i, p in enumerate(game_state["active_phrases"])]
            else:
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('SELECT id, phrase FROM phrases')
                phrases_to_send = [{'id': row[0], 'phrase': row[1]} for row in c.fetchall()]
                conn.close()
                
            self.wfile.write(json.dumps(phrases_to_send).encode('utf-8'))

        elif url_path == '/api/user_score':
            pseudo = urllib.parse.unquote(self.headers.get('pseudo', '').strip())
            password = urllib.parse.unquote(self.headers.get('password', '').strip())
            if not pseudo or not password:
                self.send_error(401)
                return
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT score FROM users WHERE pseudo = ? AND password_words = ?', (pseudo, password))
            res = c.fetchone()
            conn.close()
            if res:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'score': res[0]}).encode('utf-8'))
            else:
                self.send_error(401)
        
        elif url_path == '/api/game/state':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            time_left = 0
            if game_state["is_active"]:
                if not game_state.get("is_locked", False):
                    # Phase de jeu
                    elapsed = time.time() - game_state["start_time"] if game_state["start_time"] else 0
                    time_left = max(0, int(game_state["duration"] - elapsed))
                    if time_left == 0:
                        if game_state.get("lock_duration", 0) > 0:
                            game_state["is_locked"] = True
                            game_state["lock_start_time"] = time.time()
                            time_left = game_state["lock_duration"]
                        else:
                            game_state["is_active"] = False
                else:
                    # Phase de verrouillage
                    elapsed = time.time() - game_state["lock_start_time"] if game_state["lock_start_time"] else 0
                    time_left = max(0, int(game_state["lock_duration"] - elapsed))
                    if time_left == 0:
                        game_state["is_active"] = False
                        game_state["is_locked"] = False

            # Calcul du chrono retardataires séparé
            late_time_left = 0
            late_active = False
            late_sess = game_state.get("late_session", {})
            if late_sess.get("is_active"):
                l_elapsed = time.time() - late_sess["start_time"] if late_sess.get("start_time") else 0
                late_time_left = max(0, int(late_sess.get("duration", 300) - l_elapsed))
                if late_time_left > 0:
                    late_active = True
                else:
                    game_state["late_session"]["is_active"] = False

            # Nombre de grilles soumises (géré en mémoire sans interroger la BDD)
            sub_count = game_state.get("submissions_count", 0)

            self.wfile.write(json.dumps({
                "is_active": game_state["is_active"],
                "is_locked": game_state.get("is_locked", False),
                "is_test": bool(game_state.get("is_test", False)),
                "time_left": time_left,
                "late_session": {
                    "is_active": late_active,
                    "time_left": late_time_left,
                    "session_number": late_sess.get("session_number", 0)
                },
                "submissions_count": sub_count,
                "verification_mode": game_state.get("verification_mode", "strict"),
                "color_choice_user_pseudo": game_state.get("color_choice_user_pseudo"),
                "rules_enabled": game_state.get("rules_enabled", False)
            }).encode('utf-8'))

        elif url_path == '/api/game/submissions':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            submissions = []
            if game_state.get("is_active"):
                try:
                    conn = get_db_connection()
                    c = conn.cursor()
                    c.execute('SELECT pseudo, color, submitted_grid, is_late, submitted_at, current_streak FROM users WHERE submitted_grid IS NOT NULL ORDER BY submitted_at ASC, id ASC')
                    for r in c.fetchall():
                        phrases_list = []
                        if r[2]:
                            try:
                                phrases_list = json.loads(r[2])
                            except Exception:
                                phrases_list = []
                        submissions.append({
                            'pseudo': r[0],
                            'color': r[1],
                            'count': len(phrases_list),
                            'phrases': phrases_list,
                            'is_late': bool(r[3]),
                            'submitted_at': r[4] or 0,
                            'streak': r[5] or 0
                        })
                    conn.close()
                except Exception:
                    pass
            self.wfile.write(json.dumps(submissions).encode('utf-8'))

        elif url_path == '/api/action/trigger_late':
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            key = params.get('key', [None])[0]
            
            admin_auth = False
            if key:
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('SELECT id FROM admins WHERE password = ?', (key,))
                if c.fetchone():
                    admin_auth = True
                conn.close()
            elif check_admin(self.headers):
                admin_auth = True
                
            if not admin_auth:
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Unauthorized'}).encode('utf-8'))
                return
                
            if not game_state.get("is_active"):
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Aucun live en cours'}).encode('utf-8'))
                return

            game_state["late_session"] = {
                "is_active": True,
                "start_time": time.time(),
                "duration": 300
            }
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True, 'duration': 300}).encode('utf-8'))

        elif url_path == '/api/admin/users':
            admin_data = check_admin(self.headers)
            if not admin_data:
                self.send_error(401, "Unauthorized")
                return
                
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT id, pseudo, password_words, score, has_accepted_rules, font_family FROM users')
            users = [{'id': row[0], 'pseudo': row[1], 'password': row[2], 'score': row[3], 'has_accepted_rules': bool(row[4]), 'font_family': row[5]} for row in c.fetchall()]
            conn.close()
            self.wfile.write(json.dumps(users).encode('utf-8'))

        elif url_path == '/api/admin/profiles':
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT id, name, phrases_text FROM profiles')
            profiles = [{'id': row[0], 'name': row[1], 'phrases': row[2]} for row in c.fetchall()]
            conn.close()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(profiles).encode('utf-8'))
            
        elif url_path == '/api/admin/game/live_data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'active_phrases': game_state["active_phrases"],
                'admin_ticked': game_state["admin_ticked"]
            }).encode('utf-8'))
            
        elif url_path == '/ping':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'pong')

        elif url_path == '/api/admin/backup':
            admin = check_admin(self.headers)
            if not admin or admin['role'] != 'superadmin':
                self.send_response(401)
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Unauthorized'}).encode('utf-8'))
                return
                
            conn = get_db_connection()
            c = conn.cursor()
            backup_data = {}
            c.execute('SELECT * FROM users')
            users = c.fetchall()
            backup_data['users'] = [{'id': u[0], 'pseudo': u[1], 'score': u[3], 'submitted_grid': u[4], 'color': u[5] if len(u)>5 else None} for u in users]
            c.execute('SELECT * FROM phrase_stats')
            stats = c.fetchall()
            backup_data['phrase_stats'] = [{'phrase': s[0], 'count': s[1]} for s in stats]
            c.execute('SELECT * FROM profiles')
            profiles = c.fetchall()
            backup_data['profiles'] = [{'id': p[0], 'name': p[1], 'phrases': p[2]} for p in profiles]
            conn.close()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-Disposition', 'attachment; filename="bingo_backup.json"')
            self.end_headers()
            self.wfile.write(json.dumps(backup_data, indent=2).encode('utf-8'))

        elif url_path == '/api/admin/stats':
            admin = check_admin(self.headers)
            if not admin:
                self.send_response(401)
                self.end_headers()
                return
            conn = get_db_connection()
            c = conn.cursor()
            
            # Totaux
            c.execute('SELECT COUNT(*) FROM users')
            total_users = c.fetchone()[0] or 0

            c.execute('SELECT COUNT(*) FROM lives')
            total_lives = c.fetchone()[0] or 0

            c.execute('SELECT SUM(boxes_checked), SUM(boxes_correct) FROM users')
            sum_row = c.fetchone()
            total_checked = sum_row[0] or 0
            total_correct = sum_row[1] or 0
            global_accuracy = round((total_correct / total_checked * 100), 1) if total_checked > 0 else 0

            # Top 10 Joueurs par Score
            c.execute('SELECT pseudo, score, wins, lives_participated, current_streak, max_streak, color FROM users ORDER BY score DESC LIMIT 10')
            usrs = [{'pseudo': u[0], 'score': u[1], 'wins': u[2], 'participations': u[3], 'streak': u[4], 'max_streak': u[5], 'color': u[6]} for u in c.fetchall()]

            # Top 10 Phrases les plus validées
            c.execute('SELECT phrase, count FROM phrase_stats ORDER BY count DESC LIMIT 10')
            phrs = [{'phrase': p[0], 'count': p[1]} for p in c.fetchall()]

            # Phrases les moins souvent validées ou jamais dites
            c.execute('SELECT phrase, count FROM phrase_stats ORDER BY count ASC LIMIT 5')
            rare_phrs = [{'phrase': p[0], 'count': p[1]} for p in c.fetchall()]

            # Top 5 Joueurs Sniper (meilleure précision, min 5 cases cochées)
            c.execute('SELECT pseudo, boxes_checked, boxes_correct, color FROM users WHERE boxes_checked >= 5')
            raw_snipers = c.fetchall()
            snipers = []
            for s in raw_snipers:
                pseudo_s, checked_s, correct_s, color_s = s[0], s[1], s[2], s[3]
                acc_s = round((correct_s / checked_s * 100), 1) if checked_s > 0 else 0
                snipers.append({'pseudo': pseudo_s, 'checked': checked_s, 'correct': correct_s, 'accuracy': acc_s, 'color': color_s})
            snipers.sort(key=lambda x: (x['accuracy'], x['correct']), reverse=True)
            snipers = snipers[:5]

            # Top 5 Records de Streak 🔥
            c.execute('SELECT pseudo, max_streak, color FROM users WHERE max_streak > 0 ORDER BY max_streak DESC LIMIT 5')
            top_streaks = [{'pseudo': t[0], 'max_streak': t[1], 'color': t[2]} for t in c.fetchall()]

            conn.close()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            res = {
                "summary": {
                    "total_users": total_users,
                    "total_lives": total_lives,
                    "total_checked": total_checked,
                    "total_correct": total_correct,
                    "global_accuracy": global_accuracy
                },
                "users": usrs,
                "phrases": phrs,
                "rare_phrases": rare_phrs,
                "snipers": snipers,
                "top_streaks": top_streaks
            }
            self.wfile.write(json.dumps(res).encode('utf-8'))
            
        else:
            super().do_GET()

    def do_POST(self):
        global game_state
        url_path = self.path.split('?')[0]
        content_length = int(self.headers.get('Content-Length', 0))
        
        if url_path != '/api/admin/fonts/upload':
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8')) if post_data else {}
            except Exception:
                self.send_response(400)
                self.end_headers()
                return
        else:
            data = {}

        if url_path == '/api/admin/rules/toggle':
            admin_data = check_admin(self.headers)
            if not admin_data or admin_data['role'] not in ['admin', 'superadmin']:
                self.send_error(401, "Unauthorized")
                return
            game_state['rules_enabled'] = data.get('enabled', False)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True, 'rules_enabled': game_state['rules_enabled']}).encode('utf-8'))

        elif url_path == '/api/admin/rules/reset':
            admin_data = check_admin(self.headers)
            if not admin_data or admin_data['role'] not in ['admin', 'superadmin']:
                self.send_error(401, "Unauthorized")
                return
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('UPDATE users SET has_accepted_rules = 0')
            conn.commit()
            conn.close()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode('utf-8'))

        elif url_path == '/api/rules/accept':
            pseudo = urllib.parse.unquote(self.headers.get('pseudo', '').strip())
            password = urllib.parse.unquote(self.headers.get('password', '').strip())
            if not pseudo or not password:
                self.send_error(401)
                return
            conn = get_db_connection()
            c = conn.cursor()
            # Verify credentials
            c.execute('SELECT id FROM users WHERE pseudo = ? AND password_words = ?', (pseudo, password))
            if not c.fetchone():
                self.send_error(401)
                conn.close()
                return
            c.execute('UPDATE users SET has_accepted_rules = 1 WHERE pseudo = ?', (pseudo,))
            conn.commit()
            conn.close()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode('utf-8'))

        elif url_path == '/api/register':
            pseudo = data.get('pseudo', '').strip()
            if not pseudo:
                self.send_error(400, "Bad Request")
                return

            conn = get_db_connection()
            c = conn.cursor()
            try:
                c.execute('SELECT id FROM users WHERE pseudo = ?', (pseudo,))
                if c.fetchone():
                    self.send_response(409)
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Pseudo already exists'}).encode())
                else:
                    password = "-".join(random.sample(WORDS, 3))
                    c.execute('INSERT INTO users (pseudo, password_words) VALUES (?, ?)', (pseudo, password))
                    conn.commit()
                    _users_all_cache["data"] = None
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'password': password}).encode('utf-8'))
            finally:
                conn.close()

        elif url_path == '/api/login':
            pseudo = data.get('pseudo', '').strip()
            password = data.get('password', '').strip()
            
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT color, has_accepted_rules, current_streak, last_live_id FROM users WHERE pseudo = ? AND password_words = ?', (pseudo, password))
            user = c.fetchone()
            if user:
                eff_streak = get_eff_streak_checker(c)
                color = user[0]
                has_accepted = user[1]
                login_streak = eff_streak(user[2] or 0, user[3] or 0)
                conn.close()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'token': pseudo, 'color': color, 'has_accepted_rules': bool(has_accepted), 'current_streak': login_streak}).encode('utf-8'))
            else:
                conn.close()
                self.send_response(401)
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Invalid credentials'}).encode('utf-8'))

        elif url_path == '/api/action/trigger_late':
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            key = params.get('key', [None])[0] or data.get('key') or data.get('password')
            
            admin_auth = False
            if key:
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('SELECT id FROM admins WHERE password = ?', (key,))
                if c.fetchone():
                    admin_auth = True
                conn.close()
            elif check_admin(self.headers):
                admin_auth = True
                
            if not admin_auth:
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Unauthorized'}).encode('utf-8'))
                return
                
            if not game_state.get("is_active"):
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Aucun live en cours'}).encode('utf-8'))
                return

            game_state["late_session"] = {
                "is_active": True,
                "start_time": time.time(),
                "duration": 300
            }
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True, 'duration': 300}).encode('utf-8'))
            return

        elif url_path == '/api/score':
            pseudo = data.get('pseudo', '').strip()
            password = data.get('password', '').strip()
            checked_phrases = data.get('checked_phrases', [])
            
            if not isinstance(checked_phrases, list) or len(checked_phrases) > 5:
                self.send_error(400, "Bad Request")
                return

            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT id, score, submitted_grid, current_streak FROM users WHERE pseudo = ? AND password_words = ?', (pseudo, password))
            user = c.fetchone()
            
            if user:
                # Anti-doublon : Si le joueur a déjà soumis sa grille pour ce live
                if user[2] is not None:
                    conn.close()
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Grille déjà soumise pour cette session'}).encode('utf-8'))
                    return

                # Vérification session retardataires
                is_late_sub = False
                late_active = False
                late_sess = game_state.get("late_session", {})
                if late_sess.get("is_active"):
                    l_elapsed = time.time() - late_sess["start_time"] if late_sess.get("start_time") else 0
                    if l_elapsed < late_sess.get("duration", 300):
                        late_active = True
                    else:
                        game_state["late_session"]["is_active"] = False

                elapsed = time.time() - game_state["start_time"] if game_state.get("start_time") else 0
                main_time_left = max(0, int(game_state.get("duration", 600) - elapsed))
                if late_active or (main_time_left == 0 or game_state.get("is_locked", False)):
                    is_late_sub = True

                # ==========================================
                # MODE TEST : AUCUN IMPACT STATS / STREAKS
                # ==========================================
                if game_state.get("is_test", False):
                    now_t = time.time()
                    c.execute('UPDATE users SET submitted_grid = ?, is_late = ?, submitted_at = ? WHERE id = ?', 
                              (json.dumps(checked_phrases), 1 if is_late_sub else 0, now_t, user[0]))
                    conn.commit()
                    conn.close()
                    game_state["submissions_count"] = game_state.get("submissions_count", 0) + 1
                    is_strict = (game_state.get("verification_mode") == "strict")
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'success': True,
                        'pending': is_strict,
                        'is_late': is_late_sub,
                        'current_streak': user[3] or 0,
                        'is_test': True,
                        'new_score': user[1]
                    }).encode('utf-8'))
                    return

                # Update streak and record participation
                curr_live = game_state.get('current_live_id', 0)
                new_streak = 0
                if curr_live > 0:
                    c.execute('SELECT 1 FROM live_participations WHERE user_id = ? AND live_id = ?', (user[0], curr_live))
                    if not c.fetchone():
                        c.execute('INSERT INTO live_participations (user_id, live_id) VALUES (?, ?)', (user[0], curr_live))

                    c.execute('SELECT DISTINCT live_id FROM live_participations ORDER BY live_id DESC')
                    all_played_lives = [r[0] for r in c.fetchall()]

                    c.execute('SELECT live_id FROM live_participations WHERE user_id = ?', (user[0],))
                    user_played_set = set(r[0] for r in c.fetchall())

                    for l_id in all_played_lives:
                        if l_id in user_played_set:
                            new_streak += 1
                        else:
                            break

                    c.execute('SELECT max_streak FROM users WHERE id = ?', (user[0],))
                    m_row = c.fetchone()
                    current_max = m_row[0] if (m_row and m_row[0]) else 0
                    new_max = max(current_max, new_streak)

                    c.execute('UPDATE users SET current_streak = ?, max_streak = ?, last_live_id = ? WHERE id = ?', 
                              (new_streak, new_max, curr_live, user[0]))

                if (game_state.get("is_active") or late_active) and game_state.get("verification_mode") == "strict":
                    boxes_checked = len(checked_phrases)
                    now_t = time.time()
                    c.execute('UPDATE users SET submitted_grid = ?, is_late = ?, submitted_at = ?, lives_participated = lives_participated + 1, boxes_checked = boxes_checked + ? WHERE id = ?', 
                              (json.dumps(checked_phrases), 1 if is_late_sub else 0, now_t, boxes_checked, user[0]))
                    conn.commit()
                    conn.close()
                    game_state["submissions_count"] = game_state.get("submissions_count", 0) + 1
                    _leaderboard_cache["data"] = None
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'success': True, 'pending': True, 'is_late': is_late_sub, 'current_streak': new_streak}).encode('utf-8'))
                    return

                boxes_checked = len(checked_phrases)
                boxes_correct = 0
                score_to_add = 0
                if game_state.get("verification_mode") == "strict":
                    for phrase in checked_phrases:
                        if phrase in game_state.get("admin_ticked", []):
                            score_to_add += 10
                            boxes_correct += 1
                else:
                    score_to_add = len(checked_phrases) * 10
                    boxes_correct = len(checked_phrases)
                    
                new_score = user[1] + score_to_add
                
                # In trust mode, or when game is inactive, we update standard stats.
                # Note: if the game was active and strict, it already returned above.
                c.execute('UPDATE users SET score = ?, score_live = score_live + ?, lives_participated = lives_participated + 1, boxes_checked = boxes_checked + ?, boxes_correct = boxes_correct + ? WHERE id = ?', (new_score, score_to_add, boxes_checked, boxes_correct, user[0]))
                conn.commit()
                conn.close()
                _leaderboard_cache["data"] = None
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'new_score': new_score, 'current_streak': new_streak}).encode('utf-8'))
            else:
                conn.close()
                self.send_response(401)
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Invalid credentials'}).encode('utf-8'))

        elif url_path == '/api/admin/login':
            password = data.get('password')
            
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT id, role FROM admins WHERE password = ?', (password,))
            admin = c.fetchone()
            conn.close()
            
            if admin:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'token': password, 'role': admin[1]}).encode('utf-8'))
            else:
                self.send_response(401)
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Invalid admin password'}).encode('utf-8'))


        elif url_path == '/api/user/color':
            pseudo = data.get('pseudo', '').strip()
            password = data.get('password', '').strip()
            if not pseudo or not password:
                self.send_response(401)
                self.end_headers()
                return
                
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT id, pseudo FROM users WHERE pseudo = ? AND password_words = ?', (pseudo, password))
            user = c.fetchone()
            conn.close()
            
            if not user:
                self.send_response(401)
                self.end_headers()
                return
                
            if game_state.get('color_choice_user_pseudo') != user[1]:
                self.send_response(403)
                self.end_headers()
                return
                
            color = data.get('color', '').strip()
            import re
            if not re.match(r'^#[0-9a-fA-F]{6}$', color):
                self.send_response(400)
                self.end_headers()
                return
                
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('UPDATE users SET color = ? WHERE id = ?', (color, user[0]))
            conn.commit()
            conn.close()
            
            # Remove the right once used
            game_state['color_choice_user_pseudo'] = None
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode())

        elif url_path.startswith('/api/admin/'):
            admin_data = check_admin(self.headers)
            if not admin_data:
                self.send_response(401)
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Unauthorized'}).encode('utf-8'))
                return

            if url_path == '/api/admin/game/start':
                is_test = bool(data.get("is_test", False))
                game_state["is_active"] = True
                game_state["is_locked"] = False
                game_state["is_test"] = is_test
                game_state["start_time"] = time.time()
                game_state["duration"] = data.get("duration", 600)
                game_state["lock_duration"] = data.get("lock_duration", 0)
                game_state["lock_start_time"] = None
                game_state["verification_mode"] = data.get("verification_mode", "strict")
                game_state["admin_ticked"] = []
                
                profile_id = data.get("profile_id")
                conn = get_db_connection()
                c = conn.cursor()
                # Reset score_live for all users when a new live starts
                c.execute('UPDATE users SET score_live = 0, submitted_grid = NULL, is_late = 0, submitted_at = 0')
                game_state["submissions_count"] = 0
                game_state["late_session"] = {"is_active": False, "start_time": None, "duration": 300}
                _leaderboard_cache["data"] = None

                if not is_test:
                    c.execute('INSERT INTO lives DEFAULT VALUES')
                    c.execute('SELECT MAX(id) FROM lives')
                    max_live = c.fetchone()[0]
                    game_state["current_live_id"] = max_live if max_live else 0
                else:
                    game_state["current_live_id"] = 0

                conn.commit()
                
                if profile_id and str(profile_id) != "random":
                    c.execute('SELECT phrases_text FROM profiles WHERE id = ?', (profile_id,))
                    row = c.fetchone()
                    if row:
                        phrases = [p.strip() for p in row[0].split('\n') if p.strip()]
                        game_state["active_phrases"] = phrases[:16]
                    else:
                        game_state["active_phrases"] = []
                else:
                    c.execute('SELECT phrase FROM phrases')
                    all_phrases = [row[0] for row in c.fetchall()]
                    if len(all_phrases) >= 16:
                        game_state["active_phrases"] = random.sample(all_phrases, 16)
                    else:
                        game_state["active_phrases"] = all_phrases
                conn.close()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'is_test': is_test}).encode('utf-8'))

            elif url_path == '/api/admin/game/stop':
                is_test_mode = bool(game_state.get("is_test", False))
                game_state["is_active"] = False
                game_state["is_locked"] = False
                game_state["is_test"] = False
                game_state["start_time"] = None
                game_state["lock_start_time"] = None
                game_state["late_session"]["is_active"] = False
                game_state["late_session"]["start_time"] = None
                game_state["submissions_count"] = 0
                
                conn = get_db_connection()
                c = conn.cursor()

                if is_test_mode:
                    # En mode test : nettoyage sans toucher aux scores, victoires, participations ni stats de phrases
                    c.execute('UPDATE users SET submitted_grid = NULL, is_late = 0, score_live = 0')
                    conn.commit()
                    conn.close()
                    _leaderboard_cache["data"] = None
                    _users_all_cache["data"] = None
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'success': True, 'is_test': True}).encode('utf-8'))
                    return
                
                # Evaluate scores for players who submitted
                conn = get_db_connection()
                c = conn.cursor()
                
                # Update phrase stats
                try:
                    for phrase_said in game_state["admin_ticked"]:
                        c.execute('SELECT count FROM phrase_stats WHERE phrase = ?', (phrase_said,))
                        r = c.fetchone()
                        if r:
                            c.execute('UPDATE phrase_stats SET count = count + 1 WHERE phrase = ?', (phrase_said,))
                        else:
                            c.execute('INSERT INTO phrase_stats (phrase, count) VALUES (?, 1)', (phrase_said,))
                except Exception as e:
                    pass

                c.execute('SELECT id, score, submitted_grid, is_late FROM users WHERE submitted_grid IS NOT NULL')
                for row in c.fetchall():
                    user_id, current_score, submitted_grid_json, is_late_val = row
                    score_multiplier = 5 if is_late_val else 10
                    try:
                        checked_phrases = json.loads(submitted_grid_json)
                        score_to_add = 0
                        boxes_correct = 0
                        for phrase in checked_phrases:
                            if phrase in game_state["admin_ticked"]:
                                score_to_add += score_multiplier
                                boxes_correct += 1
                        new_score = current_score + score_to_add
                        c.execute('UPDATE users SET score = ?, score_live = score_live + ?, submitted_grid = NULL, is_late = 0, boxes_correct = boxes_correct + ? WHERE id = ?', (new_score, score_to_add, boxes_correct, user_id))
                    except:
                        c.execute('UPDATE users SET submitted_grid = NULL, is_late = 0 WHERE id = ?', (user_id,))
                
                # Award a win to the player(s) with the highest score_live
                c.execute('SELECT MAX(score_live) FROM users')
                max_score = c.fetchone()
                if max_score and max_score[0] and max_score[0] > 0:
                    c.execute('UPDATE users SET wins = wins + 1 WHERE score_live = ?', (max_score[0],))
                
                conn.commit()
                conn.close()

                game_state["submissions_count"] = 0
                _leaderboard_cache["data"] = None
                _users_all_cache["data"] = None

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode('utf-8'))
                
            elif url_path == '/api/admin/stats':
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('SELECT pseudo, score FROM users ORDER BY score DESC LIMIT 10')
                usrs = c.fetchall()
                c.execute('SELECT phrase, count FROM phrase_stats ORDER BY count DESC LIMIT 10')
                phrs = c.fetchall()
                conn.close()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                # Format json
                res = {"users": [{"pseudo": u[0], "score": u[1]} for u in usrs], "phrases": [{"phrase": p[0], "count": p[1]} for p in phrs]}
                self.wfile.write(json.dumps(res).encode('utf-8'))
                
            elif url_path == '/api/admin/users/delete':
                user_id = data.get('id')
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('DELETE FROM users WHERE id = ?', (user_id,))
                conn.commit()
                conn.close()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode('utf-8'))


            elif url_path == '/api/admin/game/grant_color':
                user_id = data.get('user_id')
                if user_id:
                    conn = get_db_connection()
                    c = conn.cursor()
                    c.execute("SELECT pseudo FROM users WHERE id = ?", (user_id,))
                    user = c.fetchone()
                    if user:
                        game_state['color_choice_user_pseudo'] = user[0]
                        c.execute('UPDATE users SET wins = wins + 1 WHERE id = ?', (user_id,))
                        conn.commit()
                    else:
                        game_state['color_choice_user_pseudo'] = None
                    conn.close()
                else:
                    game_state['color_choice_user_pseudo'] = None
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode())

            elif url_path == '/api/admin/user/font':
                user_id = data.get("user_id")
                font_family = data.get("font_family", "")
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('UPDATE users SET font_family = ? WHERE id = ?', (font_family, user_id))
                conn.commit()
                conn.close()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode('utf-8'))
                
            elif url_path == '/api/admin/fonts/upload':
                import os, zipfile, io
                
                content_type = self.headers.get('Content-Type', '')
                if 'multipart/form-data' not in content_type:
                    self.send_error(400, "Bad Request")
                    return
                
                # Parse boundary from Content-Type
                boundary = None
                for part in content_type.split(';'):
                    part = part.strip()
                    if part.startswith('boundary='):
                        boundary = part.split('=', 1)[1].strip('"')
                        break
                
                if not boundary:
                    self.send_error(400, "No boundary found")
                    return
                
                raw_data = self.rfile.read(content_length)
                boundary_bytes = ('--' + boundary).encode()
                parts = raw_data.split(boundary_bytes)
                
                file_data = None
                filename = None
                
                for part in parts:
                    if b'Content-Disposition' not in part:
                        continue
                    # Extract headers and body
                    header_end = part.find(b'\r\n\r\n')
                    if header_end == -1:
                        continue
                    header_section = part[:header_end].decode('utf-8', errors='replace')
                    body = part[header_end + 4:]
                    # Remove trailing \r\n
                    if body.endswith(b'\r\n'):
                        body = body[:-2]
                    
                    if 'name="font_file"' in header_section:
                        # Extract filename
                        for h_part in header_section.split(';'):
                            h_part = h_part.strip()
                            if h_part.startswith('filename='):
                                filename = h_part.split('=', 1)[1].strip('"')
                        file_data = body
                
                if not file_data or not filename:
                    self.send_error(400, "No file uploaded")
                    return
                
                os.makedirs(os.path.join('public', 'fonts'), exist_ok=True)
                saved_fonts = []
                
                if filename.lower().endswith('.zip'):
                    with zipfile.ZipFile(io.BytesIO(file_data)) as z:
                        for zip_info in z.infolist():
                            if zip_info.filename.lower().endswith(('.ttf', '.otf', '.woff', '.woff2')):
                                safe_name = os.path.basename(zip_info.filename)
                                if safe_name:
                                    extracted_path = os.path.join('public', 'fonts', safe_name)
                                    with open(extracted_path, 'wb') as f_out:
                                        f_out.write(z.read(zip_info.filename))
                                    saved_fonts.append(safe_name)
                elif filename.lower().endswith(('.ttf', '.otf', '.woff', '.woff2')):
                    safe_name = os.path.basename(filename)
                    extracted_path = os.path.join('public', 'fonts', safe_name)
                    with open(extracted_path, 'wb') as f_out:
                        f_out.write(file_data)
                    saved_fonts.append(safe_name)
                    
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'saved': saved_fonts}).encode('utf-8'))

            elif url_path == '/api/admin/users/reset':
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('UPDATE users SET score = 0')
                conn.commit()
                conn.close()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode('utf-8'))
                
            elif url_path == '/api/admin/users/points':
                user_id = data.get('id')
                points_to_add = data.get('points')
                
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('SELECT score FROM users WHERE id = ?', (user_id,))
                result = c.fetchone()
                
                if result:
                    new_score = result[0] + points_to_add
                    if new_score < 0:
                        new_score = 0
                    c.execute('UPDATE users SET score = ? WHERE id = ?', (new_score, user_id))
                    conn.commit()
                    
                conn.close()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode('utf-8'))
                
            elif url_path == '/api/admin/create':
                if admin_data['role'] != 'superadmin':
                    self.send_response(403)
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Forbidden'}).encode('utf-8'))
                    return
                    
                new_password = data.get('password', '').strip()
                if new_password:
                    conn = get_db_connection()
                    c = conn.cursor()
                    try:
                        c.execute('INSERT INTO admins (password, role) VALUES (?, ?)', (new_password, 'admin'))
                        conn.commit()
                        self.send_response(200)
                    except DBIntegrityError:
                        self.send_response(400)
                    finally:
                        conn.close()
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode('utf-8'))

            elif url_path == '/api/admin/list_admins':
                if admin_data['role'] != 'superadmin':
                    self.send_response(403)
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Forbidden'}).encode('utf-8'))
                    return
                    
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('SELECT id, password, role FROM admins')
                admins_list = [{'id': row[0], 'password': row[1], 'role': row[2]} for row in c.fetchall()]
                conn.close()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(admins_list).encode('utf-8'))

            elif url_path == '/api/admin/delete_admin':
                if admin_data['role'] != 'superadmin':
                    self.send_response(403)
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Forbidden'}).encode('utf-8'))
                    return
                    
                admin_id = data.get('id')
                conn = get_db_connection()
                c = conn.cursor()
                # Empêcher le superadmin de se supprimer lui-même
                c.execute('DELETE FROM admins WHERE id = ? AND role != "superadmin"', (admin_id,))
                conn.commit()
                conn.close()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode('utf-8'))

            elif url_path == '/api/admin/phrases/add':
                phrase = data.get('phrase', '').strip()
                if phrase:
                    conn = get_db_connection()
                    c = conn.cursor()
                    try:
                        c.execute('INSERT INTO phrases (phrase) VALUES (?)', (phrase,))
                        conn.commit()
                        self.send_response(200)
                    except DBIntegrityError:
                        self.send_response(400)
                    finally:
                        conn.close()
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode('utf-8'))
                
            elif url_path == '/api/admin/phrases/delete':
                phrase_id = data.get('id')
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('DELETE FROM phrases WHERE id = ?', (phrase_id,))
                conn.commit()
                conn.close()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode('utf-8'))
                
            elif url_path == '/api/admin/profiles/add':
                name = data.get('name', '').strip()
                phrases_text = data.get('phrases_text', '').strip()
                if name and phrases_text:
                    conn = get_db_connection()
                    c = conn.cursor()
                    try:
                        c.execute('INSERT INTO profiles (name, phrases_text) VALUES (?, ?)', (name, phrases_text))
                        conn.commit()
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({'success': True}).encode('utf-8'))
                    except Exception as e:
                        self.send_response(400)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({'error': 'Ce nom de profil existe déjà'}).encode('utf-8'))
                    finally:
                        conn.close()
                else:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Nom et phrases requis'}).encode('utf-8'))
                
            elif url_path == '/api/admin/profiles/update':
                profile_id = data.get('id')
                name = data.get('name', '').strip()
                phrases_text = data.get('phrases_text', '').strip()
                if profile_id and name and phrases_text:
                    conn = get_db_connection()
                    c = conn.cursor()
                    try:
                        c.execute('UPDATE profiles SET name = ?, phrases_text = ? WHERE id = ?', (name, phrases_text, profile_id))
                        conn.commit()
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({'success': True}).encode('utf-8'))
                    except Exception as e:
                        self.send_response(400)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({'error': 'Erreur lors de la modification'}).encode('utf-8'))
                    finally:
                        conn.close()
                else:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Données invalides'}).encode('utf-8'))
                
            elif url_path == '/api/admin/profiles/delete':
                profile_id = data.get('id')
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('DELETE FROM profiles WHERE id = ?', (profile_id,))
                conn.commit()
                conn.close()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode('utf-8'))

            elif url_path == '/api/admin/game/tick':
                phrase = data.get('phrase', '')
                is_checked = data.get('checked', False)
                if is_checked:
                    if phrase not in game_state["admin_ticked"]:
                        game_state["admin_ticked"].append(phrase)
                else:
                    if phrase in game_state["admin_ticked"]:
                        game_state["admin_ticked"].remove(phrase)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode('utf-8'))
                
            else:
                self.send_error(404, "Not Found")
        else:
            self.send_error(404, "Not Found")

class ThreadingSimpleServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == '__main__':
    init_db()
    with ThreadingSimpleServer(("", PORT), MyRequestHandler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()
