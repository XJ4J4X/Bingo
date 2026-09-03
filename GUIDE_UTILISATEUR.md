# 📘 Guide Complet : AminatoBingo

Ce document explique le fonctionnement de chaque partie du site, que ce soit pour les joueurs, les streamers, ou les administrateurs.

---

## 1️⃣ Espace Joueur (`/`)

C'est l'interface principale accessible à tout le monde.

### Connexion et Profil
- **Inscription simple** : Les joueurs entrent simplement un pseudo. Aucune gestion de mot de passe compliquée n'est nécessaire.
- **Sauvegarde locale** : Le navigateur se souvient du joueur. S'il ferme l'onglet et revient plus tard, il est directement reconnecté.
- **Couleur Personnalisée** : Lorsqu'un administrateur donne l'accès, le joueur peut choisir sa propre couleur via une roue des couleurs qui s'affiche à l'écran. La couleur s'applique sur son pseudo partout sur le site.

### Les Onglets Joueur
- **Jeu (La Grille)** : Affiche la grille de 16 cases. Les joueurs cliquent pour cocher/décocher. Attention : la case n'est validée officiellement que si l'administrateur la coche de son côté.
- **Statistiques** : Affiche les performances globales du joueur (taux de précision, parties jouées, victoires accumulées).
- **Joueurs Inscrits** : Liste en direct tous les utilisateurs connectés et inscrits sur le site.

### Le Classement Multi-onglets
- **Top Points** : Classement historique de tous les points accumulés.
- **Top Victoires** : Classement de ceux qui ont gagné le plus de sessions (lives).
- **Points du Live** : Classement temporaire de la partie en cours, remis à zéro à chaque nouveau live.

---

## 2️⃣ Espace Administrateur (`/admin.html`)

Panneau de contrôle protégé par mot de passe, conçu pour le streamer ou les modérateurs.

### Gestion du "Live" (La Partie)
- **Démarrer un Live** : Envoie une nouvelle grille vierge à tout le monde. L'admin peut choisir de générer une grille totalement aléatoire, ou bien d'utiliser un **Profil de Grille** spécifique (ex: Profil "Horreur").
- **Valider les cases** : Pendant le live, l'admin coche les phrases qui se réalisent. Cela donne instantanément les points aux joueurs qui ont coché la bonne case.
- **Arrêter le Live** : Verrouille les grilles, arrête les points, et **ajoute +1 Victoire** au joueur qui a le plus de points dans le classement du Live actuel.

### Gestion des Phrases & Profils
- **Création unitaire** : Permet d'ajouter une phrase aléatoire dans la grosse base de données globale.
- **Profils de Grille (Bulk Import)** : L'admin peut créer des "sets" de 16 phrases (des profils) pour des jeux spécifiques.
  - *Modification* : Édition rapide en un clic (bouton jaune).
  - *Import CSV* : Possibilité d'importer un fichier CSV (ligne par ligne) pour créer des dizaines de profils d'un seul coup. Le site affiche une **prévisualisation détaillée** avant de valider.

### Statistiques & Comptes
- **Statistiques Globales** : Affiche les courbes et barres de progression des meilleurs joueurs et des **phrases qui arrivent le plus souvent**.
- **Gestion des joueurs** : Permet de voir tous les inscrits, de leur donner l'autorisation de choisir leur couleur personnalisée (bouton 🎨), ou d'ajouter/retirer des points manuellement.
- **Comptes Admins (Superadmin)** : Si connecté avec le mot de passe maître, possibilité de créer ou supprimer des mots de passe pour les modérateurs.
- **Backup BDD** : Bouton d'export pour télécharger l'intégralité de la base de données au format JSON en cas de besoin de sauvegarde.

---

## 3️⃣ La Roue de la Fortune (`/roue.html`)

Une page indépendante, idéale pour le streaming.

- **Fonctionnement** : Génère une roue 3D en Canvas qui tourne de manière fluide. Les noms/phrases sur la roue sont modifiables directement sur la page.
- **Mode Fond Vert (OBS)** : Un bouton dédié permet de cacher toute l'interface (menus, ombres, bordures) et de peindre le fond en vert pur (`#00FF00`) pour une intégration parfaite dans OBS via un filtre de chrominance.
- **Affichage propre** : Une fois la roue arrêtée, seul le texte gagnant s'affiche au milieu de l'écran, pour un rendu propre à la caméra.

---

## 4️⃣ Easter Eggs et Spécificités

Certains joueurs ont un affichage unique et forcé par le système, peu importe leur personnalisation :
- **Aminat0_** : Toujours affiché avec une animation CSS spéciale bleue "fantomatique" clignotante (`.aminato-effect`).
- **J4X** : Le pseudo "J4X" clignote en rouge agressif sur tous les classements et grilles du site.

---
*Généré pour la v1.0.0.30.*
