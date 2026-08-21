with open('/Users/aurelien/.gemini/antigravity/brain/1cd2a214-eca4-4830-908b-630ef1eeacb6/task.md', 'r') as f:
    content = f.read()
content = content.replace('`[ ]`', '`[x]`')
with open('/Users/aurelien/.gemini/antigravity/brain/1cd2a214-eca4-4830-908b-630ef1eeacb6/task.md', 'w') as f:
    f.write(content)
