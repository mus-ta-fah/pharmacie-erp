# -*- coding: utf-8 -*-
from odoo import models, fields


class ResPartnerExtend(models.Model):
    """Héritage de res.partner pour les fournisseurs pharmaceutiques."""
    _inherit = 'res.partner'

    is_fournisseur_pharma = fields.Boolean(
        string='Fournisseur pharmaceutique',
        default=False,
        help='Distingue les grossistes/laboratoires des autres partenaires',
    )
    delai_livraison_moyen = fields.Integer(
        string='Délai de livraison moyen (jours)',
        default=7,
    )
    numero_agrement = fields.Char(
        string='N° agrément DPM',
        help='Numéro d\'agrément Direction de la Pharmacie et du Médicament',
    )
