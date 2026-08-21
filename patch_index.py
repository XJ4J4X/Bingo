with open('public/index.html', 'r') as f:
    content = f.read()

old_leaderboard = """        <section id="leaderboard-section">
            <h2>Classement</h2>
            <table id="leaderboard-table">
                <thead>
                    <tr>
                        <th>Rang</th>
                        <th>Pseudo</th>
                        <th>Score</th>
                    </tr>
                </thead>
                <tbody id="leaderboard-body">
                </tbody>
            </table>
        </section>"""

new_stats_and_leaderboard = """        <section id="stats-section" class="hidden">
            <h2>Statistiques</h2>
            <div class="stats-container">
                <div class="stat-card">
                    <h3>Mes Stats</h3>
                    <p><strong>Score Global:</strong> <span id="my-score">0</span> pts</p>
                    <p><strong>Victoires (Top 1):</strong> <span id="my-wins">0</span></p>
                    <p><strong>Participations:</strong> <span id="my-participations">0</span> lives</p>
                    <p><strong>Taux de Précision:</strong> <span id="my-accuracy">0</span>%</p>
                    <div class="progress-bar-container">
                        <div id="accuracy-progress" class="progress-bar" style="width: 0%;"></div>
                    </div>
                </div>
                <div class="stat-card">
                    <h3>Stats du Bingo</h3>
                    <p><strong>Top Phrases :</strong></p>
                    <ul id="top-phrases-list" style="text-align: left; margin: 0; padding-left: 20px; font-size: 0.9rem;">
                    </ul>
                </div>
            </div>
        </section>

        <section id="leaderboard-section">
            <h2>Classement</h2>
            <div class="leaderboard-tabs">
                <button id="btn-top-score" class="active">Top Points</button>
                <button id="btn-top-wins">Top Victoires</button>
            </div>
            <table id="leaderboard-table">
                <thead>
                    <tr>
                        <th>Rang</th>
                        <th>Pseudo</th>
                        <th id="leaderboard-value-header">Score</th>
                    </tr>
                </thead>
                <tbody id="leaderboard-body">
                </tbody>
            </table>
        </section>"""

if old_leaderboard in content:
    content = content.replace(old_leaderboard, new_stats_and_leaderboard)
    with open('public/index.html', 'w') as f:
        f.write(content)
    print("Patched index.html")
else:
    print("Could not find leaderboard section in index.html")
