import re
with open('server.py', 'r') as f:
    content = f.read()

# 1. Update /api/game/state in do_GET
state_old = """        elif self.path == '/api/game/state':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            safe_state = {
                "is_active": game_state["is_active"],
                "start_time": game_state["start_time"],
                "duration": game_state["duration"],
                "lock_start_time": game_state["lock_start_time"],
                "lock_duration": game_state["lock_duration"],
                "is_locked": game_state["is_locked"],
                "verification_mode": game_state["verification_mode"]
            }
            self.wfile.write(json.dumps(safe_state).encode('utf-8'))"""
state_new = """        elif self.path == '/api/game/state':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            safe_state = {
                "is_active": game_state["is_active"],
                "start_time": game_state["start_time"],
                "duration": game_state["duration"],
                "lock_start_time": game_state["lock_start_time"],
                "lock_duration": game_state["lock_duration"],
                "is_locked": game_state["is_locked"],
                "verification_mode": game_state["verification_mode"],
                "color_choice_user_id": game_state["color_choice_user_id"]
            }
            self.wfile.write(json.dumps(safe_state).encode('utf-8'))"""
content = content.replace(state_old, state_new)

# 2. Add /api/user/color in do_POST before /api/admin
# I'll insert it right before: elif self.path.startswith('/api/admin/'):
user_color_route = """
        elif self.path == '/api/user/color':
            user = check_user(self.headers)
            if not user:
                self.send_response(401)
                self.end_headers()
                return
            if game_state.get('color_choice_user_id') != user['id']:
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
            c.execute('UPDATE users SET color = ? WHERE id = ?', (color, user['id']))
            conn.commit()
            conn.close()
            
            # Remove the right once used
            game_state['color_choice_user_id'] = None
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode())
"""
content = content.replace("        elif self.path.startswith('/api/admin/'):", user_color_route + "\n        elif self.path.startswith('/api/admin/'):")

# 3. Add /api/admin/game/grant_color in do_POST under admin block
grant_color_route = """
            elif self.path == '/api/admin/game/grant_color':
                user_id = data.get('user_id')
                if user_id:
                    game_state['color_choice_user_id'] = int(user_id)
                else:
                    game_state['color_choice_user_id'] = None
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode())
"""
# I'll insert it after '/api/admin/game/tick'
content = content.replace("            elif self.path == '/api/admin/users/reset':", grant_color_route + "\n            elif self.path == '/api/admin/users/reset':")

with open('server.py', 'w') as f:
    f.write(content)
