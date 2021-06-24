from odoo.addons.l10n_mx_edi.tests.common import InvoiceTransactionCase
from odoo.tests import tagged


@tagged('download_zipped_cfdi')
class TestDownloadZippedCFDI(InvoiceTransactionCase):

    def setUp(self):
        super(TestDownloadZippedCFDI, self).setUp()
        self.product.l10n_mx_edi_code_sat_id = self.ref(
            'l10n_mx_edi.prod_code_sat_01010101')
        isr_tag = self.env['account.account.tag'].search(
            [('name', '=', 'ISR')])
        for rep_line in self.tax_negative.invoice_repartition_line_ids:
            rep_line.tag_ids |= isr_tag

    def test_01_download_zipped_invoice(self):
        """Test case: a user clicks the DOWNLOAD ZIP button located at my/invoices, the result is the authomatic
        download of a folder containing the pdf and xml of the current invoice"""
        invoice = self.create_invoice()
        invoice.action_post()
        url = "/my/invoices/%s" % invoice.id
        tour = 'check_download_zipped_cfdi'
        self.phantom_js(
            url_path=url,
            code="odoo.__DEBUG__.services['web_tour.tour'].run('%s')" % tour,
            ready="odoo.__DEBUG__.services['web_tour.tour'].tours.%s.ready" % tour,
            login="admin")
