with open('public/admin.html', 'r') as f:
    content = f.read()

# 1. Extract the users block
start_idx = content.find('            <div class="admin-controls">\n                <h3>Gestion des Utilisateurs</h3>')
end_idx = content.find('            <div class="admin-controls">\n                <h3>Gestion des Phrases Bingo</h3>')

if start_idx != -1 and end_idx != -1:
    users_block = content[start_idx:end_idx]
    # Remove from main panel
    content = content[:start_idx] + content[end_idx:]
    
    # Inject into accounts section
    inject_target = '            <div id="accounts-section" style="display: none;">\n'
    accounts_start = content.find(inject_target)
    if accounts_start != -1:
        insert_idx = accounts_start + len(inject_target)
        content = content[:insert_idx] + users_block + content[insert_idx:]
        
        with open('public/admin.html', 'w') as f:
            f.write(content)
        print("Success")
    else:
        print("Accounts section not found")
else:
    print("Users block not found")
