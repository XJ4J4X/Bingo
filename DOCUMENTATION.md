# Documentation du Code - Aminato Bingo

Pour des raisons de sécurité, le code source du projet ne contient aucun commentaire. 
Ce document sert de manuel pour comprendre comment le code fonctionne si vous souhaitez le modifier.

## 1. Le Backend : `server.py`

Ce fichier est le cerveau de l'application. Il gère la base de données et répond aux requêtes du site.

*   **Lignes 1 à 8 :** Importation des outils de base de Python (serveur web, base de données SQLite, gestion du temps, etc.).
*   **PORT et DB_FILE :** Définissent le port (8080) sur lequel le site tourne et le nom du fichier de base de données (`database.sqlite`).
*   **WORDS :** Une liste de mots utilisés pour générer les mots de passe des joueurs (ex: "pomme-chaise-nuage").
*   **DEFAULT_PHRASES :** La liste des phrases de base qui apparaîtront dans les grilles de Bingo.
*   **game_state :** Une mémoire qui stocke l'état du chronomètre global pour que tous les joueurs soient synchronisés.
*   **Fonction `init_db()` :** 
    *   Crée les tables `users`, `phrases` et `admins` dans la base de données.
    *   La table `admins` possède une colonne `role` (superadmin ou admin). Le mot de passe par défaut (`AminatoAdmin2026!`) est inséré avec le rôle de `superadmin`.
*   **Fonction `check_admin()` :** Vérifie si le mot de passe fourni par le site web (dans les requêtes) correspond bien à un mot de passe stocké dans la table `admins`.
*   **`MyRequestHandler` :** C'est le serveur web en lui-même.
    *   `do_GET` : Gère les demandes de lecture (ex: récupérer le classement avec `/api/leaderboard`, les phrases, ou l'état du timer).
    *   `do_POST` : Gère les envois de données (inscription, connexion, etc.). Contient des routes spécifiques `/api/admin/list_admins` et `/api/admin/delete_admin` accessibles uniquement si le rôle est `superadmin`.

## 2. Le Frontend Joueur : `public/index.html` et `public/app.js`

*   **`index.html` :** Contient la structure de la page. 
    *   Il y a trois grandes sections : `#auth-section` (pour se connecter), `#game-section` (la grille de jeu) et `#leaderboard-section` (le classement).
    *   La classe CSS `hidden` est très importante : elle permet de cacher ou d'afficher ces sections selon si le joueur est connecté ou non.
*   **`app.js` :** C'est la logique côté navigateur.
    *   Il écoute les clics sur les boutons (ex: `loginBtn.addEventListener`).
    *   `fetchPhrases()` : Demande les phrases au serveur.
    *   `generateGrid()` : Mélange les phrases et crée 16 cases HTML (`div`).
    *   `syncState()` : Cette fonction est appelée toutes les secondes. Elle demande au serveur "Où en est le chrono ?". Si le chrono est à zéro, elle bloque la grille.
    *   `validateGridBtn` : Quand cliqué, compte le nombre de cases cochées, multiplie par 10, et envoie le score au serveur.

## 3. Le Panel Admin : `public/admin.html` et `public/admin.js`

*   **`admin.html` :** L'interface d'administration. Elle contient plusieurs "boîtes" (`.admin-controls`). La boîte `#superadmin-section` (Gestion de l'équipe) est cachée par défaut.
*   **`admin.js` :**
    *   Lors de la connexion, le serveur renvoie le rôle. Si le rôle est `superadmin`, le Javascript affiche la section de gestion d'équipe.
    *   Il utilise une fonction spéciale `fetchWithAuth()` qui ajoute automatiquement le mot de passe admin à chaque requête.
    *   `loadAdmins()` : Réservée au superadmin, elle liste les autres administrateurs et permet de les supprimer.

## 4. Le Design : `public/style.css`

*   Il gère l'apparence visuelle. Le design a été pensé pour être minimaliste.
*   La classe `.hidden { display: none !important; }` est la clé de voûte de la navigation (elle masque les écrans inactifs).
*   La grille de Bingo utilise `display: grid` avec `grid-template-columns: repeat(4, 1fr)` pour créer 4 colonnes. Sur téléphone (écran < 600px), cela passe à 2 colonnes grâce à `@media (max-width: 600px)`.
*   Les couleurs et les effets de survol (`:hover`) sont définis ici pour donner un côté interactif simple sans surcharger le navigateur.
