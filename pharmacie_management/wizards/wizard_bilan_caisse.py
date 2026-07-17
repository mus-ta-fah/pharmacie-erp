# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class WizardBilanCaisse(models.TransientModel):
    _name = 'wizard.bilan.caisse'
    _description = 'Bilan de caisse'

    date_debut = fields.Date(string='Date de début', required=True, default=fields.Date.today)
    date_fin = fields.Date(string='Date de fin', required=True, default=fields.Date.today)

    # Résultats calculés
    ca_total = fields.Float(string='Chiffre d\'affaires TTC (FCFA)', readonly=True, digits=(10, 0))
    nb_ventes = fields.Integer(string='Nombre de ventes', readonly=True)
    panier_moyen = fields.Float(string='Panier moyen (FCFA)', readonly=True, digits=(10, 0))
    detail_ids = fields.One2many(
        'wizard.bilan.caisse.detail', 'wizard_id', string='Détail par vendeur', readonly=True,
    )
    calcule = fields.Boolean(default=False)

    @api.constrains('date_debut', 'date_fin')
    def _check_dates(self):
        for w in self:
            if w.date_debut and w.date_fin and w.date_fin < w.date_debut:
                raise UserError('La date de fin doit être postérieure à la date de début.')

    def action_calculer(self):
        """Calcule les indicateurs financiers sur la période."""
        for wizard in self:
            ventes = self.env['pharmacie.vente'].search([
                ('statut', '=', 'confirmee'),
                ('date_vente', '>=', f'{wizard.date_debut} 00:00:00'),
                ('date_vente', '<=', f'{wizard.date_fin} 23:59:59'),
            ])

            ca = sum(ventes.mapped('montant_ttc'))
            nb = len(ventes)
            panier = ca / nb if nb > 0 else 0.0

            # Détail par vendeur
            vendeurs = ventes.mapped('vendeur_id')
            details = []
            for vendeur in vendeurs:
                ventes_vendeur = ventes.filtered(lambda v: v.vendeur_id == vendeur)
                ca_vendeur = sum(ventes_vendeur.mapped('montant_ttc'))
                nb_vendeur = len(ventes_vendeur)
                details.append((0, 0, {
                    'vendeur_id': vendeur.id,
                    'nb_ventes': nb_vendeur,
                    'ca_ttc': ca_vendeur,
                    'panier_moyen': ca_vendeur / nb_vendeur if nb_vendeur > 0 else 0,
                }))

            # Supprimer les anciens détails et recalculer
            wizard.detail_ids.unlink()
            wizard.write({
                'ca_total': ca,
                'nb_ventes': nb,
                'panier_moyen': panier,
                'detail_ids': details,
                'calcule': True,
            })

        # Recharger le même wizard (rester sur le popup)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.bilan.caisse',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_generer_pdf(self):
        """Lance la génération du rapport PDF bilan de caisse."""
        if not self.calcule:
            raise UserError('Veuillez d\'abord cliquer sur "Calculer" avant de générer le PDF.')
        return self.env.ref(
            'pharmacie_management.action_report_bilan_caisse'
        ).report_action(self)


class WizardBilanCaisseDetail(models.TransientModel):
    _name = 'wizard.bilan.caisse.detail'
    _description = 'Détail par vendeur'

    wizard_id = fields.Many2one('wizard.bilan.caisse', ondelete='cascade')
    vendeur_id = fields.Many2one('res.users', string='Vendeur', readonly=True)
    nb_ventes = fields.Integer(string='Nb ventes', readonly=True)
    ca_ttc = fields.Float(string='CA TTC (FCFA)', readonly=True, digits=(10, 0))
    panier_moyen = fields.Float(string='Panier moyen (FCFA)', readonly=True, digits=(10, 0))
