with open('server.py', 'r') as f:
    content = f.read()

# 1. Update game_state
game_state_old = """game_state = {
    "is_active": False,
    "is_locked": False,
    "start_time": None,
    "duration": 600,
    "lock_duration": 0,
    "lock_start_time": None,
    "verification_mode": "trust",
    "active_phrases": [],
    "admin_ticked": []
}"""
game_state_new = """game_state = {
    "is_active": False,
    "is_locked": False,
    "start_time": None,
    "duration": 600,
    "lock_duration": 0,
    "lock_start_time": None,
    "verification_mode": "trust",
    "active_phrases": [],
    "admin_ticked": [],
    "color_choice_user_id": None
}"""
content = content.replace(game_state_old, game_state_new)

# 2. Update init_db schema
schema_old = """        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pseudo TEXT UNIQUE,
            password_words TEXT,
            score INTEGER DEFAULT 0,
            submitted_grid TEXT
        )"""
schema_new = """        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pseudo TEXT UNIQUE,
            password_words TEXT,
            score INTEGER DEFAULT 0,
            submitted_grid TEXT,
            color TEXT
        )"""
content = content.replace(schema_old, schema_new)

# 3. Update init_db column check for migration
pragma_old = """    if 'submitted_grid' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN submitted_grid TEXT")
    c.execute('''
        CREATE TABLE IF NOT EXISTS phrases ("""
pragma_new = """    if 'submitted_grid' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN submitted_grid TEXT")
    if 'color' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN color TEXT")
    c.execute('''
        CREATE TABLE IF NOT EXISTS phrases ("""
content = content.replace(pragma_old, pragma_new)

# 4. Update /api/leaderboard to return color
leaderboard_old = """            c.execute('SELECT pseudo, score FROM users ORDER BY score DESC LIMIT 50')
            users = [{'pseudo': row[0], 'score': row[1]} for row in c.fetchall()]"""
leaderboard_new = """            c.execute('SELECT pseudo, score, color FROM users ORDER BY score DESC LIMIT 50')
            users = [{'pseudo': row[0], 'score': row[1], 'color': row[2]} for row in c.fetchall()]"""
content = content.replace(leaderboard_old, leaderboard_new)

# 5. Update backup to include color
backup_old = """backup_data['users'] = [{'id': u[0], 'pseudo': u[1], 'score': u[3], 'submitted_grid': u[4]} for u in users]"""
backup_new = """backup_data['users'] = [{'id': u[0], 'pseudo': u[1], 'score': u[3], 'submitted_grid': u[4], 'color': u[5] if len(u)>5 else None} for u in users]"""
content = content.replace(backup_old, backup_new)

with open('server.py', 'w') as f:
    f.write(content)
