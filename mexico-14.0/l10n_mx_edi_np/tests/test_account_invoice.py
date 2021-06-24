from lxml.objectify import fromstring

from odoo.addons.l10n_mx_edi.tests.common import TestMxEdiCommon


class TestL10nMxEdiInvoiceNP(TestMxEdiCommon):

    def setUp(self):
        super(TestL10nMxEdiInvoiceNP, self).setUp()
        self.user_billing.partner_id.write({
            'l10n_mx_edi_curp': 'TICE700419HCLJND07'})
        self.invoice.company_id.write({'company_registry': '123'})
        self.client = self.env['res.partner'].create({
            'name': 'Pablo, Perez',
            'vat': 'XEXX010101000',
            'l10n_mx_edi_curp': 'AAAA010101HCLJND07',
        })
        self.buyer = self.env['res.partner'].create({
            'name': 'Juan, Lopez',
            'vat': 'AAAA010101AAA',
        })
        self.rs_property = self.env['res.partner'].create({
            'type': 'other',
            'name': 'Apartment',
            'street': 'South street',
            'city': 'South city',
            'state_id': self.ref('base.state_mx_ags'),
            'zip': '20541',
            'country_id': self.ref('base.mx'),
            'comment': '03',
            'parent_id': self.client.id,
            'ref': '25000.98|10'
        })
        self.certificate._check_credentials()

    def test_l10n_mx_edi_np_single(self):
        invoice = self.invoice
        invoice.write({
            'partner_id': self.client.id,
            'l10n_mx_edi_np_partner_id': self.buyer.id,
            'name': '1234',
        })
        invoice.action_post()
        generated_files = self._process_documents_web_services(self.invoice, {'cfdi_3_3'})
        self.assertTrue(generated_files)
        self.assertEqual(invoice.edi_state, "sent", invoice.message_ids.mapped('body'))
        xml = fromstring(generated_files[0])
        namespaces = {
            'notariospublicos': 'http://www.sat.gob.mx/notariospublicos'}
        comp = xml.Complemento.xpath('//notariospublicos:NotariosPublicos',
                                     namespaces=namespaces)
        self.assertTrue(comp, 'Notary Public Complement not added correctly')

    def test_l10n_mx_edi_np_multiple(self):
        self.client.category_id = [self.ref('l10n_mx_edi_np.l10n_mx_edi_np_partnership')] # noqa
        self.client.comment = '50'
        self.env['res.partner'].create({
            'name': 'Julia, Gonzalez',
            'vat': 'XEXX010101000',
            'l10n_mx_edi_curp': 'AAAA010101HCLJND07',
            'parent_id': self.client.id,
            'comment': '50',
        })
        self.buyer.category_id = [self.ref('l10n_mx_edi_np.l10n_mx_edi_np_partnership')] # noqa
        self.buyer.comment = '50'
        self.env['res.partner'].create({
            'name': 'Miguel, Pinto',
            'vat': 'XEXX010101000',
            'parent_id': self.buyer.id,
            'comment': '50',
        })
        invoice = self.invoice
        invoice.write({
            'partner_id': self.client.id,
            'l10n_mx_edi_np_partner_id': self.buyer.id,
            'name': '1234',
        })
        invoice.action_post()
        generated_files = self._process_documents_web_services(self.invoice, {'cfdi_3_3'})
        self.assertTrue(generated_files)
        self.assertEqual(invoice.edi_state, "sent", invoice.message_ids.mapped('body'))
        xml = fromstring(generated_files[0])
        namespaces = {
            'notariospublicos': 'http://www.sat.gob.mx/notariospublicos'}
        comp1 = xml.Complemento.xpath(
            '//notariospublicos:DatosEnajenantesCopSC', namespaces=namespaces)
        comp2 = xml.Complemento.xpath(
            '//notariospublicos:DatosAdquirientesCopSC', namespaces=namespaces)
        self.assertTrue(comp1 and comp2,
                        'Notary Public Complement not added correctly')
