from odoo.addons.l10n_mx_edi.tests.common import InvoiceTransactionCase


class TestL10nMxInvoiceTaxImportation(InvoiceTransactionCase):

    def setUp(self):
        super().setUp()
        self.env['base.language.install'].create(
            {'lang': 'es_MX', 'overwrite': 1}).lang_install()
        self.imp_product = self.env.ref(
            'l10n_mx_import_taxes.product_tax_importation')
        self.imp_tax = self.env.ref('l10n_mx_import_taxes.tax_importation')
        self.journal_payment = self.env['account.journal'].search(
            [('code', '=', 'CSH1'),
             ('type', '=', 'cash'),
             ('company_id', '=', self.company.id)],
            limit=1)

    def test_case_with_tax_importation(self):
        foreing_invoice = self.create_invoice('in_invoice', self.mxn.id)
        foreing_invoice.tax_line_ids.filtered('manual').unlink()
        foreing_invoice.invoice_line_ids.write({
            'invoice_line_tax_ids': False,
        })
        foreing_invoice.compute_taxes()
        foreing_invoice.action_invoice_open()
        invoice = self.create_invoice('in_invoice', self.mxn.id)
        invoice.tax_line_ids.filtered('manual').unlink()
        invoice.invoice_line_ids.write({
            'invoice_line_tax_ids': [(6, 0, self.imp_tax.ids)],
            'product_id': self.imp_product.id,
            'quantity': 0.0,
            'price_unit': 76.0,
            'x_l10n_mx_edi_invoice_broker_id': foreing_invoice.id,
        })
        invoice.compute_taxes()
        invoice.journal_id.sudo().update_posted = True
        invoice.action_invoice_open()
        invoice.pay_and_reconcile(
            self.journal_payment, pay_amount=invoice.amount_total,
            date=invoice.date_invoice)
        # Get DIOT report
        invoice.sudo().partner_id.commercial_partner_id.l10n_mx_type_of_operation = '85'  # noqa
        self.diot_report = self.env['l10n_mx.account.diot']
        options = self.diot_report.get_options()
        options.get('date', {})['date_from'] = invoice.date_invoice
        options.get('date', {})['date_to'] = invoice.date_invoice
        data = self.diot_report.get_txt(options)
        self.assertEqual(
            data, '05|85|||Agrolait|BE|Belga||||||||76|||||||||\n',
            "Error with tax importation DIOT")
