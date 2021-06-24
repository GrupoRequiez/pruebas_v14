# Part of Odoo. See LICENSE file for full copyright and licensing details.

from lxml.etree import fromstring
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_mx_edi_serie_cd = fields.Selection([
        ('serie_a', 'Serie A'),
        ('serie_b', 'Serie B'),
        ('serie_c', 'Serie C'),
        ('serie_d', 'Serie D'),
        ('serie_e', 'Serie E')], 'Serie',
        help='Assign the serie according the SAT catalog to the vehicle that '
        'was destroyed')
    l10n_mx_edi_folio_cd = fields.Char(
        'Folio', help='Assign the folio provided by the SAT to this '
        'destruction')
    l10n_mx_edi_vehicle_id = fields.Many2one(
        'fleet.vehicle', 'Vehicle',
        help='Indicate the vehicle that was destroyed if you are using the '
        'Destruction Certificate. Or the transfer vehicle if you are using '
        'the Vehicle Renew and Substitution Complement. If it is a sale of a '
        'vehicle, or using the PFIC complement, specify the vehicle.')
    l10n_mx_edi_decree_type = fields.Selection(
        string="Decree Type",
        selection=[
            ('01', 'Renovation of the motor transport vehicle park'),
            ('02', 'Replacement of passenger and freight motor vehicles')
        ],
        help='Decree which is going to be applicated'
    )
    l10n_mx_edi_vehicle_ids = fields.Many2many(
        'fleet.vehicle',
        string='Used Vehicles',
        help='Indicate the vehicles that are going to be replaced'
    )
    l10n_mx_edi_substitute_id = fields.Many2one(
        'fleet.vehicle', 'Substitute Vehicle',
        help='Indicate the vehicle that is going to be replaced')
    l10n_mx_edi_complement_type = fields.Selection(
        related='company_id.l10n_mx_edi_complement_type', readonly=True)

    @api.onchange('l10n_mx_edi_decree_type')
    def _decree_type_change(self):
        """Assure the fields are reset when decree type is changed"""
        self.l10n_mx_edi_substitute_id = False
        self.l10n_mx_edi_vehicle_ids = False

    def _l10n_mx_edi_decode_cfdi(self, cfdi_data=None):
        """If the CFDI was signed, try to adds the schemaLocation correctly"""
        result = super(AccountMove, self)._l10n_mx_edi_decode_cfdi(cfdi_data=cfdi_data)
        if not cfdi_data:
            return result
        cfdi_data = cfdi_data.replace(b'xmlns__destruccion', b'xmlns:destruccion').replace(
            b'xmlns__ventavehiculos', b'xmlns:ventavehiculos').replace(
                b'xmlns__ventavehiculos', b'xmlns:ventavehiculos').replace(
                    b'xmlns__pfic', b'xmlns:pfic').replace(b'xmlns__decreto', b'xmlns:decreto').replace(
                        b'xmlns__vehiculousado', b'xmlns:vehiculousado')
        cfdi = fromstring(cfdi_data)
        if 'destruccion' in cfdi.nsmap:
            cfdi.attrib['{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'] = '%s %s %s' % (
                cfdi.get('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'),
                'http://www.sat.gob.mx/certificadodestruccion',
                'http://www.sat.gob.mx/sitio_internet/cfd/certificadodestruccion/certificadodedestruccion.xsd')
        elif 'ventavehiculos' in cfdi.nsmap:
            cfdi.attrib['{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'] = '%s %s %s' % (
                cfdi.get('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'),
                'http://www.sat.gob.mx/ventavehiculos',
                'http://www.sat.gob.mx/sitio_internet/cfd/ventavehiculos/ventavehiculos11.xsd')
        elif 'pfic' in cfdi.nsmap:
            cfdi.attrib['{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'] = '%s %s %s' % (
                cfdi.get('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'),
                'http://www.sat.gob.mx/pfic',
                'http://www.sat.gob.mx/sitio_internet/cfd/pfic/pfic.xsd')
        elif 'decreto' in cfdi.nsmap:
            cfdi.attrib['{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'] = '%s %s %s' % (
                cfdi.get('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'),
                'http://www.sat.gob.mx/renovacionysustitucionvehiculos',
                'http://www.sat.gob.mx/sitio_internet/cfd/renovacionysustitucionvehiculos/renovacionysustitucionvehiculos.xsd')  # noqa
        elif 'vehiculousado' in cfdi.nsmap:
            cfdi.attrib['{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'] = '%s %s %s' % (
                cfdi.get('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'),
                'http://www.sat.gob.mx/vehiculousado',
                'http://www.sat.gob.mx/sitio_internet/cfd/vehiculousado/vehiculousado.xsd')
        result['cfdi_node'] = cfdi
        return result
