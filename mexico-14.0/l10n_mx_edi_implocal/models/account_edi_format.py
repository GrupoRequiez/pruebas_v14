from odoo import models


class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    def _l10n_mx_edi_get_invoice_line_cfdi_values(self, invoice, line):
        cfdi_values = super(AccountEdiFormat, self)._l10n_mx_edi_get_invoice_line_cfdi_values(invoice, line)
        taxes = []
        for tax in cfdi_values.get('tax_details'):
            if 'local' in tax['tax'].mapped('invoice_repartition_line_ids.tag_ids.name'):
                continue
            taxes.append(tax)
        cfdi_values['tax_details'] = taxes
        return cfdi_values
