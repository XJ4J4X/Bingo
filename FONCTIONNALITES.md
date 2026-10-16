# 🎯 Aminato Bingo - Présentation & Fonctionnalités

Document synthétique présentant les technologies utilisées, l'architecture globale et l'ensemble des fonctionnalités de l'application **Aminato Bingo**.

---

## 🛠️ 1. Technologies Utilisées

L'application a été conçue pour être **ultra-légère**, **rapide à charger**, sans dépendances lourdes ni compilation :

- **Backend (Serveur)** :
  - **Python 3** avec le module standard `http.server` et `socketserver` (aucun framework lourd, zéro latence au démarrage).
  - **Base de données hybride** :
    - En local : **SQLite 3** (`database.sqlite`).
    - En production (Render/Cloud) : **PostgreSQL** hébergé sur **Neon** via `psycopg2`.
  - **Cache RAM anti-spam** : mise en mémoire tampon des requêtes fréquentes (classements, liste des joueurs) pour réduire à zéro les coûts de requêtes SQL sur le cloud.

- **Frontend (Interface Web)** :
  - **HTML5 & CSS3** personnalisé (design rétro et moderne avec thème tableau à la craie, mode sombre et animations fluides).
  - **JavaScript Vanilla (ES6+)** : aucun framework (zéro React/Vue), chargement instantané même sur mobile ou connexion 4G.
  - **HTML5 Canvas 2D/3D** pour le moteur physique de la Roue de la fortune.

- **Streaming & OBS Studio** :
  - **Sources Navigateur OBS (Overlays)** transparentes avec rafraîchissement en direct.
  - **Docks personnalisés OBS** intégrables directement dans les fenêtres d'OBS Studio pour le streamer et son équipe de modération.

---

## 🔄 2. Comment ça marche ? (Cycle d'une partie de Bingo)

Une session de Bingo se déroule en plusieurs étapes simples et automatisées :

1. **Avant le live** : L'équipe d'administration prépare les phrases (ex: *"Aminato rage sur un jeu"*, *"Let's go !"*) manuellement ou en chargeant un profil prédéfini (profil Horreur, profil Minecraft, etc. via fichier CSV).
2. **Lancement du Live** : L'administrateur lance le chrono (ex: 30 minutes de jeu + 5 minutes de vérification). L'application peut être lancée en **Mode Normal** ou en **Mode Test** (aucun impact sur les scores ni les streaks).
3. **Pendant le Live (Joueurs)** : Les spectateurs se connectent avec leur pseudo, reçoivent une grille personnalisée de 16 cases mélangées et cochent les événements au fur et à mesure qu'Aminato les réalise en live.
4. **Fin du temps de jeu & Verrouillage** : Dès que le chrono de jeu tombe à zéro, les grilles des joueurs sont verrouillées. L'admin peut déclencher une session **Retardataires** de 5 minutes si besoin.
5. **Compte à rebours de vérification & Validation automatique** : Durant la phase de vérification, le décompte final s'affiche. Dès qu'il atteint zéro, le serveur valide automatiquement les choix et crédite les points instantanément.
6. **Mise à jour des scores & Streaks** : Le classement du live désigne le vainqueur (+1 Victoire). Les séries de participations consécutives (streaks) sont automatiquement incrémentées.

---

## 📱 3. Espace Joueurs (`/`)

- **Connexion rapide** : Inscription par simple pseudo. Un mot de passe mnémotechnique de 3 mots (ex: `pomme-chaise-soleil`) est généré pour sécuriser le compte sans formulaire complexe.
- **Grille de 16 cases interactive** : Grille 4x4 réactive sur ordinateur et smartphone, avec son de validation ("Ting !") et sauvegarde locale automatique en cas de rechargement de page.
- **Personnalisation Cosmétique** :
  - **Couleur personnalisée** : Roue chromatique permettant aux joueurs autorisés par les modos de teinter leur pseudo sur tout le site.
  - **Choix de la police** : Possibilité de personnaliser la typographie de son profil.
