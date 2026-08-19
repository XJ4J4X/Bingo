with open('public/admin.html', 'r') as f:
    content = f.read()

# 1. Add Nav button
nav_old = """            <div style="margin-bottom: 20px; display: flex; gap: 10px;">
                <button id="nav-main-btn" class="success-btn" style="padding: 10px 20px; font-weight: bold; flex: 1;">Gestion du Jeu</button>
                <button id="nav-stats-btn" style="padding: 10px 20px; font-weight: bold; flex: 1; background-color: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer;">Statistiques</button>
            </div>"""
nav_new = """            <div style="margin-bottom: 20px; display: flex; gap: 10px;">
                <button id="nav-main-btn" class="success-btn" style="padding: 10px 20px; font-weight: bold; flex: 1;">Gestion du Jeu</button>
                <button id="nav-stats-btn" style="padding: 10px 20px; font-weight: bold; flex: 1; background-color: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer;">Statistiques</button>
                <button id="nav-accounts-btn" style="padding: 10px 20px; font-weight: bold; flex: 1; background-color: #9b59b6; color: white; border: none; border-radius: 4px; cursor: pointer;">Comptes</button>
            </div>"""
content = content.replace(nav_old, nav_new)

# 2. Extract superadmin section and wrap it
# We know the superadmin-section starts at `<div class="admin-controls" id="superadmin-section">`
# and ends at `            </div> <!-- End main-admin-panel -->`
# We'll just replace the start and end of it.
superadmin_start = """            <div class="admin-controls" id="superadmin-section">
                <h3>Gestion de l'Équipe & Sauvegardes (Superadmin uniquement)</h3>"""
superadmin_new = """            </div> <!-- End main-admin-panel -->
            
            <div id="accounts-section" style="display: none;">
            <div class="admin-controls" id="superadmin-section">
                <h3>Gestion de l'Équipe & Sauvegardes (Superadmin uniquement)</h3>"""
content = content.replace(superadmin_start, superadmin_new)

end_main_panel = """            </div> <!-- End main-admin-panel -->
            
            <div id="stats-section" style="display: none;" class="admin-controls">"""
end_main_panel_new = """            </div> <!-- End accounts-section -->
            
            <div id="stats-section" style="display: none;" class="admin-controls">"""
# Wait, this replace might be tricky because of spacing. Let's do a more robust approach.
# Actually, I can just use python regex or find/replace carefully.
# The original code has:
#             <div class="admin-controls" id="superadmin-section">
#                 ...
#             </div>
#             
#             </div> <!-- End main-admin-panel -->

content = content.replace(
    '            <div class="admin-controls" id="superadmin-section">',
    '            </div> <!-- End main-admin-panel -->\n            <div id="accounts-section" style="display: none;">\n            <div class="admin-controls" id="superadmin-section">'
)
content = content.replace(
    '            </div>\n            \n            </div> <!-- End main-admin-panel -->',
    '            </div>\n            </div> <!-- End accounts-section -->'
)

with open('public/admin.html', 'w') as f:
    f.write(content)
