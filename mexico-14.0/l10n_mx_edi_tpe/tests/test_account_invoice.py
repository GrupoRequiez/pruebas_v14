from lxml.objectify import fromstring

from odoo.addons.l10n_mx_edi.tests.common import TestMxEdiCommon


class TestL10nMxEdiInvoiceTPE(TestMxEdiCommon):

    def test_l10n_mx_edi_invoice_tpe(self):
        self.certificate._check_credentials()
        self.env['base.language.install'].create(
            {'lang': 'es_MX', 'overwrite': 0}).lang_install()
        self.product.sudo().write({
            'l10n_mx_edi_tpe_track': 'seaway'
        })
        invoice = self.invoice
        invoice.partner_id.sudo().write({
            'country_id': self.ref('base.aw'),
            'ref': 'passport|EGA93812273-PLM3821'
        })
        invoice.l10n_mx_edi_tpe_transit_date = '2018-05-12'
        invoice.l10n_mx_edi_tpe_transit_time = 5.16666666666667
        invoice.l10n_mx_edi_tpe_transit_type = 'departure'
        invoice.name = 'MX8321/GC9328'
        invoice.l10n_mx_edi_tpe_partner_id = self.ref('base.res_partner_3')
        invoice.message_ids.unlink()
        invoice.action_post()
        generated_files = self._process_documents_web_services(self.invoice, {'cfdi_3_3'})
        self.assertTrue(generated_files)
        self.assertEqual(invoice.edi_state, "sent", invoice.message_ids.mapped('body'))
        xml = fromstring(generated_files[0])
        xml_expected = fromstring(
            '<tpe:TuristaPasajeroExtranjero '
            'xmlns:tpe="http://www.sat.gob.mx/TuristaPasajeroExtranjero" '
            'version="1.0" fechadeTransito="2018-05-12T05:10:00" '
            'tipoTransito="Salida"><tpe:datosTransito Via="Marítima" '
            'TipoId="passport" NumeroId="EGA93812273-PLM3821" '
            'Nacionalidad="Aruba" EmpresaTransporte="Gemini Furniture" '
            'IdTransporte="MX8321/GC9328"/></tpe:TuristaPasajeroExtranjero>')
        namespace = {'tpe': 'http://www.sat.gob.mx/TuristaPasajeroExtranjero'}
        xml_tpe = xml.Complemento.xpath('//tpe:TuristaPasajeroExtranjero',
                                        namespaces=namespace)
        self.assertEqualXML(xml_tpe[0], xml_expected)

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
