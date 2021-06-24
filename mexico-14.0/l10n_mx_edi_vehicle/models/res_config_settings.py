# Copyright 2018 Vauxoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    l10n_mx_edi_complement_type = fields.Selection(
        related='company_id.l10n_mx_edi_complement_type',
        string='Vehicle Complement', readonly=False,
        help='Select one of those complements if you want it to be available '
        'for invoice')
