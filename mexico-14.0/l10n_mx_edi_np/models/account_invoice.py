# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_mx_edi_np_partner_id = fields.Many2one(
        'res.partner',
        string="Buyer",
        help="Buyer or buyers information"
    )
