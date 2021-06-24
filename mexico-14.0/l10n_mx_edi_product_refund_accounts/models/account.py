from odoo import models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _get_computed_account(self):
        if self.move_id.move_type not in (
                'out_refund', 'in_refund') or not self.product_id:
            return super(AccountMoveLine, self)._get_computed_account()
        fpos = self.move_id.fiscal_position_id
        accounts = self.product_id.product_tmpl_id.get_product_accounts(fpos)
        account_map = {
            'out_refund': 'income_refund',
            'in_refund': 'expense_refund',
        }
        return accounts[account_map[self.move_id.move_type]]
