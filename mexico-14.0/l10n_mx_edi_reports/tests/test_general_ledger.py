# Part of Odoo. See LICENSE file for full copyright and licensing details.

from os.path import join
from dateutil.relativedelta import relativedelta
from lxml import objectify
from odoo.addons.l10n_mx_edi.tests.common import TestMxEdiCommon
from odoo import fields
from odoo.tools import misc
from odoo.tests.common import Form


class TestJournalEntryReport(TestMxEdiCommon):

    def setUp(self):
        super().setUp()
        self.report_moves = self.env['l10n_mx.general.ledger.report']
        self.payments_model = self.env['account.payment.register']
        self.payment_obj = self.env['account.payment']
        self.journal_bank = self.env['account.journal'].search(
            [('type', '=', 'bank'),
             ('company_id', '=', self.invoice.company_id.id)], limit=1)
        self.date = fields.Datetime.context_timestamp(
            self.journal_bank, fields.Datetime.from_string(
                fields.Datetime.now())).replace(day=15)
        self.date = self.date - relativedelta(months=1)
        self.xml_expected_str = misc.file_open(join(
            'l10n_mx_edi_reports', 'tests', 'expected_moves.xml')
        ).read().encode('UTF-8')
        self.payment_method_manual_out = self.env.ref(
            'account.account_payment_method_manual_out')
        self.transfer = self.env.ref(
            'l10n_mx_edi.payment_method_transferencia')
        self.bank_account = self.env.ref('account_bank_statement_import.ofx_partner_bank_1').sudo().copy({
            'company_id': self.invoice.company_id.id})
        journal_acc = self.env['res.partner.bank'].create({
            'acc_number': '123456789012345',
            'bank_id': self.ref('l10n_mx.acc_bank_012_BBVA_BANCOMER'),
            'partner_id': self.journal_bank.company_id.partner_id.id,
            'company_id': self.journal_bank.company_id.id,
        })
        self.journal_bank.bank_account_id |= journal_acc
        self.certificate._check_credentials()

    def test_general_ledger_report(self):
        self.product.taxes_id = False
        invoice = self.invoice
        invoice.currency_id = self.env.ref('base.MXN')
        invoice.invoice_date = self.date.date()
        invoice.with_context(
            check_move_validity=False)._onchange_invoice_date()
        invoice.invoice_payment_term_id = self.env.ref('account.account_payment_term_end_following_month')
        invoice._onchange_invoice_date()
        move_form = Form(invoice)
        with move_form.invoice_line_ids.edit(0) as line_form:
            line_form.product_uom_id = invoice.invoice_line_ids.product_id.uom_id
            line_form.tax_ids.clear()
        move_form.save()
        invoice.action_post()
        self.env['account.edi.document'].sudo().with_context(edi_test_mode=False).search(
            [('state', 'in', ('to_send', 'to_cancel'))])._process_documents_web_services()
        payment = self.generate_payment(invoice)
        self.env['account.edi.document'].sudo().with_context(edi_test_mode=False).search(
            [('state', 'in', ('to_send', 'to_cancel'))])._process_documents_web_services()
        options = self.report_moves._get_options()
        date = self.date.strftime('%Y-%m-%d')
        options.get('date', {})['date_from'] = date
        options.get('date', {})['date_to'] = date
        data = self.report_moves.get_xml(options)
        xml = objectify.fromstring(data)
        xml.attrib['Sello'] = ''
        xml.attrib['Certificado'] = ''
        xml.attrib['noCertificado'] = ''
        xml_dt = self.xml2dict(xml)
        self.xml_expected_str = self.xml_expected_str.decode().format(
            concept1=invoice.name, date=date, move1=invoice.id,
            uuid_inv=invoice.l10n_mx_edi_cfdi_uuid,
            payment_date=payment.date,
            uuid2=payment.l10n_mx_edi_cfdi_uuid,
            move2=payment.id,
            concept2=payment.ref,
        )
        xml_expected = objectify.fromstring(self.xml_expected_str.encode('utf-8'))
        xml_expected.attrib['Mes'] = self.date.strftime('%m')
        xml_expected.attrib['Anio'] = self.date.strftime('%Y')
        xml_expected_dt = self.xml2dict(xml_expected)
        self.maxDiff = None
        self.assertEqual(xml_dt, xml_expected_dt)
        # Check the first payment
        xml.remove(xml.getchildren()[0])
        xml_expected.remove(xml_expected.getchildren()[0])
        xml_dt = self.xml2dict(xml)
        xml_expected_dt = self.xml2dict(xml_expected)
        self.assertEqual(xml_dt, xml_expected_dt)

    def generate_payment(self, invoice):
        statement = self.env['account.bank.statement'].with_context(edi_test_mode=True).create({
            'name': 'test_statement',
            'date': invoice.invoice_date,
            'journal_id': self.journal_bank.id,
            'currency_id': invoice.currency_id,
            'line_ids': [
                (0, 0, {
                    'payment_ref': 'mx_st_line',
                    'partner_id': self.partner_a.id,
                    'amount': invoice.amount_total,
                    'l10n_mx_edi_payment_method_id': self.env.ref('l10n_mx_edi.payment_method_efectivo').id,
                }),
            ],
        })
        statement.button_post()
        receivable_line = invoice.line_ids.filtered(lambda line: line.account_internal_type == 'receivable')
        statement.line_ids.reconcile([{'id': receivable_line.id}])
        return statement.line_ids.move_id

    def xml2dict(self, xml):
        """Receive 1 lxml etree object and return a dict string.
        This method allow us have a precise diff output"""
        def recursive_dict(element):
            return (element.tag,
                    dict((recursive_dict(e) for e in element.getchildren()),
                         ____text=(element.text or '').strip(), **element.attrib))
        return dict([recursive_dict(xml)])
