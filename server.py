# Aminato si tu lis cette phrase j'ai galerer mdr -- J4X
import http.server
import socketserver
import json
import sqlite3
import random
import os
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
    "start_time": None,
    "duration": 600,
    "verification_mode": "trust",
    "active_phrases": [],
    "admin_ticked": []
}

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pseudo TEXT UNIQUE,
            password_words TEXT,
            score INTEGER DEFAULT 0
        )
    ''')
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
    
    c.execute('SELECT COUNT(*) FROM phrases')
    if c.fetchone()[0] == 0:
        for phrase in DEFAULT_PHRASES:
            c.execute('INSERT INTO phrases (phrase) VALUES (?)', (phrase,))
            
    c.execute('SELECT COUNT(*) FROM admins')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO admins (password, role) VALUES (?, ?)', ("Xz7!Kj9$Lm2@Qw1", "superadmin"))
    
    conn.commit()
    conn.close()

def check_admin(headers):
    auth_header = headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    provided_password = auth_header.split("Bearer ")[1]
    
    conn = sqlite3.connect(DB_FILE)
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
            conn = sqlite3.connect(DB_FILE)
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
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute('SELECT id, phrase FROM phrases')
                phrases_to_send = [{'id': row[0], 'phrase': row[1]} for row in c.fetchall()]
                conn.close()
                
            self.wfile.write(json.dumps(phrases_to_send).encode('utf-8'))

        elif self.path == '/api/game/state':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            time_left = 0
            if game_state["is_active"] and game_state["start_time"]:
                elapsed = time.time() - game_state["start_time"]
                time_left = max(0, int(game_state["duration"] - elapsed))
                if time_left == 0:
                    game_state["is_active"] = False
            
            self.wfile.write(json.dumps({
                "is_active": game_state["is_active"],
                "time_left": time_left
            }).encode('utf-8'))

        elif self.path == '/api/admin/users':
            admin_data = check_admin(self.headers)
            if not admin_data:
                self.send_error(401, "Unauthorized")
                return
                
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('SELECT id, pseudo, password_words, score FROM users')
            users = [{'id': row[0], 'pseudo': row[1], 'password': row[2], 'score': row[3]} for row in c.fetchall()]
            conn.close()
            self.wfile.write(json.dumps(users).encode('utf-8'))

        elif self.path == '/api/admin/profiles':
            conn = sqlite3.connect(DB_FILE)
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

            conn = sqlite3.connect(DB_FILE)
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
            
            conn = sqlite3.connect(DB_FILE)
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

            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('SELECT id, score FROM users WHERE pseudo = ? AND password_words = ?', (pseudo, password))
            user = c.fetchone()
            
            if user:
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
            
            conn = sqlite3.connect(DB_FILE)
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
                game_state["start_time"] = time.time()
                game_state["duration"] = data.get("duration", 600)
                game_state["verification_mode"] = data.get("verification_mode", "trust")
                game_state["admin_ticked"] = []
                
                profile_id = data.get("profile_id")
                conn = sqlite3.connect(DB_FILE)
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
                game_state["start_time"] = None
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode('utf-8'))
                
            elif self.path == '/api/admin/users/delete':
                user_id = data.get('id')
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute('DELETE FROM users WHERE id = ?', (user_id,))
                conn.commit()
                conn.close()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode('utf-8'))

            elif self.path == '/api/admin/users/reset':
                conn = sqlite3.connect(DB_FILE)
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
                
                conn = sqlite3.connect(DB_FILE)
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
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    try:
                        c.execute('INSERT INTO admins (password, role) VALUES (?, ?)', (new_password, 'admin'))
                        conn.commit()
                        self.send_response(200)
                    except sqlite3.IntegrityError:
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
                    
                conn = sqlite3.connect(DB_FILE)
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
                conn = sqlite3.connect(DB_FILE)
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
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    try:
                        c.execute('INSERT INTO phrases (phrase) VALUES (?)', (phrase,))
                        conn.commit()
                        self.send_response(200)
                    except sqlite3.IntegrityError:
                        self.send_response(400)
                    finally:
                        conn.close()
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode('utf-8'))
                
            elif self.path == '/api/admin/phrases/delete':
                phrase_id = data.get('id')
                conn = sqlite3.connect(DB_FILE)
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
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    try:
                        c.execute('INSERT INTO profiles (name, phrases_text) VALUES (?, ?)', (name, phrases_text))
                        conn.commit()
                        self.send_response(200)
                    except sqlite3.IntegrityError:
                        self.send_response(400)
                    finally:
                        conn.close()
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode('utf-8'))
                
            elif self.path == '/api/admin/profiles/delete':
                profile_id = data.get('id')
                conn = sqlite3.connect(DB_FILE)
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
