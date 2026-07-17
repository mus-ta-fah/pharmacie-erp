# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import date


class PharmacieVente(models.Model):
    _name = 'pharmacie.vente'
    _description = 'Vente au comptoir'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_vente desc'

    reference = fields.Char(string='Référence', copy=False, readonly=True, default='Nouveau')
    client_id = fields.Many2one(comodel_name='res.partner', string='Client')
    vendeur_id = fields.Many2one(
        comodel_name='res.users', string='Vendeur',
        required=True, default=lambda self: self.env.user, tracking=True,
    )
    ordonnance_id = fields.Many2one(
        comodel_name='pharmacie.ordonnance', string='Ordonnance', tracking=True,
    )
    ligne_ids = fields.One2many(
        comodel_name='pharmacie.vente.ligne', inverse_name='vente_id', string='Articles vendus',
    )
    montant_ht = fields.Float(
        string='Montant HT (FCFA)', compute='_compute_montants', store=True, digits=(10, 0),
    )
    tva = fields.Float(
        string='TVA (FCFA)', compute='_compute_montants', store=True, digits=(10, 0),
    )
    montant_ttc = fields.Float(
        string='Total TTC (FCFA)', compute='_compute_montants', store=True,
        digits=(10, 0), tracking=True,
    )

    @api.depends('ligne_ids.sous_total_ht', 'ligne_ids.montant_tva')
    def _compute_montants(self):
        for vente in self:
            vente.montant_ht = sum(vente.ligne_ids.mapped('sous_total_ht'))
            vente.tva = sum(vente.ligne_ids.mapped('montant_tva'))
            vente.montant_ttc = vente.montant_ht + vente.tva

    statut = fields.Selection(
        selection=[
            ('brouillon', 'Brouillon'),
            ('confirmee', 'Confirmée'),
            ('annulee', 'Annulée'),
        ],
        string='Statut', default='brouillon', tracking=True, readonly=True,
    )
    mode_paiement = fields.Selection(
        selection=[
            ('especes', 'Espèces'), ('carte', 'Carte bancaire'),
            ('wave', 'Wave'), ('orange_money', 'Orange Money'),
            ('free_money', 'Free Money'),
        ],
        string='Mode de paiement', required=True, default='especes',
    )
    date_vente = fields.Datetime(string='Date de vente', readonly=True)
    note = fields.Text(string='Observations')

    def action_confirmer(self):
        for vente in self:
            if vente.statut != 'brouillon':
                raise UserError('Seules les ventes en brouillon peuvent être confirmées.')
            if not vente.ligne_ids:
                raise UserError('Impossible de confirmer une vente sans articles.')

            # Vérification ordonnance
            for ligne in vente.ligne_ids:
                if ligne.medicament_id.sur_ordonnance and not vente.ordonnance_id:
                    raise ValidationError(
                        f'Le médicament "{ligne.medicament_id.nom_commercial}" '
                        f'nécessite une ordonnance. Veuillez en associer une.'
                    )

            # Décrémentation FEFO (First Expired First Out)
            for ligne in vente.ligne_ids:
                quantite_a_servir = ligne.quantite
                lots_valides = self.env['pharmacie.lot'].search(
                    [
                        ('medicament_id', '=', ligne.medicament_id.id),
                        ('statut', '=', 'valide'),
                        ('quantite_restante', '>', 0),
                        # Sécurité supplémentaire : on exclut tout lot dont la date
                        # de péremption est dépassée, même si son statut n'a pas
                        # encore été recalculé par le cron (_cron_update_statuts).
                        ('date_peremption', '>=', date.today()),
                    ],
                    order='date_peremption asc',
                )
                for lot in lots_valides:
                    if quantite_a_servir <= 0:
                        break
                    prise = min(lot.quantite_restante, quantite_a_servir)
                    lot.quantite_restante -= prise
                    quantite_a_servir -= prise
                    if lot.quantite_restante == 0:
                        lot.statut = 'epuise'

                if quantite_a_servir > 0:
                    raise ValidationError(
                        f'Stock insuffisant pour "{ligne.medicament_id.nom_commercial}". '
                        f'Il manque {quantite_a_servir} unité(s).'
                    )

            if vente.ordonnance_id:
                vente.ordonnance_id.write({'vente_id': vente.id, 'statut': 'complete'})

            vente.write({
                'statut': 'confirmee',
                'date_vente': fields.Datetime.now(),
                'reference': self.env['ir.sequence'].next_by_code('pharmacie.vente') or 'VTE/0001',
            })

    def action_annuler(self):
        for vente in self:
            if vente.statut == 'confirmee':
                raise UserError('Une vente confirmée ne peut pas être annulée directement.')
            vente.statut = 'annulee'

    def action_remettre_brouillon(self):
        for vente in self:
            if vente.statut == 'annulee':
                vente.statut = 'brouillon'

    def _compute_display_name(self):
        for vente in self:
            vente.display_name = (
                vente.reference if vente.reference != 'Nouveau' else 'Nouvelle vente'
            )


class PharmacieVenteLigne(models.Model):
    _name = 'pharmacie.vente.ligne'
    _description = 'Ligne de vente'

    vente_id = fields.Many2one(
        comodel_name='pharmacie.vente', string='Vente',
        required=True, ondelete='cascade',
    )
    medicament_id = fields.Many2one(
        comodel_name='pharmacie.medicament', string='Médicament', required=True,
    )
    quantite = fields.Integer(string='Quantité', required=True, default=1)
    prix_unitaire = fields.Float(string='Prix unitaire (FCFA)', required=True, digits=(10, 0))
    taux_tva = fields.Selection(related='medicament_id.taux_tva', string='TVA', store=True)

    sous_total_ht = fields.Float(
        string='Sous-total HT', compute='_compute_sous_total', store=True, digits=(10, 0),
    )
    montant_tva = fields.Float(
        string='Montant TVA', compute='_compute_sous_total', store=True, digits=(10, 0),
    )
    sous_total_ttc = fields.Float(
        string='Sous-total TTC', compute='_compute_sous_total', store=True, digits=(10, 0),
    )

    @api.depends('quantite', 'prix_unitaire', 'taux_tva')
    def _compute_sous_total(self):
        for ligne in self:
            ht = ligne.quantite * ligne.prix_unitaire
            tva_rate = float(ligne.taux_tva or '0') / 100
            ligne.sous_total_ht = ht
            ligne.montant_tva = ht * tva_rate
            ligne.sous_total_ttc = ht + ligne.montant_tva

    @api.onchange('medicament_id')
    def _onchange_medicament_id(self):
        if self.medicament_id:
            self.prix_unitaire = self.medicament_id.prix_vente

    @api.constrains('quantite')
    def _check_quantite(self):
        for ligne in self:
            if ligne.quantite <= 0:
                raise ValidationError('La quantité doit être supérieure à zéro.')
