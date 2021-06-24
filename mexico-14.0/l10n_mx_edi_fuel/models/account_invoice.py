from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_mx_edi_emitter_reference = fields.Char(
        string="Electronic Purse Issuer Reference",
        help="This is needed when a service station invoice a fuel "
        "consumption given an electronic purse issuer credit note. "
        "The format should be: 'electronic purse number|"
        "electronic purse identifier owner bank account'."
        "ex.: 1234|0001234")

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None,
                        description=None, journal_id=None):
        values = super(AccountMove, self)._prepare_refund(
            invoice, date_invoice=date_invoice, date=date,
            description=description, journal_id=journal_id)
        for line in values.get('invoice_line_ids'):
            line[2].update({'l10n_mx_edi_fuel_partner_id': False})
        return values

    def _l10n_mx_edi_create_cfdi_values(self):
        values = super(AccountMove, self)._l10n_mx_edi_create_cfdi_values()
        fuel_billing = self.invoice_line_ids.filtered(
            'product_id.l10n_mx_edi_fuel_billing')
        if not fuel_billing:
            return values
        values['fuel_lines'] = fuel_billing
        values['fuel_amount_untaxed'] = sum(fuel_billing.mapped(
            lambda l: l.quantity * l.price_unit))
        fuel_total_tax = self._get_fuel_taxes(fuel_billing)
        values['fuel_amount_total'] = values['fuel_amount_untaxed'] + fuel_total_tax # noqa
        return values

    def _get_fuel_taxes(self, lines):
        result = False
        if not lines:
            return result
        for line in lines:
            for tax in line.tax_ids.filtered(lambda r: r.amount > 0 and r.l10n_mx_tax_type != 'Exento'):
                result += round(abs(
                    tax.amount / 100.0 * line.price_subtotal), 2)
        return result


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    l10n_mx_edi_fuel_partner_id = fields.Many2one(
        'res.partner',
        string='Service Station',
        help='Service Station information, set this if the company is an '
        'electronic purse issuer and you are issuing an Invoice',
    )
