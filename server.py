# Aminato si tu lis cette phrase j'ai galerer mdr -- J4X
import http.server
import socketserver
import json
import sqlite3
import os

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

PORT = 8080
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
    "start_time": None,
    "duration": 600,
    "lock_duration": 0,
    "lock_start_time": None,
    "verification_mode": "trust",
    "active_phrases": [],
    "admin_ticked": []
}

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pseudo TEXT UNIQUE,
            password_words TEXT,
            score INTEGER DEFAULT 0,
            submitted_grid TEXT
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

class MyRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="public", **kwargs)

    def do_GET(self):
        if self.path == '/api/leaderboard':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT pseudo, score FROM users ORDER BY score DESC LIMIT 50')
            users = [{'pseudo': row[0], 'score': row[1]} for row in c.fetchall()]
            conn.close()
            self.wfile.write(json.dumps(users).encode('utf-8'))
            
        elif self.path == '/api/phrases':
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

        elif self.path == '/api/user_score':
            pseudo = self.headers.get('pseudo', '').strip()
            password = self.headers.get('password', '').strip()
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
        
        elif self.path == '/api/game/state':
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
            self.wfile.write(json.dumps({
                "is_active": game_state["is_active"],
                "is_locked": game_state.get("is_locked", False),
                "time_left": time_left,
                "verification_mode": game_state.get("verification_mode", "auto")
            }).encode('utf-8'))

        elif self.path == '/api/admin/users':
            admin_data = check_admin(self.headers)
            if not admin_data:
                self.send_error(401, "Unauthorized")
                return
                
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT id, pseudo, password_words, score FROM users')
            users = [{'id': row[0], 'pseudo': row[1], 'password': row[2], 'score': row[3]} for row in c.fetchall()]
            conn.close()
            self.wfile.write(json.dumps(users).encode('utf-8'))

        elif self.path == '/api/admin/profiles':
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT id, name, phrases_text FROM profiles')
            profiles = [{'id': row[0], 'name': row[1], 'phrases': row[2]} for row in c.fetchall()]
            conn.close()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(profiles).encode('utf-8'))
            
        elif self.path == '/api/admin/game/live_data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'active_phrases': game_state["active_phrases"],
                'admin_ticked': game_state["admin_ticked"]
            }).encode('utf-8'))
            
        elif self.path == '/ping':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'pong')

        elif self.path == '/api/admin/backup':
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
            backup_data['users'] = [{'id': u[0], 'pseudo': u[1], 'score': u[3], 'submitted_grid': u[4]} for u in users]
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

        elif self.path == '/api/admin/stats':
            admin = check_admin(self.headers)
            if not admin:
                self.send_response(401)
                self.end_headers()
                return
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
            res = {"users": [{"pseudo": u[0], "score": u[1]} for u in usrs], "phrases": [{"phrase": p[0], "count": p[1]} for p in phrs]}
            self.wfile.write(json.dumps(res).encode('utf-8'))
            
        else:
            super().do_GET()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8')) if post_data else {}
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return

        if self.path == '/api/register':
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
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'password': password}).encode('utf-8'))
            finally:
                conn.close()

        elif self.path == '/api/login':
            pseudo = data.get('pseudo', '').strip()
            password = data.get('password', '').strip()
            
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT id FROM users WHERE pseudo = ? AND password_words = ?', (pseudo, password))
            user = c.fetchone()
            conn.close()

            if user:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode('utf-8'))
            else:
                self.send_response(401)
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Invalid credentials'}).encode('utf-8'))

        elif self.path == '/api/score':
            pseudo = data.get('pseudo', '').strip()
            password = data.get('password', '').strip()
            checked_phrases = data.get('checked_phrases', [])
            
            if not isinstance(checked_phrases, list) or len(checked_phrases) > 5:
                self.send_error(400, "Bad Request")
                return

            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT id, score FROM users WHERE pseudo = ? AND password_words = ?', (pseudo, password))
            user = c.fetchone()
            
            if user:
                if game_state["is_active"] and game_state["verification_mode"] == "strict":
                    c.execute('UPDATE users SET submitted_grid = ? WHERE id = ?', (json.dumps(checked_phrases), user[0]))
                    conn.commit()
                    conn.close()
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'success': True, 'pending': True}).encode('utf-8'))
                    return

                score_to_add = 0
                if game_state["verification_mode"] == "strict":
                    for phrase in checked_phrases:
                        if phrase in game_state["admin_ticked"]:
                            score_to_add += 10
                else:
                    score_to_add = len(checked_phrases) * 10
                    
                new_score = user[1] + score_to_add
                c.execute('UPDATE users SET score = ? WHERE id = ?', (new_score, user[0]))
                conn.commit()
                conn.close()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'new_score': new_score}).encode('utf-8'))
            else:
                conn.close()
                self.send_response(401)
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Invalid credentials'}).encode('utf-8'))

        elif self.path == '/api/admin/login':
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

        elif self.path.startswith('/api/admin/'):
            admin_data = check_admin(self.headers)
            if not admin_data:
                self.send_response(401)
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Unauthorized'}).encode('utf-8'))
                return

            if self.path == '/api/admin/game/start':
                game_state["is_active"] = True
                game_state["is_locked"] = False
                game_state["start_time"] = time.time()
                game_state["duration"] = data.get("duration", 600)
                game_state["lock_duration"] = data.get("lock_duration", 0)
                game_state["lock_start_time"] = None
                game_state["verification_mode"] = data.get("verification_mode", "trust")
                game_state["admin_ticked"] = []
                
                profile_id = data.get("profile_id")
                conn = get_db_connection()
                c = conn.cursor()
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
                self.wfile.write(json.dumps({'success': True}).encode('utf-8'))

            elif self.path == '/api/admin/game/stop':
                game_state["is_active"] = False
                game_state["is_locked"] = False
                game_state["start_time"] = None
                game_state["lock_start_time"] = None
                
                # Evaluate scores for players who submitted early
                conn = get_db_connection()
                c = conn.cursor()
                
                # Update phrase stats (amateur style code)
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

                c.execute('SELECT id, score, submitted_grid FROM users WHERE submitted_grid IS NOT NULL')
                for row in c.fetchall():
                    user_id, current_score, submitted_grid_json = row
                    try:
                        checked_phrases = json.loads(submitted_grid_json)
                        score_to_add = 0
                        for phrase in checked_phrases:
                            if phrase in game_state["admin_ticked"]:
                                score_to_add += 10
                        new_score = current_score + score_to_add
                        c.execute('UPDATE users SET score = ?, submitted_grid = NULL WHERE id = ?', (new_score, user_id))
                    except:
                        c.execute('UPDATE users SET submitted_grid = NULL WHERE id = ?', (user_id,))
                conn.commit()
                conn.close()

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode('utf-8'))
                
            elif self.path == '/api/admin/stats':
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
                
            elif self.path == '/api/admin/users/delete':
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

            elif self.path == '/api/admin/users/reset':
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('UPDATE users SET score = 0')
                conn.commit()
                conn.close()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode('utf-8'))
                
            elif self.path == '/api/admin/users/points':
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
                
            elif self.path == '/api/admin/create':
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

            elif self.path == '/api/admin/list_admins':
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

            elif self.path == '/api/admin/delete_admin':
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

            elif self.path == '/api/admin/phrases/add':
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
                
            elif self.path == '/api/admin/phrases/delete':
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
                
            elif self.path == '/api/admin/profiles/add':
                name = data.get('name', '').strip()
                phrases_text = data.get('phrases_text', '').strip()
                if name and phrases_text:
                    conn = get_db_connection()
                    c = conn.cursor()
                    try:
                        c.execute('INSERT INTO profiles (name, phrases_text) VALUES (?, ?)', (name, phrases_text))
                        conn.commit()
                        self.send_response(200)
                    except DBIntegrityError:
                        self.send_response(400)
                    finally:
                        conn.close()
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode('utf-8'))
                
            elif self.path == '/api/admin/profiles/delete':
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

            elif self.path == '/api/admin/game/tick':
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
