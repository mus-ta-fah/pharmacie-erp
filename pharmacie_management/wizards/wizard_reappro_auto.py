# -*- coding: utf-8 -*-
from odoo import models, fields, api


class WizardReapproAutoLigne(models.TransientModel):
    _name = 'wizard.reappro.auto.ligne'
    _description = 'Ligne de réapprovisionnement automatique'

    wizard_id = fields.Many2one('wizard.reappro.auto', ondelete='cascade')
    medicament_id = fields.Many2one('pharmacie.medicament', string='Médicament', readonly=True)
    fournisseur_id = fields.Many2one('res.partner', string='Fournisseur', readonly=True)
    stock_actuel = fields.Integer(string='Stock actuel', readonly=True)
    alerte_rupture = fields.Integer(string='Seuil alerte', readonly=True)
    quantite_suggeree = fields.Integer(string='Qté suggérée')
    selectionne = fields.Boolean(string='Inclure', default=True)


class WizardReapproAuto(models.TransientModel):
    _name = 'wizard.reappro.auto'
    _description = 'Réapprovisionnement automatique'

    ligne_ids = fields.One2many(
        'wizard.reappro.auto.ligne', 'wizard_id', string='Médicaments en alerte',
    )
    nb_alertes = fields.Integer(string='Nb médicaments en alerte', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record._charger_alertes()
        return records

    def _charger_alertes(self):
        """Scanne automatiquement les médicaments en alerte ou rupture."""
        meds_en_alerte = self.env['pharmacie.medicament'].search(
            [('alerte_stock', 'in', ['faible', 'rupture'])]
        )
        lignes = []
        for med in meds_en_alerte:
            quantite_suggeree = max(med.alerte_rupture * 2, 10)
            lignes.append((0, 0, {
                'medicament_id': med.id,
                'fournisseur_id': med.fournisseur_id.id if med.fournisseur_id else False,
                'stock_actuel': med.stock_actuel,
                'alerte_rupture': med.alerte_rupture,
                'quantite_suggeree': quantite_suggeree,
                'selectionne': True,
            }))
        self.write({'ligne_ids': lignes, 'nb_alertes': len(meds_en_alerte)})

    def action_generer_bons(self):
        """Génère un bon de commande par fournisseur."""
        lignes_selectionnees = self.ligne_ids.filtered(
            lambda l: l.selectionne and l.quantite_suggeree > 0 and l.fournisseur_id
        )
        if not lignes_selectionnees:
            from odoo.exceptions import UserError
            raise UserError('Aucune ligne sélectionnée avec fournisseur et quantité.')

        # Regroupement par fournisseur
        bons_par_fournisseur = {}
        for ligne in lignes_selectionnees:
            fid = ligne.fournisseur_id.id
            if fid not in bons_par_fournisseur:
                bons_par_fournisseur[fid] = []
            bons_par_fournisseur[fid].append(ligne)

        bons_crees = self.env['pharmacie.reappro']
        for fournisseur_id, lignes in bons_par_fournisseur.items():
            from datetime import date, timedelta
            bon_vals = {
                'fournisseur_id': fournisseur_id,
                'date_commande': date.today(),
                'date_livraison_prevue': date.today() + timedelta(days=7),
                'ligne_ids': [(0, 0, {
                    'medicament_id': l.medicament_id.id,
                    'quantite_commandee': l.quantite_suggeree,
                    'prix_unitaire': l.medicament_id.prix_achat,
                    'date_peremption': date.today() + timedelta(days=365),
                }) for l in lignes],
            }
            bons_crees |= self.env['pharmacie.reappro'].create(bon_vals)

        # Ouvrir les bons créés
        return {
            'type': 'ir.actions.act_window',
            'name': 'Bons de commande générés',
            'res_model': 'pharmacie.reappro',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', bons_crees.ids)],
        }
