import urllib.request, json
r = urllib.request.Request('http://localhost:8080/api/admin/game/start', method='POST', data=json.dumps({'duration': 2, 'lock_duration': 2}).encode('utf-8'))
r.add_header('Authorization', 'Bearer Xz7!Kj9$Lm2@Qw1')
r.add_header('Content-Type', 'application/json')
with urllib.request.urlopen(r) as resp:
    print("Start:", json.loads(resp.read().decode()))

r2 = urllib.request.Request('http://localhost:8080/api/game/state', method='GET')
with urllib.request.urlopen(r2) as resp:
    print("State:", json.loads(resp.read().decode()))
