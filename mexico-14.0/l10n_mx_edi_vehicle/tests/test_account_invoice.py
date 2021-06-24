
import base64

from lxml import objectify

from odoo.addons.l10n_mx_edi.tests.common import TestMxEdiCommon


class TestL10nMxEdiInvoiceVehicle(TestMxEdiCommon):

    def setUp(self):
        super(TestL10nMxEdiInvoiceVehicle, self).setUp()
        self.certificate._check_credentials()
        self.env.user.write({
            'groups_id': [(4, self.ref('fleet.fleet_group_manager'))],
        })

    def test_l10n_mx_edi_invoice_cd(self):
        vehicle_id = self.env.ref('fleet.vehicle_3')
        vehicle_id.sudo().write({
            'model_year': '2000',
            'l10n_mx_edi_niv': 'YU76YI',
            'l10n_mx_edi_motor': '567MOTORN087',
            'l10n_mx_edi_circulation_no': 'MEX6467HGTO',
            'l10n_mx_edi_landing': '15 000 435',
            'l10n_mx_edi_landing_date': '2000-06-06',
            'l10n_mx_edi_aduana': 'Aduana',
            'vin_sn': '1234567ASDF12V67W',
        })
        invoice = self.invoice
        invoice.sudo().company_id.l10n_mx_edi_complement_type = 'destruction'
        invoice.write({
            'l10n_mx_edi_serie_cd': 'serie_a',
            'l10n_mx_edi_folio_cd': '123456GFD',
            'l10n_mx_edi_vehicle_id': vehicle_id.id,
        })
        invoice.action_post()
        generated_files = self._process_documents_web_services(invoice, {'cfdi_3_3'})
        self.assertTrue(generated_files)
        self.assertEqual(invoice.edi_state, "sent", invoice.message_ids.mapped('body'))
        xml = objectify.fromstring(generated_files[0])
        namespaces = {
            'destruccion': 'http://www.sat.gob.mx/certificadodestruccion'}
        comp = xml.Complemento.xpath('//destruccion:certificadodedestruccion',
                                     namespaces=namespaces)
        self.assertTrue(comp, 'Complement to EAPA not added correctly')

    def test_l10n_mx_edi_xsd(self):
        """Verify that xsd file is downloaded"""
        self.invoice.company_id._load_xsd_attachments()
        xsd_file = self.ref(
            'l10n_mx_edi.xsd_cached_certificadodedestruccion_xsd')
        self.assertTrue(xsd_file, 'XSD file not load')

    def test_invoice_renew_and_substitution(self):
        vehicle_id = self.env.ref('fleet.vehicle_3')
        vehicle_id.sudo().write({
            'vin_sn': '1234567ASDF12V67W',
            'model_year': '2016',
        })
        substitute_vehicle_id = self.env.ref('fleet.vehicle_1').sudo()
        vehicle_type_tag = self.env['fleet.vehicle.tag'].search(
            [('name', '=', '01 - Fifth wheel tractor')])
        if not vehicle_type_tag:
            vehicle_type_tag = self.env['fleet.vehicle.tag'].create({
                'name': '01 - Fifth wheel tractor'})
        substitute_vehicle_id.tag_ids.unlink()
        substitute_vehicle_id.tag_ids = [
            self.env.ref('fleet.vehicle_3').sudo().tag_ids[0].id,
            vehicle_type_tag.id
        ]
        substitute_vehicle_id.sudo().write({
            'model_year': '2000',
            'vin_sn': '1234567ASDF12V67Y',
            'l10n_mx_edi_circulation_no': 'MEX6467HGTO',
            'l10n_mx_edi_fiscal_folio': '123-ABCDE-4567-FGHI',
            'l10n_mx_edi_int_advice': '89-JKL-09-MN',
            'l10n_mx_edi_landing': '1234567',
            'l10n_mx_edi_landing_date': '2000-01-01',
            'l10n_mx_edi_aduana': 'Aduana Prueba',
        })
        invoice = self.invoice
        invoice.sudo().company_id.l10n_mx_edi_complement_type = 'renew'
        invoice.write({
            'l10n_mx_edi_decree_type': '02',
            'l10n_mx_edi_substitute_id': substitute_vehicle_id.id,
            'l10n_mx_edi_vehicle_id': vehicle_id.id,
        })
        invoice.action_post()
        generated_files = self._process_documents_web_services(invoice, {'cfdi_3_3'})
        self.assertTrue(generated_files)
        self.assertEqual(invoice.edi_state, "sent", invoice.message_ids.mapped('body'))
        xml = objectify.fromstring(generated_files[0])
        namespaces = {
            'decreto': 'http://www.sat.gob.mx/renovacionysustitucionvehiculos'}
        comp = xml.Complemento.xpath('//decreto:renovacionysustitucionvehiculos', # noqa
                                     namespaces=namespaces)
        self.assertTrue(comp, 'Complement to Renew ans Substitution not added '
                        'correctly')

    def test_used_vehicle(self):
        vehicle_id = self.env.ref('fleet.vehicle_3')
        vehicle_model_brand = self.env['fleet.vehicle.model.brand'].create({
            'name': 'Nissan', })
        vehicle_model = self.env['fleet.vehicle.model'].create({
            'name': 'Aprio',
            'brand_id': vehicle_model_brand.id,
        })
        vehicle_id.sudo().write({
            'license_plate': '1BMW001',
            'model_id': vehicle_model.id,
            'residual_value': 1000.00,
            'l10n_mx_edi_motor': '1234JN90LNX',
            'l10n_mx_edi_niv': '123456789',
            'model_year': '2008',
            'odometer': 10345,
            'car_value': 131100,
            'vin_sn': '1234567ASDF12V67Y',
            'l10n_mx_edi_landing': '33227007095',
            'l10n_mx_edi_landing_date': '2007-11-07',
            'l10n_mx_edi_aduana': 'Int. del Edo. de Ags.'
        })
        invoice = self.invoice
        invoice.sudo().company_id.l10n_mx_edi_complement_type = 'sale'
        invoice.write({'l10n_mx_edi_vehicle_id': vehicle_id.id})
        invoice.message_ids.unlink()
        invoice.action_post()
        generated_files = self._process_documents_web_services(invoice, {'cfdi_3_3'})
        self.assertTrue(generated_files)
        self.assertEqual(invoice.edi_state, "sent", invoice.message_ids.mapped('body'))
        attach = self.env['ir.attachment'].search(
            [('res_model', '=', 'account.move'),
             ('res_id', '=', invoice.id)], limit=1)
        xml_str = base64.b64decode(attach.datas)
        xml = objectify.fromstring(xml_str)
        xml_expected = objectify.fromstring(
            '<vehiculousado:VehiculoUsado '
            'xmlns:vehiculousado="http://www.sat.gob.mx/vehiculousado" '
            'Version="1.0" montoAdquisicion="131100.0" '
            'montoEnajenacion="8480.0" claveVehicular="1BMW001" marca="Nissan" '
            'tipo="Aprio" modelo="2008" numeroMotor="1234JN90LNX" '
            'numeroSerie="1234567ASDF12V67Y" NIV="123456789" '
            'valor="1000.0"><vehiculousado:InformacionAduanera '
            'numero="33227007095" fecha="2007-11-07" '
            'aduana="Int. del Edo. de Ags."/></vehiculousado:VehiculoUsado>'
        )
        namespaces = {'vehiculousado': 'http://www.sat.gob.mx/vehiculousado'}
        comp = xml.Complemento.xpath('//vehiculousado:VehiculoUsado',
                                     namespaces=namespaces)
        self.assertEqualXML(comp[0], xml_expected)

    def test_pfic(self):
        vehicle_id = self.env.ref('fleet.vehicle_3')
        vehicle_id.sudo().write({'l10n_mx_edi_niv': '0101011'})
        invoice = self.invoice
        invoice.sudo().company_id.l10n_mx_edi_complement_type = 'pfic'
        invoice.write({'l10n_mx_edi_vehicle_id': vehicle_id.id})
        invoice.action_post()
        generated_files = self._process_documents_web_services(invoice, {'cfdi_3_3'})
        self.assertTrue(generated_files)
        self.assertEqual(invoice.edi_state, "sent", invoice.message_ids.mapped('body'))
        xml = objectify.fromstring(generated_files[0])
        namespaces = {'pfic': 'http://www.sat.gob.mx/pfic'}
        comp = xml.Complemento.xpath('//pfic:PFintegranteCoordinado',
                                     namespaces=namespaces)
        self.assertTrue(comp, 'Complement for PFIC not added correctly')

    def test_new_vehicle(self):
        vehicle_id = self.env.ref('fleet.vehicle_3')
        vehicle_model_brand = self.env['fleet.vehicle.model.brand'].create({
            'name': '01', })
        vehicle_model = self.env['fleet.vehicle.model'].create({
            'name': '1234',
            'brand_id': vehicle_model_brand.id,
        })
        vehicle_id.sudo().write({
            'license_plate': '1BMW0017',
            'model_id': vehicle_model.id,
            'l10n_mx_edi_niv': '123456789',
            'odometer': 0.0,
        })
        self.env['fleet.vehicle.log.services'].create({
            'vehicle_id': vehicle_id.id,
            'service_type_id': self.env.ref('l10n_mx_edi_vehicle.l10n_mx_edi_fleet_service_extra').id,
            'amount': 4000.00,
            'description': '3/PZ/12345/09876/test aduana',
            'date': '2018-03-15',
        })
        invoice = self.invoice
        invoice.sudo().company_id.l10n_mx_edi_complement_type = 'sale'
        invoice.write({'l10n_mx_edi_vehicle_id': vehicle_id.id})
        invoice.action_post()
        generated_files = self._process_documents_web_services(invoice, {'cfdi_3_3'})
        self.assertTrue(generated_files)
        self.assertEqual(invoice.edi_state, "sent", invoice.message_ids.mapped('body'))
        xml = objectify.fromstring(generated_files[0])
        namespaces = {'ventavehiculos': 'http://www.sat.gob.mx/ventavehiculos'}
        comp = xml.Conceptos.xpath('//ventavehiculos:VentaVehiculos', namespaces=namespaces)
        self.assertTrue(comp, 'Concept Complement for New Vehicle not added correctly')

    def xml2dict(self, xml):
        """Receive 1 lxml etree object and return a dict string.
        This method allow us have a precise diff output"""
        def recursive_dict(element):
            return (element.tag,
                    dict((recursive_dict(e) for e in element.getchildren()),
                         ____text=(element.text or '').strip(), **element.attrib))
        return dict([recursive_dict(xml)])

    def assertEqualXML(self, xml_real, xml_expected):  # pylint: disable=invalid-name
        """Receive 2 objectify objects and show a diff assert if exists."""
        xml_expected = self.xml2dict(xml_expected)
        xml_real = self.xml2dict(xml_real)
        # "self.maxDiff = None" is used to get a full diff from assertEqual method
        # This allow us get a precise and large log message of where is failing
        # expected xml vs real xml More info:
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None
        self.assertEqual(xml_real, xml_expected)
