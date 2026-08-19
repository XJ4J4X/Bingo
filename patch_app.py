with open('public/app.js', 'r') as f:
    content = f.read()

# 1. Add elements
elements_old = """const leaderboardBody = document.getElementById('leaderboard-body');"""
elements_new = """const leaderboardBody = document.getElementById('leaderboard-body');
const colorPickerSection = document.getElementById('color-picker-section');
const userColorPicker = document.getElementById('user-color-picker');
const saveColorBtn = document.getElementById('save-color-btn');"""
content = content.replace(elements_old, elements_new)

# 2. Add save color logic
save_logic = """
saveColorBtn.addEventListener('click', async () => {
    const color = userColorPicker.value;
    try {
        const res = await fetch('/api/user/color', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${userToken}`
            },
            body: JSON.stringify({ color })
        });
        if (res.ok) {
            alert("Couleur sauvegardée avec succès !");
            colorPickerSection.classList.add('hidden');
            fetchLeaderboard();
        } else {
            alert("Erreur lors de la sauvegarde de la couleur.");
        }
    } catch (e) {
        console.error(e);
    }
});
"""
# Insert before fetchGameState
content = content.replace("async function fetchGameState() {", save_logic + "\nasync function fetchGameState() {")

# 3. Update game state to show color picker
state_old = """        if (state.is_locked) {
            validationLockOverlay.classList.remove('hidden');
        } else {
            validationLockOverlay.classList.add('hidden');
        }
    } catch (e) {"""
state_new = """        if (state.is_locked) {
            validationLockOverlay.classList.remove('hidden');
        } else {
            validationLockOverlay.classList.add('hidden');
        }
        
        // Show color picker if user is the winner
        if (isLoggedIn && currentUser && state.color_choice_user_id === currentUser.id) {
            colorPickerSection.classList.remove('hidden');
        } else if (colorPickerSection && !colorPickerSection.classList.contains('hidden')) {
            colorPickerSection.classList.add('hidden');
        }
    } catch (e) {"""
content = content.replace(state_old, state_new)

# 4. Update fetchLeaderboard to apply colors and aminato effect
leaderboard_old = """        users.forEach((u, idx) => {
            const tr = document.createElement('tr');
            if (currentUser && u.pseudo === currentUser.pseudo) {
                tr.style.fontWeight = 'bold';
                tr.style.backgroundColor = 'var(--bg-tertiary)';
            }
            tr.innerHTML = `
                <td>#${idx + 1}</td>
                <td>${u.pseudo}</td>
                <td>${u.score}</td>
            `;
            leaderboardBody.appendChild(tr);
        });"""
leaderboard_new = """        users.forEach((u, idx) => {
            const tr = document.createElement('tr');
            if (currentUser && u.pseudo === currentUser.pseudo) {
                tr.style.backgroundColor = 'var(--bg-tertiary)';
            }
            
            let pseudoDisplay = u.pseudo;
            let pseudoClass = '';
            let pseudoStyle = '';
            
            if (u.pseudo.toLowerCase() === 'aminato') {
                pseudoClass = 'aminato-effect';
            } else if (u.color) {
                pseudoStyle = `color: ${u.color}; font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);`;
            } else if (currentUser && u.pseudo === currentUser.pseudo) {
                pseudoStyle = 'font-weight: bold;';
            }
            
            tr.innerHTML = `
                <td>#${idx + 1}</td>
                <td class="${pseudoClass}" style="${pseudoStyle}">${u.pseudo}</td>
                <td>${u.score}</td>
            `;
            leaderboardBody.appendChild(tr);
        });"""
content = content.replace(leaderboard_old, leaderboard_new)

with open('public/app.js', 'w') as f:
    f.write(content)
