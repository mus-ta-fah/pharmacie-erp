# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PharmacieOrdonnance(models.Model):
    _name = 'pharmacie.ordonnance'
    _description = 'Ordonnance médicale'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_prescription desc'

    patient_nom = fields.Char(string='Nom du patient', required=True, tracking=True)
    patient_age = fields.Integer(string='Âge du patient')
    patient_genre = fields.Selection(
        selection=[('m', 'Masculin'), ('f', 'Féminin')], string='Genre',
    )
    medecin_nom = fields.Char(string='Médecin prescripteur', required=True)
    structure_sante = fields.Char(string='Structure de santé')
    date_prescription = fields.Date(
        string='Date de prescription', required=True, default=fields.Date.today,
    )
    medicament_ids = fields.Many2many(
        comodel_name='pharmacie.medicament',
        relation='pharmacie_ordonnance_medicament_rel',
        column1='ordonnance_id', column2='medicament_id',
        string='Médicaments prescrits',
    )
    posologie_ids = fields.One2many(
        comodel_name='pharmacie.posologie',
        inverse_name='ordonnance_id', string='Détail posologique',
    )
    statut = fields.Selection(
        selection=[
            ('attente', 'En attente'),
            ('partielle', 'Délivrée partiellement'),
            ('complete', 'Délivrée complètement'),
        ],
        string='Statut', default='attente', tracking=True,
    )
    vente_id = fields.Many2one(
        comodel_name='pharmacie.vente', string='Vente associée', readonly=True,
    )
    scan_ordonnance = fields.Binary(string='Scan / Photo de l\'ordonnance', attachment=True)
    notes = fields.Text(string='Notes internes')

    @api.constrains('date_prescription')
    def _check_date_prescription(self):
        for ordo in self:
            if ordo.date_prescription and ordo.date_prescription > fields.Date.today():
                raise ValidationError(
                    'La date de prescription ne peut pas être dans le futur.'
                )

    def _compute_display_name(self):
        for ordo in self:
            ordo.display_name = f'Ordo. {ordo.patient_nom} — {ordo.date_prescription}'


class PharmaciePosologie(models.Model):
    _name = 'pharmacie.posologie'
    _description = 'Posologie'

    ordonnance_id = fields.Many2one(
        comodel_name='pharmacie.ordonnance', string='Ordonnance',
        required=True, ondelete='cascade',
    )
    medicament_id = fields.Many2one(
        comodel_name='pharmacie.medicament', string='Médicament', required=True,
    )
    posologie = fields.Char(
        string='Posologie', required=True,
        help='ex : 1 comprimé matin et soir pendant 7 jours',
    )
    duree_jours = fields.Integer(string='Durée (jours)')
    quantite_prescrite = fields.Integer(string='Quantité prescrite')
