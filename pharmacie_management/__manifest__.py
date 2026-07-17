# -*- coding: utf-8 -*-
{
    'name': 'Pharmacie Management',
    'version': '18.0.1.0.0',
    'category': 'Health',
    'summary': 'Module de gestion complète d\'une pharmacie sénégalaise',
    'description': '''
        Module Odoo 18 — Gestion de Pharmacie
        ======================================
        Développé dans le cadre du Master 2 DSGL — Université Alioune DIOP de Bambey
        CRD Dakar — Année 2025-2026

        Fonctionnalités :

        - Catalogue de médicaments (DCI, formes, TVA sénégalaise)
        - Gestion des lots et alertes de péremption
        - Ventes au comptoir avec ou sans ordonnance
        - Réapprovisionnement fournisseurs
        - Rapports PDF QWeb professionnels
        - Gestion des droits par profil (Vendeur, Pharmacien, Gestionnaire)
    ''',
    'author': 'Moustapha Mbaye',
    'website': 'https://mustafah.dev',
    'depends': ['base', 'mail'],
    'data': [
        # 1. Sécurité en premier (toujours)
        'security/pharmacie_security.xml',
        'security/ir.model.access.csv',

        # 2. Données initiales (séquences, données de démo)
        'data/pharmacie_data.xml',

        # 3. Actions de rapports (déclarées avant les vues car
        #    le bouton "Imprimer ticket" de la vue vente référence
        #    action_report_ticket_caisse par son external ID)
        'report/report_actions.xml',
        'report/report_ticket_caisse.xml',
        'report/report_inventaire.xml',
        'report/report_bilan_caisse.xml',
        'report/report_bon_commande.xml',

        # 4. Vues
        'views/pharmacie_medicament_views.xml',
        'views/pharmacie_lot_views.xml',
        'views/pharmacie_vente_views.xml',
        'views/pharmacie_ordonnance_views.xml',
        'views/pharmacie_reappro_views.xml',

        # 5. Wizards
        'wizards/wizard_reappro_auto_views.xml',
        'wizards/wizard_bilan_caisse_views.xml',

        # 6. Menus en dernier (référencent les actions)
        'views/pharmacie_menu.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
