# -*- coding: utf-8 -*-
from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    weighing_count = fields.Integer(compute='_compute_weighing_data')
    total_net_weight = fields.Float(compute='_compute_weighing_data', string='Total Net Weight')
    total_net_weight_display = fields.Char(compute='_compute_weighing_data', string='Weight Display')
    has_weighable_products = fields.Boolean(compute='_compute_has_weighable_products')

    @api.depends('move_ids.product_id.is_weighable')
    def _compute_has_weighable_products(self):
        for picking in self:
            picking.has_weighable_products = any(move.product_id.is_weighable for move in picking.move_ids)

    def _compute_weighing_data(self):
        for picking in self:
            weighings_in = self.env['truck.weighing'].search([('picking_id', '=', picking.id)])
            weighings_out = self.env['truck.weighing'].search([('delivery_id', '=', picking.id)])
            all_weighings = weighings_in | weighings_out
            picking.weighing_count = len(all_weighings)
            picking.total_net_weight = sum(all_weighings.mapped('net_weight'))
            if picking.total_net_weight > 2000:
                picking.total_net_weight_display = f"{picking.total_net_weight / 1000:.1f} T"
            else:
                picking.total_net_weight_display = f"{picking.total_net_weight:.0f} KG"

    def action_view_weighing_records(self):
        self.ensure_one()
        if self.picking_type_code == 'incoming':
            return super().action_view_weighing_records()
        context = {
            'default_partner_id': self.partner_id.id,
            'default_delivery_id': self.id,
            'default_operation_type': 'outgoing',
            'create': True
        }
        return {
            'name': 'Weighing Records',
            'type': 'ir.actions.act_window',
            'res_model': 'truck.weighing',
            'view_mode': 'list,form',
            'domain': [('delivery_id', '=', self.id)],
            'context': context
        }
