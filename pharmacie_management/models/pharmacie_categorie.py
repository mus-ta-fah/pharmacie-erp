# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PharmacieCategorie(models.Model):
    _name = 'pharmacie.categorie'
    _description = 'Catégorie de médicament'
    _order = 'name asc'
    _parent_name = 'parent_id'
    _parent_store = True

    name = fields.Char(string='Nom de la catégorie', required=True)
    code = fields.Char(string='Code', size=10)
    description = fields.Text(string='Description')

    parent_id = fields.Many2one(
        comodel_name='pharmacie.categorie',
        string='Catégorie parente',
        ondelete='restrict',
        index=True,
    )
    child_ids = fields.One2many(
        comodel_name='pharmacie.categorie',
        inverse_name='parent_id',
        string='Sous-catégories',
    )
    parent_path = fields.Char(index=True)

    medicament_count = fields.Integer(
        string='Nb médicaments',
        compute='_compute_medicament_count',
    )

    @api.depends('child_ids')
    def _compute_medicament_count(self):
        for cat in self:
            cat.medicament_count = self.env['pharmacie.medicament'].search_count(
                [('categorie_id', '=', cat.id)]
            )

    # Odoo 18 : _compute_display_name() remplace name_get()
    def _compute_display_name(self):
        for cat in self:
            name = cat.name
            if cat.parent_id:
                name = f"{cat.parent_id.name} / {name}"
            cat.display_name = name
