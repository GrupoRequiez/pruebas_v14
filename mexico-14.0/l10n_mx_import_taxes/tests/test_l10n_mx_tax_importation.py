from odoo.addons.l10n_mx_edi.tests.common import TestMxEdiCommon
from odoo.tests import tagged
from odoo.tests.common import Form


@tagged('post_install', '-at_install')
class TestL10nMxInvoiceTaxImportation(TestMxEdiCommon):

    def setUp(self):
        super().setUp()
        company = self.invoice.company_id
        self.imp_product = self.env.ref('l10n_mx_import_taxes.product_tax_importation')
        imp_tax = self.env.ref('l10n_mx_import_taxes.tax_importation')
        account = imp_tax.sudo().cash_basis_transition_account_id.copy({'company_id': company.id})
        self.imp_tax = imp_tax.sudo().copy({
            'company_id': company.id,
            'cash_basis_transition_account_id': account.id,
        })
        self.journal_payment = self.env['account.journal'].search(
            [('code', '=', 'CSH1'),
             ('type', '=', 'cash'),
             ('company_id', '=', company.id)], limit=1)
        self.invoice_journal = self.env['account.journal'].search(
            [('code', '=', 'BILL'),
             ('type', '=', 'purchase'),
             ('company_id', '=', company.id)], limit=1)

    def test_case_with_tax_importation(self):
        foreign_invoice = self.invoice
        foreign_invoice.write({
            'move_type': 'in_invoice',
            'currency_id': self.env.ref('base.MXN'),
        })
        move_form = Form(foreign_invoice)
        with move_form.invoice_line_ids.edit(0) as line_form:
            line_form.tax_ids.clear()
        move_form.save()
        self._validate_invoice(foreign_invoice, False)
        self.partner_a.write({
            'country_id': self.env.ref('base.mx').id,
            'vat': 'VAU111017CG9',
        })
        invoice = self.invoice.copy()
        move_form = Form(invoice)
        with move_form.invoice_line_ids.edit(0) as line_form:
            line_form.tax_ids.add(self.imp_tax)
            line_form.product_id = self.imp_product
            line_form.quantity = 0.0
            line_form.price_unit = 450.00
            line_form.l10n_mx_edi_invoice_broker_id = foreign_invoice
        move_form.save()
        self._validate_invoice(invoice)
        # Get DIOT report
        invoice.sudo().partner_id.commercial_partner_id.l10n_mx_type_of_operation = '85'
        self.diot_report = self.env['l10n_mx.account.diot']
        options = self.diot_report._get_options()
        options.get('date', {})['date_from'] = invoice.invoice_date
        options.get('date', {})['date_to'] = invoice.invoice_date
        data = self.diot_report.get_txt(options)
        self.assertEqual(
            data, '05|85|||Deco Addict|US|Americano|||||||||450|||||||||\n',
            "Error with tax importation DIOT")

    def _validate_invoice(self, invoice, pay=True):
        invoice.action_post()
        if pay:
            payment_register = Form(self.env['account.payment'].with_context(
                active_model='account.move', active_ids=invoice.ids))
            payment_register.date = invoice.invoice_date
            payment_register.l10n_mx_edi_payment_method_id = self.env.ref('l10n_mx_edi.payment_method_efectivo')
            payment_register.payment_method_id = self.env.ref('account.account_payment_method_manual_in')
            payment_register.journal_id = self.journal_payment
            payment_register.amount = invoice.amount_total
            payment = payment_register.save()
            payment.action_post()
        return invoice
