import urllib.request
import json
import time

def req(path, method='GET', data=None):
    r = urllib.request.Request(f'http://localhost:8080{path}', method=method)
    r.add_header('Authorization', 'Bearer Xz7!Kj9$Lm2@Qw1')
    if data:
        r.data = json.dumps(data).encode('utf-8')
        r.add_header('Content-Type', 'application/json')
    with urllib.request.urlopen(r) as resp:
        return json.loads(resp.read().decode())

print(req('/api/admin/game/start', 'POST', {'duration': 2, 'lock_duration': 2}))
print("Start ->", req('/api/game/state'))
time.sleep(2.5)
print("After 2s (Locked) ->", req('/api/game/state'))
time.sleep(2.5)
print("After 5s (Stop) ->", req('/api/game/state'))
