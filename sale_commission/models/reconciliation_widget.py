# -*- coding: utf-8 -*-

import copy
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import pycompat
from odoo.tools.misc import formatLang
from odoo.tools import misc


class AccountReconciliation(models.AbstractModel):
    _inherit = 'account.reconciliation.widget'

    @api.model
    def process_bank_statement_line(self, st_line_ids, data):
        """ Handles data sent from the bank statement reconciliation widget
            (and can otherwise serve as an old-API bridge)

            :param st_line_ids
            :param list of dicts data: must contains the keys
                'counterpart_aml_dicts', 'payment_aml_ids' and 'new_aml_dicts',
                whose value is the same as described in process_reconciliation
                except that ids are used instead of recordsets.
        """
        st_lines = self.env['account.bank.statement.line'].browse(st_line_ids)
        AccountMoveLine = self.env['account.move.line']
        AccountBankStatement = self.env['account.bank.statement']
        ctx = dict(self._context, force_price_include=False)

        for st_line, datum in pycompat.izip(st_lines, copy.deepcopy(data)):
            payment_aml_rec = AccountMoveLine.browse(
                datum.get('payment_aml_ids', []))

            for aml_dict in datum.get('counterpart_aml_dicts', []):
                aml_dict['move_line'] = AccountMoveLine.browse(
                    aml_dict['counterpart_aml_id'])
                del aml_dict['counterpart_aml_id']

            if datum.get('partner_id') is not None:
                st_line.write({'partner_id': datum['partner_id']})

            st_line.with_context(ctx).process_reconciliation(
                datum.get('counterpart_aml_dicts', []),
                payment_aml_rec,
                datum.get('new_aml_dicts', []))

            statement_id = AccountBankStatement.search(
                [('id', '=', st_line.statement_id.id)])
            for move_line in statement_id.move_line_ids:
                for invoice in move_line.payment_id.invoice_ids:
                    if invoice.type == "out_invoice":
                        self.env['account.association'].create({
                            'invoice_id': invoice.id,
                            'move_line_id': move_line.id,
                            'date': fields.datetime.now(),
                        })

    @api.model
    def process_move_lines(self, data):
        """ Used to validate a batch of reconciliations in a single call
            :param data: list of dicts containing:
                - 'type': either 'partner' or 'account'
                - 'id': id of the affected res.partner or account.account
                - 'mv_line_ids': ids of existing account.move.line to reconcile
                - 'new_mv_line_dicts': list of dicts containing values suitable for account_move_line.create()
        """

        Partner = self.env['res.partner']
        Account = self.env['account.account']

        for datum in data:
            if len(datum['mv_line_ids']) >= 1 or len(datum['mv_line_ids']) + len(datum['new_mv_line_dicts']) >= 2:
                self._process_move_lines(
                    datum['mv_line_ids'], datum['new_mv_line_dicts'])

            if datum['type'] == 'partner':
                partners = Partner.browse(datum['id'])
                partners.mark_as_reconciled()
            if datum['type'] == 'account':
                accounts = Account.browse(datum['id'])
                accounts.mark_as_reconciled()

            # AccountBankStatement = self.env['account.bank.statement']
            # statement_id = AccountBankStatement.search(
            #     [('move_line_ids', 'in', datum['mv_line_ids'])])
            AccountMoveLine = self.env['account.move.line']
            move_lines = AccountMoveLine.search(
                [('id', 'in', datum['mv_line_ids'])])
            for move_line in move_lines:
                for invoice in move_line.payment_id.invoice_ids:
                    if invoice.type == "out_invoice":
                        self.env['account.association'].create({
                            'invoice_id': invoice.id,
                            'move_line_id': move_line.id,
                            'date': fields.datetime.now(),
                        })
