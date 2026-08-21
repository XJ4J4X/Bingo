with open('public/app.js', 'r') as f:
    content = f.read()

# Replace loadLeaderboard
old_load = """async function loadLeaderboard() {
    try {
        const res = await fetch('/api/leaderboard');
        const data = await res.json();
        
        leaderboardBody.innerHTML = '';
        
        if (data.length === 0) {
            leaderboardBody.innerHTML = '<tr><td colspan="3" style="text-align: center;">Aucun score pour le moment.</td></tr>';
            return;
        }
        
        data.forEach((user, index) => {
            const tr = document.createElement('tr');
            
            let pseudoDisplay = user.pseudo.replace(/J4X/gi, '<span class="j4x-highlight">$&</span>');
            let pseudoClass = '';
            let pseudoStyle = '';
            
            if (user.pseudo.toLowerCase() === 'aminat0_') {
                pseudoClass = 'aminato-effect';
            } else if (user.color) {
                pseudoStyle = `color: ${user.color}; font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);`;
            } else if (currentUser && user.pseudo === currentUser.pseudo) {
                pseudoStyle = 'font-weight: bold;';
            }
            
            if (currentUser && user.pseudo === currentUser.pseudo) {
                tr.style.backgroundColor = 'rgba(255, 234, 167, 0.5)'; // Highlight
            }
            
            tr.innerHTML = `
                <td>#${index + 1}</td>
                <td class="${pseudoClass}" style="${pseudoStyle}">${pseudoDisplay}</td>
                <td>${user.score} pts</td>
            `;
            leaderboardBody.appendChild(tr);
        });
    } catch (err) {
        console.error("Erreur classement:", err);
    }
}"""

new_load = """let currentLeaderboardMode = 'score';
let leaderboardData = { top_score: [], top_wins: [] };

document.getElementById('btn-top-score')?.addEventListener('click', () => {
    currentLeaderboardMode = 'score';
    document.getElementById('btn-top-score').classList.add('active');
    document.getElementById('btn-top-wins').classList.remove('active');
    document.getElementById('leaderboard-value-header').textContent = 'Score';
    renderLeaderboard();
});

document.getElementById('btn-top-wins')?.addEventListener('click', () => {
    currentLeaderboardMode = 'wins';
    document.getElementById('btn-top-wins').classList.add('active');
    document.getElementById('btn-top-score').classList.remove('active');
    document.getElementById('leaderboard-value-header').textContent = 'Victoires';
    renderLeaderboard();
});

async function loadLeaderboard() {
    try {
        const res = await fetch('/api/leaderboard');
        leaderboardData = await res.json();
        renderLeaderboard();
    } catch (err) {
        console.error("Erreur classement:", err);
    }
}

function renderLeaderboard() {
    leaderboardBody.innerHTML = '';
    const data = currentLeaderboardMode === 'score' ? leaderboardData.top_score : leaderboardData.top_wins;
    
    if (!data || data.length === 0) {
        leaderboardBody.innerHTML = '<tr><td colspan="3" style="text-align: center;">Aucun score pour le moment.</td></tr>';
        return;
    }
    
    data.forEach((user, index) => {
        const tr = document.createElement('tr');
        
        let pseudoDisplay = user.pseudo.replace(/J4X/gi, '<span class="j4x-highlight">$&</span>');
        let pseudoClass = '';
        let pseudoStyle = '';
        
        if (user.pseudo.toLowerCase() === 'aminat0_') {
            pseudoClass = 'aminato-effect';
        } else if (user.color) {
            pseudoStyle = `color: ${user.color}; font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);`;
        } else if (currentUser && user.pseudo === currentUser) {
            pseudoStyle = 'font-weight: bold;';
        }
        
        if (currentUser && user.pseudo === currentUser) {
            tr.style.backgroundColor = 'rgba(255, 234, 167, 0.5)'; // Highlight
        }
        
        const val = currentLeaderboardMode === 'score' ? `${user.score} pts` : `${user.wins} victoires`;
        
        tr.innerHTML = `
            <td>#${index + 1}</td>
            <td class="${pseudoClass}" style="${pseudoStyle}">${pseudoDisplay}</td>
            <td>${val}</td>
        `;
        leaderboardBody.appendChild(tr);
    });
}

async function loadUserStats() {
    if (!currentUser || !currentPassword) return;
    try {
        const res = await fetch('/api/user_stats', {
            headers: {
                'pseudo': currentUser,
                'password': currentPassword
            }
        });
        if (res.ok) {
            const data = await res.json();
            document.getElementById('stats-section').classList.remove('hidden');
            
            document.getElementById('my-score').textContent = data.score || 0;
            document.getElementById('my-wins').textContent = data.wins || 0;
            document.getElementById('my-participations').textContent = data.lives_participated || 0;
            
            let accuracy = 0;
            if (data.boxes_checked > 0) {
                accuracy = Math.round((data.boxes_correct / data.boxes_checked) * 100);
            }
            document.getElementById('my-accuracy').textContent = accuracy;
            document.getElementById('accuracy-progress').style.width = accuracy + '%';
            
            const phrasesList = document.getElementById('top-phrases-list');
            phrasesList.innerHTML = '';
            if (data.top_phrases && data.top_phrases.length > 0) {
                data.top_phrases.forEach(p => {
                    const li = document.createElement('li');
                    li.textContent = `${p.phrase} (${p.count} fois)`;
                    phrasesList.appendChild(li);
                });
            } else {
                phrasesList.innerHTML = '<li>Aucune donnée pour le moment.</li>';
            }
        }
    } catch (e) {
        console.error('Erreur stats', e);
    }
}
"""

if old_load in content:
    content = content.replace(old_load, new_load)
    
    # Also inject loadUserStats into startGame
    content = content.replace('        loadLeaderboard();\n        syncState();', '        loadLeaderboard();\n        loadUserStats();\n        syncState();')
    
    with open('public/app.js', 'w') as f:
        f.write(content)
    print("Patched app.js")
else:
    print("Could not find loadLeaderboard in app.js")
