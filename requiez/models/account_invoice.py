# -*- coding: utf-8 -*-
# Copyright 2018 Vauxoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import fields, models
_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'
    _name = 'account.move'

    date_payment = fields.Datetime('Payment Date',)
    prioritized = fields.Boolean('Prioritized', readonly=True)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    _name = 'account.move.line'

    _sql_constraints = [
        ('check_amount_currency_balance_sign', CHECK(1=1), "Test _sql_constraints"),
    ]
