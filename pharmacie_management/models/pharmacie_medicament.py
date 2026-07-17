# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PharmacieMedicament(models.Model):
    _name = 'pharmacie.medicament'
    _description = 'Médicament'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'nom_commercial asc'

    # ── Identification ────────────────────────────────────────────────────
    nom_commercial = fields.Char(
        string='Nom commercial', required=True, tracking=True,
        help='Nom de marque déposée, ex : Amoxil®',
    )
    dci = fields.Char(
        string='DCI', required=True, tracking=True,
        help='Dénomination Commune Internationale, ex : Amoxicilline',
    )
    forme = fields.Selection(
        selection=[
            ('comprime', 'Comprimé'), ('sirop', 'Sirop'),
            ('injectable', 'Injectable'), ('suppositoire', 'Suppositoire'),
            ('creme', 'Crème'), ('gouttes', 'Gouttes'),
            ('pommade', 'Pommade'), ('gelule', 'Gélule'),
            ('patch', 'Patch'), ('autre', 'Autre'),
        ],
        string='Forme galénique', required=True,
    )
    dosage = fields.Char(string='Dosage', help='ex : 500 mg, 250 mg/5 mL')
    conditionnement = fields.Char(string='Conditionnement', help='ex : Boîte de 24, Flacon 100 mL')

    # ── Relations ─────────────────────────────────────────────────────────
    categorie_id = fields.Many2one(
        comodel_name='pharmacie.categorie',
        string='Catégorie thérapeutique', ondelete='set null',
    )
    fournisseur_id = fields.Many2one(
        comodel_name='res.partner',
        string='Fournisseur principal',
        domain=[('is_fournisseur_pharma', '=', True)],
    )

    # ── Prix & TVA ────────────────────────────────────────────────────────
    prix_achat = fields.Float(string='Prix achat (FCFA)', required=True, digits=(10, 0))
    prix_vente = fields.Float(string='Prix vente (FCFA)', required=True, digits=(10, 0), tracking=True)
    taux_tva = fields.Selection(
        selection=[('0', '0 % — Médicament essentiel'), ('18', '18 % — Autre médicament')],
        string='Taux TVA', required=True, default='0',
    )

    # ── Champs calculés ───────────────────────────────────────────────────
    marge_pct = fields.Float(
        string='Marge (%)', compute='_compute_marge_pct', store=True, digits=(5, 2),
    )

    @api.depends('prix_vente', 'prix_achat')
    def _compute_marge_pct(self):
        for med in self:
            med.marge_pct = (
                (med.prix_vente - med.prix_achat) / med.prix_achat * 100
                if med.prix_achat > 0 else 0.0
            )

    sur_ordonnance = fields.Boolean(
        string='Sur ordonnance', default=False, tracking=True,
    )
    alerte_rupture = fields.Integer(string='Seuil alerte rupture (unités)', default=10)

    lot_ids = fields.One2many(
        comodel_name='pharmacie.lot', inverse_name='medicament_id', string='Lots',
    )
    stock_actuel = fields.Integer(
        string='Stock actuel', compute='_compute_stock_actuel', store=True,
    )

    @api.depends('lot_ids.quantite_restante', 'lot_ids.statut')
    def _compute_stock_actuel(self):
        for med in self:
            lots_valides = med.lot_ids.filtered(lambda l: l.statut == 'valide')
            med.stock_actuel = sum(lots_valides.mapped('quantite_restante'))

    alerte_stock = fields.Selection(
        selection=[('ok', 'OK'), ('faible', 'Stock faible'), ('rupture', 'Rupture')],
        string='État du stock', compute='_compute_alerte_stock', store=True,
    )

    @api.depends('stock_actuel', 'alerte_rupture')
    def _compute_alerte_stock(self):
        for med in self:
            if med.stock_actuel <= 0:
                med.alerte_stock = 'rupture'
            elif med.stock_actuel <= med.alerte_rupture:
                med.alerte_stock = 'faible'
            else:
                med.alerte_stock = 'ok'

    notice = fields.Text(string='Notice / Posologie')
    photo = fields.Binary(string='Photo du produit', attachment=True)

    # ── Contraintes ───────────────────────────────────────────────────────
    @api.constrains('prix_achat', 'prix_vente')
    def _check_prix(self):
        for med in self:
            if med.prix_achat < 0:
                raise ValidationError('Le prix d\'achat ne peut pas être négatif.')
            if med.prix_vente < 0:
                raise ValidationError('Le prix de vente ne peut pas être négatif.')
            if med.prix_vente < med.prix_achat:
                raise ValidationError(
                    f'Le prix de vente ({med.prix_vente} FCFA) ne peut pas être '
                    f'inférieur au prix d\'achat ({med.prix_achat} FCFA).'
                )

    # Odoo 18 : _compute_display_name() remplace name_get()
    def _compute_display_name(self):
        for med in self:
            name = med.nom_commercial
            if med.dci:
                name += f' ({med.dci})'
            if med.dosage:
                name += f' — {med.dosage}'
            med.display_name = name
