# pharmacie_management — Module Odoo 18

Module de gestion de pharmacie développé pour le Master 2 DSGL
Université Alioune Diop de Bambey — CRD Dakar — Année 2025-2026

**Auteur :** Moustapha Mbaye
**Enseignant :** Youssoupha LAM — Unité ERP Odoo
**Dépôt :** https://github.com/mus-ta-fah/pharmacie-erp
**Rapport technique :** voir `RAPPORT_TECHNIQUE_pharmacie_management.docx` à la racine du dépôt

---

## Installation — via Docker (méthode recommandée, utilisée pour le développement et les tests)

Un fichier `docker-compose.yml` est fourni à la racine du dépôt (Odoo 18.0 + PostgreSQL 16).

```bash
docker compose up -d
```

Puis ouvrir **http://localhost:8069/web/database/manager** et créer une base (ex. `pharma_test`), en **décochant "Demo Data"** — le module fournit ses propres données de démonstration (voir plus bas).

Une fois la base créée, se connecter, aller dans **Apps**, retirer le filtre "Apps" par défaut, rechercher **pharmacie**, puis cliquer sur **Activer**.

## Installation — sans Docker (Odoo déjà installé localement)

1. Copier le dossier `pharmacie_management` dans le répertoire `addons` d'Odoo 18
2. Redémarrer le serveur Odoo
3. Aller dans **Réglages → Applications → Mettre à jour la liste des applications**
4. Rechercher "Pharmacie Management" et cliquer sur **Activer**

```bash
# Installation en ligne de commande
python odoo-bin -c odoo.conf -d ma_base -i pharmacie_management

# Mise à jour après modification du code
python odoo-bin -c odoo.conf -d ma_base -u pharmacie_management

# Mode développeur (recommandé pendant le développement)
python odoo-bin -c odoo.conf -d ma_base -u pharmacie_management --dev=reload,qweb
```

---

## Attribution des rôles à un utilisateur (important)

Les trois groupes de sécurité du module (Vendeur, Pharmacien, Gestionnaire) sont **indépendants** — aucun n'hérite des droits d'un autre (choix volontaire, voir section 10.2 du rapport technique : chaîner les groupes casserait l'isolation des ventes par vendeur pour les rôles Pharmacien/Gestionnaire).

Conséquence pratique : l'onglet "Droits d'accès" d'une fiche utilisateur n'affiche **pas** de menu déroulant simplifié pour la catégorie Pharmacie. Pour assigner un rôle :

1. Activer le **mode développeur** (Réglages → Général → Activer le mode développeur)
2. Ouvrir la fiche de l'utilisateur → onglet **Droits d'accès**
3. Dans la section **Pharmacie**, cocher la case correspondant au rôle voulu (Vendeur / Pharmacien / Gestionnaire — un seul suffit, ils ne sont pas cumulatifs par défaut)
4. Se déconnecter puis se reconnecter pour recharger la session

Sans cette étape, seuls les menus ne nécessitant aucun droit spécifique (ex. Fournisseurs, qui repose sur le modèle natif `res.partner`) resteront visibles.

---

## Structure du module

```
pharmacie_management/
├── __manifest__.py          # Déclaration du module
├── __init__.py
├── models/
│   ├── pharmacie_categorie.py   # Catégories de médicaments (hiérarchique)
│   ├── pharmacie_medicament.py  # Catalogue médicaments
│   ├── pharmacie_lot.py         # Lots et stocks (FEFO)
│   ├── pharmacie_vente.py       # Ventes au comptoir
│   ├── pharmacie_ordonnance.py  # Ordonnances médicales
│   ├── pharmacie_reappro.py     # Réapprovisionnement fournisseurs
│   └── res_partner_extend.py    # Extension fournisseurs pharmaceutiques
├── views/                   # Vues XML (form, list, kanban, search)
├── wizards/                 # Wizards (réappro auto, bilan de caisse)
├── report/                  # Rapports PDF QWeb
├── security/                # Groupes, ACL, record rules
└── data/                    # Séquences, tâche planifiée (cron), données de démo
```

---

## Groupes utilisateurs — matrice des droits

| Groupe       | Médicaments | Stocks | Ventes      | Ordonnances | Réappro          |
|--------------|-------------|--------|-------------|-------------|------------------|
| Vendeur      | Lecture     | Lecture| Créer/Lire  | Créer/Lire  | —                |
| Pharmacien   | CRUD        | CRUD   | CRUD        | CRUD        | Lecture seule    |
| Gestionnaire | CRUD        | CRUD   | CRUD        | CRUD        | CRUD complet     |

Une **record rule** additionnelle restreint un Vendeur aux seules ventes qu'il a lui-même créées ; Pharmacien et Gestionnaire voient l'ensemble des ventes de l'officine.

---

## Données de démonstration incluses

Chargées automatiquement à l'installation (`data/pharmacie_data.xml`) :

- **10 médicaments** (Doliprane, Amoxil, Coartem, Amlor, Advil, Vitascorbol, Flagyl, Mopral, Rubozinc, Ventoline), avec DCI, formes galéniques, TVA sénégalaise (0 %/18 %), statut ordonnance
- **3 fournisseurs pharmaceutiques** (Laborex Sénégal, Copharmed, Sodipharm), avec numéro d'agrément DPM
- **7 lots** de stock, avec dates de péremption variées pour démontrer les alertes (rouge < 30 jours, orange < 90 jours)
- **5 ventes confirmées** de démonstration
- Une **tâche planifiée** (`ir.cron`) quotidienne qui met à jour automatiquement le statut des lots expirés

---

## Tester rapidement le module

1. **Stock → Médicaments** : vue Kanban avec code couleur selon le niveau de stock
2. **Stock → Réapprovisionnement automatique** : génère des bons de commande pour les médicaments en alerte, regroupés par fournisseur
3. **Caisse → Nouvelle vente** : créer une vente, la confirmer (décrémentation automatique des lots selon l'algorithme FEFO), puis imprimer le ticket PDF
4. **Rapports → Bilan de caisse** : calculer le chiffre d'affaires sur une période

---

## Notes techniques

- Conforme aux standards Odoo 18 Community : balises `<list>` (et non `<tree>`, renommé en v18), expressions `invisible=`/`readonly=` directes (et non `attrs=`, supprimé en v18)
- Génération PDF via `wkhtmltopdf` (inclus dans l'image Docker officielle `odoo:18.0`)
- Le détail des difficultés rencontrées et de leur résolution (bugs de compatibilité Odoo 18, sécurité, wizards) est documenté dans le rapport technique joint