- **Statistiques Personnelles** : Taux de précision, nombre de parties jouées, victoires accumulées, streak actuel et record de streak.
- **Classements Multi-onglets** :
  - **Classement Général** (Top points historiques).
  - **Classement des Victoires** (Nombre de victoires de lives).
  - **Classement du Live en cours** (Remis à zéro à chaque nouvelle session).
  - **Liste des Joueurs Inscrits** en direct.

---

## 🛡️ 4. Espace Administration & Modération (`/admin.html`)

- **Sécurité & Rôles** : Accès protégé par mot de passe avec distinction entre **Superadmin** (maître du jeu) et **Admins/Modérateurs**.
- **Gestion du Direct** :
  - Lancement, mise en pause et arrêt du live.
  - Configuration du temps de jeu et du temps de vérification.
  - **🧪 Mode Test** : Option permettant de tester toutes les fonctionnalités en direct sans toucher aux streaks, aux points réels ni aux victoires des spectateurs.
  - **⏰ Session Retardataires (5 min)** : Bouton d'urgence pour accorder un délai aux retardataires.
- **Gestion des Phrases & Profils** :
  - Ajout, modification et suppression de phrases unitaires.
  - **Importation en masse par CSV** avec prévisualisation des colonnes avant validation.
  - Bibliothèque de profils thématiques (Horreur, Multijoueur, Chill, etc.).
- **Gestion des Joueurs** :
  - Recherche et filtrage des utilisateurs inscrits.
  - Attribution ou retrait manuel de points.
  - Bouton 🎨 pour autoriser un joueur à choisir sa couleur personnalisée.
- **Gestion de l'Équipe & Sauvegardes** :
  - Création et révocation des mots de passe des modérateurs.
  - **Export de sauvegarde BDD** en un clic au format JSON complet.

---

## 📺 5. Outils Dédiés au Streaming & OBS

L'application intègre 4 outils spécialement taillés pour la diffusion en direct sur Twitch / YouTube :

### 1. 🎬 Grille de Présentation Live (Overlay Stream) - `obs_presentation.html`
- **Affichage & Incrustation OBS** : Affiche les 16 cases du Bingo du jour avec une typographie nette, contrastée et plusieurs modes d'arrière-plan :
  - **🟢 Mode Fond Vert (Green Screen / Chroma Key)** : `?bg=green` (fond vert pur `#00FF00` avec cartes et badges opaques pour découpe chrominance parfaite dans OBS).
  - **✨ Mode Transparent (Alpha OBS direct)** : `?bg=transparent` (fond 100% transparent natif pour incrustation caméra).
  - **🌙 Mode Sombre / Glassmorphism** : `?bg=dark` (pour intégration sur écran ou retour plateau).
- **Validation 100% Visuelle** : Quand une case est validée, elle s'illumine avec un badge tamponné `VALIDÉ ✓`. **Cette validation est purement visuelle et n'a aucun impact sur les scores ni le jeu réel des spectateurs.**

### 2. 🎯 Contrôleur de Présentation Sécurisé - `obs_presentation_control.html`
- **Rôle** : Panneau réservé au modérateur ou au régisseur pour piloter l'overlay d'Aminato en temps réel.
- **Sécurité** : Protégé par mot de passe modérateur/administrateur.
- **Fonctionnement** : Grille interactive de 16 boutons permettant de cocher ou décocher une case en un clic depuis un téléphone, une tablette ou un dock OBS. Bouton "Tout décocher" inclus.

### 3. 🕹️ Dock OBS Streamer - `obs.html`
- Panneau compact intégrable dans OBS Studio (`Afficher -> Docks -> Docks personnalisés`).
- Affiche le statut du live, le chrono en cours, le chrono retardataires, le nombre de grilles soumises, et le bouton pour lancer les 5 minutes retardataires.

### 4. 📋 Dock OBS Validations en Direct - `validations.html`
- Panneau OBS dédié pour voir en temps réel qui soumet sa grille, l'ordre d'arrivée (🥇, 🥈, 🥉) et les tags direct/retard.

### 5. 🎡 La Roue de la Fortune - `roue.html`
- Roue animée en Canvas pour les tirages au sort en direct.
- Bouton **Mode Fond Vert (Chroma Key)** pour supprimer l'interface et ne garder que la roue sur fond vert pur (`#00FF00`) dans OBS.
