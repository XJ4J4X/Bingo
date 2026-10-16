# 📋 Journal des modifications (Changelog)

Toutes les modifications notables apportées au projet **Aminato Bingo** sont consignées dans ce document.

---

## [2.6.0] - 2026-10-16

### ✨ Nouveautés
- **Overlay OBS de Présentation Streamer (`obs_presentation.html`)** :
  - Grille de 16 cases 100% scalable et responsive (unités `vmin`), sans titre ni bordure, optimisée pour un affichage plein écran derrière Aminato.
  - Mode fond transparent natif (`?bg=transparent`) avec cases subtilement grisées et translucides (`backdrop-filter`) pour s'intégrer élégamment à la caméra.
  - Mode Fond Vert Chroma Key (`?bg=green`) pour intégration propre sur fond `#00FF00`.
  - Badge discret `✓ Validé` vert émeraude au coin des cases validées.
  - Carillon doux généré par synthétiseur Web Audio procédural (avec fallback `ting.mp3`) lors de chaque validation.
- **Panneau de Contrôle Modérateur (`obs_presentation_control.html`)** :
  - Interface dédiée pour la régie reprenant fidèlement la charte graphique officielle du site (en-tête bleu nuit, typographie Didact Gothic, cartes interactives).
  - Authentification sécurisée par mot de passe modérateur/administrateur avec mémorisation locale et support de l'auto-connexion via `?key=...`.
  - Validation purement visuelle : aucun impact sur la base de données, les points des spectateurs, les victoires ni les séries (streaks).
  - Synchronisation automatique avec la grille du live officiel en cours (compatible en mode normal comme en mode test).
  - Boutons de copie rapide des URLs OBS et bouton de réinitialisation rapide ("Tout décocher").
- **Routage & Liens courts** :
  - Ajout des alias `/presentation` et `/presentation_control` (ou `/control`) côté serveur pour un accès direct et simplifié.

### 📚 Documentation
- Ajout du document de synthèse `FONCTIONNALITES.md` détaillant les technologies, le cycle de jeu et l'ensemble des modules.
- Mise à jour du `GUIDE_UTILISATEUR.md` pour intégrer la présentation live.

---

## [2.5.0] - 2026-10-02

### ✨ Nouveautés
- Mode Test complet sans impact sur les statistiques, victoires ou streaks des spectateurs.
- Dock OBS streamer compact (`obs.html`) avec contrôle du timer et session retardataires (5 min).
- Tableau des validations en direct pour les administrateurs (`validations.html`).
- Validation automatique des grilles à la fin du compte à rebours de vérification.

---

## [2.4.1] - 2026-09-27

### ⚡ Optimisations & BDD
- Système anti-spam de requêtes SQL avec mise en cache RAM pour préserver les quotas Neon / PostgreSQL.
- Fiabilisation du calcul des streaks et de l'historique des participations aux lives.
- Ajout du Hall of Fame et support de l'import de profils de grilles par fichier CSV.
