from lxml.objectify import fromstring

from odoo.addons.l10n_mx_edi.tests.common import TestMxEdiCommon


class TestL10nMxEdiInvoiceIEDU(TestMxEdiCommon):

    def test_l10n_mx_edi_invoice_iedu(self):
        self.certificate._check_credentials()
        self.invoice.company_id.company_registry = '5152'  # set institution code
        # set curp because group account invoice can't modify partners
        self.partner_a.write({
            'l10n_mx_edi_curp': 'ROGC001031HJCDRR07',
            'category_id': [(4, self.ref('l10n_mx_edi_iedu.iedu_level_4'))],
        })
        invoice = self.invoice
        self.env['l10n_mx_edi_iedu.codes'].create({
            'journal_id': invoice.journal_id.id,
            'l10n_mx_edi_iedu_education_level_id': self.ref('l10n_mx_edi_iedu.iedu_level_4'),
            'l10n_mx_edi_iedu_code': 'ES4-728L-3018'
        })
        invoice.invoice_line_ids.write({
            'l10n_mx_edi_iedu_id': self.partner_a.id,
        })
        invoice.action_post()
        generated_files = self._process_documents_web_services(self.invoice, {'cfdi_3_3'})
        self.assertTrue(generated_files)
        self.assertEqual(invoice.edi_state, "sent", invoice.message_ids.mapped('body'))
        xml = fromstring(generated_files[0])
        namespaces = {
            'iedu': "http://www.sat.gob.mx/iedu"
        }
        iedu = xml.Conceptos.Concepto.ComplementoConcepto.xpath(
            '//iedu:instEducativas', namespaces=namespaces)
        self.assertTrue(iedu, 'Iedu complement was not added correctly')

    def test_l10n_mx_edi_xsd(self):
        """Verify that xsd file is downloaded"""
        self.invoice.company_id._load_xsd_attachments()
        xsd_file = self.ref('l10n_mx_edi.xsd_cached_iedu_xsd')
        self.assertTrue(xsd_file, 'XSD file not load')
