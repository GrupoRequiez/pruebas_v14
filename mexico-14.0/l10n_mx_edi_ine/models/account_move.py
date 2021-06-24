from lxml.objectify import fromstring

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_mx_edi_ine_process_type = fields.Selection(
        selection=[
            ('ordinary', 'Ordinary'),
            ('precampaign', 'Precampaign'),
            ('campaign', 'Campaign')
        ],
        string='Process Type')
    l10n_mx_edi_ine_committee_type = fields.Selection(
        selection=[
            ('national_executive', 'National Executive'),
            ('state_executive', 'State Executive'),
            ('state_manager', 'State Manager')
        ],
        string='Committee Type',
        help="Set this when Process Type is 'Ordinary'")
    l10n_mx_edi_ine_accounting = fields.Char(
        string='Accounting',
        help="This field is optional. You can fill this field when Process "
        "type is 'Ordinary' and the Committee type is 'National Executive'")
    l10n_mx_edi_ine_entity_ids = fields.One2many(
        'l10n_mx_edi_ine.entity',
        'invoice_id',
        string='Entity / Scope / Accounting Id',
        help="Set this when Committee Type is 'State Executive' or 'State '"
        "Manager'. Set 'Accounting' only when Process Type is 'Campaign' or "
        "Pre-campaign, or when Process type 'Ordinary' and Committee Type "
        "'State Executive', please use comma to separate the accounts numbers"
        "when you need to provide several numbers for one Entity.")

    @api.onchange('l10n_mx_edi_ine_process_type')
    def _process_type_change(self):
        """Assure l10n_mx_edi_committee_type to be reset when
        l10n_mx_edi_process_type is changed"""
        if (self.l10n_mx_edi_ine_process_type == 'campaign' or
                self.l10n_mx_edi_ine_process_type == 'precampaign'):
            self.l10n_mx_edi_ine_committee_type = False

    def _l10n_mx_edi_decode_cfdi(self, cfdi_data=None):
        """If the CFDI was signed, try to adds the schemaLocation correctly"""
        result = super(AccountMove, self)._l10n_mx_edi_decode_cfdi(cfdi_data=cfdi_data)
        if not cfdi_data:
            return result
        cfdi_data = cfdi_data.replace(b'xmlns__ine', b'xmlns:ine')
        cfdi = fromstring(cfdi_data)
        if 'ine' not in cfdi.nsmap:
            return result
        cfdi.attrib['{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'] = '%s %s %s' % (
            cfdi.get('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'),
            'http://www.sat.gob.mx/ine',
            'http://www.sat.gob.mx/sitio_internet/cfd/ine/ine11.xsd')
        result['cfdi_node'] = cfdi
        return result
