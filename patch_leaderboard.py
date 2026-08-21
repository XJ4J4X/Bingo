with open('server.py', 'r') as f:
    content = f.read()

old_leaderboard = """        if self.path == '/api/leaderboard':
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT pseudo, score, color FROM users ORDER BY score DESC LIMIT 10')
            users = [{"pseudo": row[0], "score": row[1], "color": row[2]} for row in c.fetchall()]
            conn.close()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(users).encode('utf-8'))"""

new_leaderboard = """        if self.path == '/api/leaderboard':
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT pseudo, score, color FROM users ORDER BY score DESC LIMIT 10')
            top_score = [{"pseudo": row[0], "score": row[1], "color": row[2]} for row in c.fetchall()]
            
            c.execute('SELECT pseudo, wins, color FROM users ORDER BY wins DESC LIMIT 10')
            top_wins = [{"pseudo": row[0], "wins": row[1], "color": row[2]} for row in c.fetchall()]
            conn.close()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"top_score": top_score, "top_wins": top_wins}).encode('utf-8'))
            
        elif self.path == '/api/user_stats':
            pseudo = self.headers.get('pseudo', '').strip()
            password = self.headers.get('password', '').strip()
            if not pseudo or not password:
                self.send_error(401)
                return
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT score, wins, lives_participated, boxes_checked, boxes_correct FROM users WHERE pseudo = ? AND password_words = ?', (pseudo, password))
            user = c.fetchone()
            
            c.execute('SELECT phrase, count FROM phrase_stats ORDER BY count DESC LIMIT 5')
            phrs = [{"phrase": p[0], "count": p[1]} for p in c.fetchall()]
            conn.close()
            
            if user:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'score': user[0],
                    'wins': user[1],
                    'lives_participated': user[2],
                    'boxes_checked': user[3],
                    'boxes_correct': user[4],
                    'top_phrases': phrs
                }).encode('utf-8'))
            else:
                self.send_error(401)"""

if old_leaderboard in content:
    content = content.replace(old_leaderboard, new_leaderboard)
    with open('server.py', 'w') as f:
        f.write(content)
    print("Patched leaderboard and stats.")
else:
    print("old_leaderboard not found.")
