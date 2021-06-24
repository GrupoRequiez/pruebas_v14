from lxml.objectify import fromstring
from odoo.addons.l10n_mx_edi.tests.common import TestMxEdiCommon


class TestL10nMxEdiInvoiceSCP(TestMxEdiCommon):

    def test_l10n_mx_edi_invoice_scp(self):
        self.certificate._check_credentials()
        invoice = self.invoice
        invoice.write({
            'l10n_mx_edi_property': self.partner_a.id,
        })
        self.partner_a.write({
            'zip': '37440',
            'state_id': self.env.ref('base.state_mx_jal').id,
            'l10n_mx_edi_property_licence': '1234567',
        })
        invoice.action_post()
        generated_files = self._process_documents_web_services(self.invoice, {'cfdi_3_3'})
        self.assertTrue(generated_files)
        self.assertEqual(invoice.edi_state, "sent", invoice.message_ids.mapped('body'))
        xml = fromstring(generated_files[0])
        namespaces = {
            'servicioparcial': 'http://www.sat.gob.mx/servicioparcialconstruccion'}
        scp = xml.Complemento.xpath('//servicioparcial:parcialesconstruccion',
                                    namespaces=namespaces)
        self.assertTrue(scp, 'Complement to SCP not added correctly')
