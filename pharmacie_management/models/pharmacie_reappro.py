# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class PharmacieReappro(models.Model):
    _name = 'pharmacie.reappro'
    _description = 'Bon de commande fournisseur'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_commande desc'

    reference = fields.Char(string='Référence', copy=False, readonly=True, default='Nouveau')
    fournisseur_id = fields.Many2one(
        comodel_name='res.partner', string='Fournisseur', required=True,
        domain=[('is_fournisseur_pharma', '=', True)], tracking=True,
    )
    date_commande = fields.Date(string='Date de commande', required=True, default=fields.Date.today)
    date_livraison_prevue = fields.Date(string='Date de livraison prévue')
    ligne_ids = fields.One2many(
        comodel_name='pharmacie.reappro.ligne',
        inverse_name='reappro_id', string='Médicaments commandés',
    )
    montant_total = fields.Float(
        string='Montant total (FCFA)', compute='_compute_montant_total',
        store=True, digits=(10, 0),
    )

    @api.depends('ligne_ids.sous_total')
    def _compute_montant_total(self):
        for reappro in self:
            reappro.montant_total = sum(reappro.ligne_ids.mapped('sous_total'))

    statut = fields.Selection(
        selection=[
            ('brouillon', 'Brouillon'), ('commande', 'Commandé'),
            ('partiel', 'Reçu partiellement'), ('recu', 'Reçu'),
            ('annulee', 'Annulée'),
        ],
        string='Statut', default='brouillon', tracking=True, readonly=True,
    )
    note_interne = fields.Text(string='Note interne')

    def action_envoyer_commande(self):
        for reappro in self:
            if reappro.statut != 'brouillon':
                raise UserError('Seuls les bons en brouillon peuvent être envoyés.')
            if not reappro.ligne_ids:
                raise UserError('Impossible de commander un bon sans médicaments.')
            reappro.write({
                'statut': 'commande',
                'reference': self.env['ir.sequence'].next_by_code('pharmacie.reappro') or 'BC/0001',
            })
            reappro.message_post(
                body=f'Bon de commande {reappro.reference} envoyé au fournisseur '
                     f'{reappro.fournisseur_id.name}.'
            )

    def action_annuler(self):
        for reappro in self:
            if reappro.statut != 'brouillon':
                raise UserError('Seuls les bons en brouillon peuvent être annulés.')
            reappro.statut = 'annulee'

    def action_receptionner(self):
        for reappro in self:
            if reappro.statut not in ('commande', 'partiel'):
                raise UserError('Seuls les bons commandés peuvent être réceptionnés.')
            if not reappro.ligne_ids:
                raise UserError('Ce bon ne contient aucune ligne.')

            for ligne in reappro.ligne_ids:
                if ligne.quantite_recue <= 0:
                    continue
                self.env['pharmacie.lot'].create({
                    'medicament_id': ligne.medicament_id.id,
                    'date_peremption': ligne.date_peremption,
                    'date_fabrication': ligne.date_fabrication,
                    'quantite_initiale': ligne.quantite_recue,
                    'quantite_restante': ligne.quantite_recue,
                    'prix_achat_lot': ligne.prix_unitaire,
                    'reappro_id': reappro.id,
                    'statut': 'valide',
                })

            total_commande = sum(reappro.ligne_ids.mapped('quantite_commandee'))
            total_recu = sum(reappro.ligne_ids.mapped('quantite_recue'))
            reappro.statut = 'recu' if total_recu >= total_commande else 'partiel'
            reappro.message_post(
                body=f'Réception : {total_recu}/{total_commande} unités reçues.'
            )

    def _compute_display_name(self):
        for r in self:
            name = r.reference if r.reference != 'Nouveau' else 'Nouveau BC'
            if r.fournisseur_id:
                name += f' — {r.fournisseur_id.name}'
            r.display_name = name


class PharmacieReapproLigne(models.Model):
    _name = 'pharmacie.reappro.ligne'
    _description = 'Ligne de bon de commande'

    reappro_id = fields.Many2one(
        comodel_name='pharmacie.reappro', string='Bon de commande',
        required=True, ondelete='cascade',
    )
    medicament_id = fields.Many2one(
        comodel_name='pharmacie.medicament', string='Médicament', required=True,
    )
    quantite_commandee = fields.Integer(string='Qté commandée', required=True, default=1)
    quantite_recue = fields.Integer(string='Qté reçue', default=0)
    prix_unitaire = fields.Float(string='Prix unitaire (FCFA)', digits=(10, 0))
    sous_total = fields.Float(
        string='Sous-total (FCFA)', compute='_compute_sous_total', store=True, digits=(10, 0),
    )
    date_fabrication = fields.Date(string='Date fabrication lot')
    date_peremption = fields.Date(string='Date péremption lot', required=True)

    @api.depends('quantite_commandee', 'prix_unitaire')
    def _compute_sous_total(self):
        for ligne in self:
            ligne.sous_total = ligne.quantite_commandee * ligne.prix_unitaire

    @api.onchange('medicament_id')
    def _onchange_medicament_id(self):
        if self.medicament_id:
            self.prix_unitaire = self.medicament_id.prix_achat

    @api.constrains('quantite_commandee')
    def _check_quantite(self):
        for ligne in self:
            if ligne.quantite_commandee <= 0:
                raise ValidationError('La quantité commandée doit être supérieure à zéro.')

    @api.constrains('quantite_recue', 'quantite_commandee')
    def _check_quantite_recue(self):
        for ligne in self:
            if ligne.quantite_recue < 0:
                raise ValidationError('La quantité reçue ne peut pas être négative.')
            if ligne.quantite_recue > ligne.quantite_commandee:
                raise ValidationError(
                    'La quantité reçue ne peut pas dépasser la quantité commandée.'
                )
