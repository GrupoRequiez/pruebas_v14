# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Odoo Mexican Localization Import Taxes",
    "summary": """
        Allows to properly link the Foreign Partner to the Import Taxes paid by
    a broker on behalf of my company
    """,
    "version": "14.0.1.0.0",
    "author": "Vauxoo",
    "category": "Accounting",
    "website": "http://www.vauxoo.com",
    "license": "LGPL-3",
    "depends": [
        "account_tax_python",
        "l10n_mx_edi",
        "l10n_mx_reports",
    ],
    "demo": [
        "demo/account_tax_demo.xml",
        "demo/product_demo.xml",
    ],
    "data": [
        "views/account_invoice_view.xml",
    ],
    "installable": True,
    "auto_install": False,
}
