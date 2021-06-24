
import os

from lxml.objectify import fromstring

from odoo.addons.l10n_mx_edi.tests.common import TestMxEdiCommon
from odoo.tools import misc
from odoo.tests.common import Form


class TestL10nMxEdiInvoiceINE(TestMxEdiCommon):

    def create_invoice_ine_line(self, invoice_id):
        invoice_ine_line_model = self.env['l10n_mx_edi_ine.entity']
        self.country = self.env['res.country'].search([("code", "=", "MX")])
        state = self.env['res.country.state'].search([
            ('code', '=', 'COL'), ('country_id', '=', self.country.id)])
        lines2create = []
        ine_line = invoice_ine_line_model.new({
            'l10n_mx_edi_ine_entity_id': state.id,
            'l10n_mx_edi_ine_scope': 'local',
            'l10n_mx_edi_ine_accounting': '789',
            'invoice_id': invoice_id,
        })
        ine_line_dict = ine_line._convert_to_write({
            name: ine_line[name] for name in ine_line._cache})
        lines2create.append((0, 0, ine_line_dict))
        ine_line = invoice_ine_line_model.new({
            'l10n_mx_edi_ine_entity_id': state.id,
            'l10n_mx_edi_ine_scope': 'local',
            'l10n_mx_edi_ine_accounting': '123,456',
            'invoice_id': invoice_id,
        })
        ine_line_dict = ine_line._convert_to_write({
            name: ine_line[name] for name in ine_line._cache})
        lines2create.append((0, 0, ine_line_dict))
        invoice_ine_line_model.create(ine_line_dict)

    def test_l10n_mx_edi_simple_ine(self):
        self.certificate._check_credentials()
        xml_expected_simple_str = misc.file_open(os.path.join(
            'l10n_mx_edi_ine', 'tests', 'expected_simple_ine.xml')).read(
            ).encode('UTF-8')
        invoice = self.invoice
        invoice.currency_id = self.env.ref('base.MXN')
        invoice.company_id.sudo().name = 'YourCompany INE'
        invoice.l10n_mx_edi_ine_process_type = 'ordinary'
        invoice.l10n_mx_edi_ine_committee_type = 'national_executive'
        invoice.l10n_mx_edi_ine_accounting = '123456'
        move_form = Form(invoice)
        with move_form.invoice_line_ids.edit(0) as line_form:
            line_form.tax_ids.clear()
        move_form.save()
        invoice.action_post()
        generated_files = self._process_documents_web_services(self.invoice, {'cfdi_3_3'})
        self.assertTrue(generated_files)
        self.assertEqual(invoice.edi_state, "sent", invoice.message_ids.mapped('body'))
        xml = fromstring(generated_files[0])
        namespaces = {'ine': 'http://www.sat.gob.mx/ine'}
        ine = xml.Complemento.xpath('//ine:INE', namespaces=namespaces)
        self.assertTrue(ine, 'Complement to INE not added correctly')
        xml_expected = fromstring(xml_expected_simple_str)
        self.xml_merge_dynamic_items(xml, xml_expected)
        xml_expected.attrib['Folio'] = xml.attrib['Folio']
        self.assertEqualXML(xml, xml_expected)

    def test_l10n_mx_edi_complex_ine(self):
        self.certificate._check_credentials()
        xml_expected_complex_str = misc.file_open(os.path.join(
            'l10n_mx_edi_ine', 'tests', 'expected_complex_ine.xml')).read(
            ).encode('UTF-8')
        invoice = self.invoice
        invoice.currency_id = self.env.ref('base.MXN')
        invoice.company_id.sudo().name = 'YourCompany INE'
        self.create_invoice_ine_line(invoice.id)
        invoice.l10n_mx_edi_ine_process_type = 'precampaign'
        move_form = Form(invoice)
        with move_form.invoice_line_ids.edit(0) as line_form:
            line_form.tax_ids.clear()
        move_form.save()
        invoice.action_post()
        generated_files = self._process_documents_web_services(self.invoice, {'cfdi_3_3'})
        self.assertTrue(generated_files)
        self.assertEqual(invoice.edi_state, "sent", invoice.message_ids.mapped('body'))
        xml = fromstring(generated_files[0])
        namespaces = {'ine': 'http://www.sat.gob.mx/ine'}
        ine = xml.Complemento.xpath('//ine:INE', namespaces=namespaces)
        self.assertTrue(ine, 'Complement to INE not added correctly')
        xml_expected = fromstring(xml_expected_complex_str)
        self.xml_merge_dynamic_items(xml, xml_expected)
        xml_expected.attrib['Folio'] = xml.attrib['Folio']
        self.assertEqualXML(xml, xml_expected)

    def xml_merge_dynamic_items(self, xml, xml_expected):
        xml_expected.attrib['Fecha'] = xml.attrib['Fecha']
        xml_expected.attrib['Sello'] = xml.attrib['Sello']
        xml_expected.attrib['Serie'] = xml.attrib['Serie']
        xml_expected.Complemento = xml.Complemento

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
