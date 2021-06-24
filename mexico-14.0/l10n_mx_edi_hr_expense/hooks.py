# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools


def pre_init_hook(cr):
    tools.convert.convert_file(
        cr, 'l10n_mx_edi_hr_expense', 'data/partner_tags.xml',
        None, mode='init', kind='data')
