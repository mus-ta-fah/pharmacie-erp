# pharmacie_management — Module Odoo 18

Module de gestion de pharmacie développé pour le Master 2 DSGL  
Université Alioune DIOP de Bambey — CRD Dakar — 2025-2026

---

## Installation

1. Copier le dossier `pharmacie_management` dans le répertoire `addons` d'Odoo 18
2. Redémarrer le serveur Odoo
3. Aller dans **Paramètres → Applications → Mettre à jour la liste des applications**
4. Rechercher "Pharmacie Management" et cliquer sur **Installer**

```bash
# Installation en ligne de commande
python odoo-bin -c odoo.conf -d ma_base -i pharmacie_management

# Mise à jour après modification
python odoo-bin -c odoo.conf -d ma_base -u pharmacie_management

# Mode développeur (recommandé pendant le développement)
python odoo-bin -c odoo.conf -d ma_base -u pharmacie_management --dev=reload,qweb
```

---

## Structure du module

```
pharmacie_management/
├── __manifest__.py          # Déclaration du module
├── __init__.py
├── models/
│   ├── pharmacie_categorie.py   # Catégories de médicaments (hiérarchique)
│   ├── pharmacie_medicament.py  # Catalogue médicaments
│   ├── pharmacie_lot.py         # Lots et stocks
│   ├── pharmacie_vente.py       # Ventes au comptoir
│   ├── pharmacie_ordonnance.py  # Ordonnances médicales
│   ├── pharmacie_reappro.py     # Réapprovisionnement fournisseurs
│   └── res_partner_extend.py    # Extension fournisseurs pharmaceutiques
├── views/                   # Vues XML (form, tree, kanban, search)
├── wizards/                 # Wizards (réappro auto, bilan de caisse)
├── report/                  # Rapports PDF QWeb
├── security/                # Groupes, ACL, record rules
└── data/                    # Séquences et données de démo
```

---

## Groupes utilisateurs

| Groupe       | Médicaments | Stocks | Ventes      | Ordonnances | Réappro  |
|-------------|-------------|--------|-------------|-------------|----------|
| Vendeur      | Lecture     | Lecture| Créer/Lire  | Créer/Lire  | —        |
| Pharmacien   | CRUD        | CRUD   | CRUD        | CRUD        | Lecture  |
| Gestionnaire | CRUD        | CRUD   | CRUD        | CRUD        | CRUD     |

---

## Données de test incluses

- 6 catégories de médicaments (avec hiérarchie)
- Séquences automatiques pour lots, ventes et bons de commande
