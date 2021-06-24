from lxml.objectify import fromstring

from odoo.addons.l10n_mx_edi.tests.common import TestMxEdiCommon
from odoo.exceptions import ValidationError


class TestCurrencyTrading(TestMxEdiCommon):
    def setUp(self):
        super(TestCurrencyTrading, self).setUp()
        self.certificate._check_credentials()
        self.namespaces = {
            'cfdi': 'http://www.sat.gob.mx/cfd/3',
            'divisas': 'http://www.sat.gob.mx/divisas',
        }
        self.product2 = self.env.ref("product.product_product_4")
        self.product2.unspsc_code_id = self.ref('product_unspsc.unspsc_code_01010101')

    def test_xml_node(self):
        """Validates that the XML node ``<divisas:Divisas>`` is included only
            when the field Exchange operation type is specified on a product,
            and that its content is generated correctly
        """
        # First, creates an invoice without any exchange operation type on any
        # of its products. XML node should not be included
        invoice = self.invoice
        invoice.action_post()
        generated_files = self._process_documents_web_services(self.invoice, {'cfdi_3_3'})
        self.assertTrue(generated_files)
        self.assertEqual(invoice.edi_state, "sent", invoice.message_ids.mapped('body'))
        xml = fromstring(generated_files[0])
        self.assertFalse(hasattr(xml, 'Complemento'), 'The Complement must not present')

        # Then, set the field on the product and re-sign.
        # This time, the XML node should be included
        xml_expected = fromstring('''
            <divisas:Divisas
                xmlns:divisas="http://www.sat.gob.mx/divisas"
                version="1.0"
                tipoOperacion="venta"/>''')
        self.product.sudo().l10n_mx_edi_ct_type = 'sale'
        invoice = self.invoice
        invoice.action_post()
        generated_files = self._process_documents_web_services(self.invoice, {'cfdi_3_3'})
        self.assertTrue(generated_files)
        self.assertEqual(invoice.edi_state, "sent", invoice.message_ids.mapped('body'))
        xml = fromstring(generated_files[0])
        error_msg = "The node '<divisas:Divisas> should be present"
        self.assertTrue(xml.Complemento.xpath(
            'divisas:Divisas', namespaces=self.namespaces), error_msg)
        xml_divisas = xml.Complemento.xpath(
            'divisas:Divisas', namespaces=self.namespaces)[0]
        self.assertEqualXML(xml_divisas, xml_expected)

    def test_ct_types_dont_match(self):
        """Validates that, when an invoice are issued for multiple products,
            and the field Exchange operation type are set but they're not the
            same for all products, an exception is raised
        """
        self.product.sudo().l10n_mx_edi_ct_type = 'sale'
        self.product2.sudo().l10n_mx_edi_ct_type = 'purchase'
        invoice = self.invoice
        invoice_line = invoice.invoice_line_ids.read([])[0]
        line2 = invoice_line.copy()
        line2.update({'product_id': self.product2.id})
        invoice.line_ids.unlink()
        invoice.invoice_line_ids.unlink()
        invoice.invoice_line_ids = [(0, 0, invoice_line), (0, 0, line2)]
        error_msg = ("This invoice contains products with different exchange "
                     "operation types.")
        with self.assertRaisesRegex(ValidationError, error_msg):
            invoice.action_post()

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
