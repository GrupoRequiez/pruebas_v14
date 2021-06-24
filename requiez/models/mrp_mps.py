# -*- coding: utf-8 -*-

from collections import defaultdict, namedtuple
from math import log10

from odoo import api, fields, models, _
from odoo.tools.date_utils import add, subtract
from odoo.tools.float_utils import float_round
from odoo.osv.expression import OR, AND
from collections import OrderedDict


class MrpProductionSchedule(models.Model):
    _inherit = 'mrp.production.schedule'
    _name = 'mrp.production.schedule'

    def get_production_schedule_view_state(self):
        res = super(MrpProductionSchedule, self).get_production_schedule_view_state()
        if res:
            for r in res:
                product_id = r['product_id'][0]
                location_dest_id = r['warehouse_id'][0]
                default_location = self.env['stock.location'].search(
                    [('default_location', '=', 'True')], limit=1)
                index = 0
                for forecast_id in r['forecast_ids']:
                    # Get incoming product qty
                    incoming_product = 0
                    if index == 0:
                        domain = [
                            ('location_dest_id', 'child_of', default_location.id),
                            ('location_id', '=', 8),
                            ('product_id', '=', product_id),
                            ('state', 'not in', ('cancel', 'draft', 'done')),
                            ('date', '<=', forecast_id['date_stop'])]
                    elif index == 11:
                        domain = [
                            ('location_dest_id', 'child_of', default_location.id),
                            ('location_id', '=', 8),
                            ('product_id', '=', product_id),
                            ('state', 'not in', ('cancel', 'draft', 'done')),
                            ('date', '>=', forecast_id['date_start']),
                        ]
                    else:
                        domain = [
                            ('location_dest_id', 'child_of', default_location.id),
                            ('location_id', '=', 8),
                            ('product_id', '=', product_id),
                            ('state', 'not in', ('cancel', 'draft', 'done')),
                            ('date', '>=', forecast_id['date_start']),
                            ('date', '<=', forecast_id['date_stop'])]
                    move_ids = self.env['stock.move'].search(domain, order='date')
                    if move_ids:
                        incoming_product = sum(move.product_uom_qty for move in move_ids)
                    r['forecast_ids'][index]['incoming_product'] = incoming_product

                    # Get product compromise qty
                    product_compromise_qty = 0
                    if index == 0:
                        domain = [
                            ('stock_move_in_id.product_id', '=', product_id),
                            ('stock_move_in_id.date', '<=', forecast_id['date_stop']),
                            ('stock_move_in_id.state', '=', 'assigned')]
                    elif index == 11:
                        domain = [
                            ('stock_move_in_id.product_id', '=', product_id),
                            ('stock_move_in_id.date', '>=', forecast_id['date_start']),
                            ('stock_move_in_id.state', '=', 'assigned')]
                    else:
                        domain = [
                            ('stock_move_in_id.product_id', '=', product_id),
                            ('stock_move_in_id.date', '>=', forecast_id['date_start']),
                            ('stock_move_in_id.date', '<=', forecast_id['date_stop']),
                            ('stock_move_in_id.state', '=', 'assigned')]
                    compromise_ids = self.env['product.compromise'].search(domain)
                    if compromise_ids:
                        product_compromise_qty = sum(
                            compromise_id.qty_compromise for compromise_id in compromise_ids)
                    r['forecast_ids'][index]['product_compromise_qty'] = product_compromise_qty

                    # Get product reserve qty
                    product_reserve_qty = 0
                    stock_move_obj = self.env['stock.move']
                    if index == 0:
                        domain = [
                            ('product_id.id', '=', product_id),
                            ('state', 'in', ['assigned', 'confirmed', 'partially_available']),
                            ('location_id', '=', default_location.id),
                            ('date', '<=', forecast_id['date_stop'])
                        ]
                    elif index == 11:
                        domain = [
                            ('product_id.id', '=', product_id),
                            ('state', 'in', ['assigned', 'confirmed', 'partially_available']),
                            ('location_id', '=', default_location.id),
                            ('date', '>=', forecast_id['date_start']),
                        ]
                    else:
                        domain = [
                            ('product_id.id', '=', product_id),
                            ('state', 'in', ['assigned', 'confirmed', 'partially_available']),
                            ('location_id', '=', default_location.id),
                            ('date', '>=', forecast_id['date_start']),
                            ('date', '<=', forecast_id['date_stop'])
                        ]

                    stock_moves = stock_move_obj.search(domain)
                    product_reserve_qty = sum([move.reserved_availability
                                               for move in stock_moves])
                    r['forecast_ids'][index]['product_reserve_qty'] = product_reserve_qty
                    init_qty = r['forecast_ids'][index]['starting_inventory_qty'] + \
                        incoming_product - product_compromise_qty - \
                        product_reserve_qty - \
                        r['forecast_ids'][index]['replenish_qty'] - \
                        r['forecast_ids'][index]['outgoing_qty']
                    if index <= 10:
                        r['forecast_ids'][index+1]['starting_inventory_qty'] = init_qty
                    index += 1
        return res
