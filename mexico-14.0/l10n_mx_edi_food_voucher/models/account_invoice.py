from lxml import etree
from odoo import _, models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    def invoice_validate(self):
        for record in self.l10n_mx_edi_cfdi_request in ('on_invoice', 'on_refund'):
            if record.invoice_line_ids.filtered(lambda r: r.l10n_mx_edi_voucher_id and r.quantity != 0): # noqa
                record.message_post(
                    body=_(
                        '''<p style="color:red">The quantity in the invoice
                        lines which have an Employee has to be zero.</p>'''),
                    subtype='account.mt_invoice_validated')
                return False
        return super(AccountMove, self).invoice_validate()

    def _l10n_mx_edi_create_cfdi(self):
        """If the CFDI was signed, try to adds the schemaLocation for Donations"""
        result = super(AccountMove, self)._l10n_mx_edi_create_cfdi()
        cfdi = result.get('cfdi')
        if not cfdi:
            return result
        cfdi = self.l10n_mx_edi_get_xml_etree(cfdi)
        if 'valesdedespensa' not in cfdi.nsmap:
            return result
        cfdi.attrib['{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'] = '%s %s %s' % (
            cfdi.get('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'),
            'http://www.sat.gob.mx/valesdedespensa',
            'http://www.sat.gob.mx/sitio_internet/cfd/valesdedespensa/valesdedespensa.xsd')
        result['cfdi'] = etree.tostring(cfdi, pretty_print=True, xml_declaration=True, encoding='UTF-8')
        return result


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    l10n_mx_edi_voucher_id = fields.Many2one(
        'res.partner',
        string='Employee',
        help='Employee information, set this if you want to use the Food '
        'Voucher Complement'
    )
