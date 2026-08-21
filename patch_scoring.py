import re

with open('server.py', 'r') as f:
    content = f.read()

# Patch /api/score
old_api_score = """                if game_state["is_active"] and game_state["verification_mode"] == "strict":
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
                c.execute('UPDATE users SET score = ? WHERE id = ?', (new_score, user[0]))"""

new_api_score = """                if game_state["is_active"] and game_state["verification_mode"] == "strict":
                    boxes_checked = len(checked_phrases)
                    c.execute('UPDATE users SET submitted_grid = ?, lives_participated = lives_participated + 1, boxes_checked = boxes_checked + ? WHERE id = ?', (json.dumps(checked_phrases), boxes_checked, user[0]))
                    conn.commit()
                    conn.close()
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'success': True, 'pending': True}).encode('utf-8'))
                    return

                boxes_checked = len(checked_phrases)
                boxes_correct = 0
                score_to_add = 0
                if game_state["verification_mode"] == "strict":
                    for phrase in checked_phrases:
                        if phrase in game_state["admin_ticked"]:
                            score_to_add += 10
                            boxes_correct += 1
                else:
                    score_to_add = len(checked_phrases) * 10
                    boxes_correct = len(checked_phrases)
                    
                new_score = user[1] + score_to_add
                c.execute('UPDATE users SET score = ?, lives_participated = lives_participated + 1, boxes_checked = boxes_checked + ?, boxes_correct = boxes_correct + ? WHERE id = ?', (new_score, boxes_checked, boxes_correct, user[0]))"""

if old_api_score in content:
    content = content.replace(old_api_score, new_api_score)
    print("Replaced /api/score")
else:
    print("Could not find /api/score block")

# Patch /api/admin/game/stop
old_admin_stop = """                        checked_phrases = json.loads(submitted_grid_json)
                        score_to_add = 0
                        for phrase in checked_phrases:
                            if phrase in game_state["admin_ticked"]:
                                score_to_add += 10
                        new_score = current_score + score_to_add
                        c.execute('UPDATE users SET score = ?, submitted_grid = NULL WHERE id = ?', (new_score, user_id))"""

new_admin_stop = """                        checked_phrases = json.loads(submitted_grid_json)
                        score_to_add = 0
                        boxes_correct = 0
                        for phrase in checked_phrases:
                            if phrase in game_state["admin_ticked"]:
                                score_to_add += 10
                                boxes_correct += 1
                        new_score = current_score + score_to_add
                        c.execute('UPDATE users SET score = ?, submitted_grid = NULL, boxes_correct = boxes_correct + ? WHERE id = ?', (new_score, boxes_correct, user_id))"""

if old_admin_stop in content:
    content = content.replace(old_admin_stop, new_admin_stop)
    print("Replaced /api/admin/game/stop")
else:
    print("Could not find /api/admin/game/stop block")

with open('server.py', 'w') as f:
    f.write(content)
