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
            weighings = self.env['truck.weighing'].search([('picking_id', '=', picking.id)])
            if weighings:
                picking.weighing_count = len(weighings)
                picking.total_net_weight = sum(weighings.mapped('net_weight'))
                if picking.total_net_weight > 2000:
                    picking.total_net_weight_display = f"{picking.total_net_weight / 1000:.1f} T"
                else:
                    picking.total_net_weight_display = f"{picking.total_net_weight:.0f} KG"
            else:
                picking.weighing_count = 0
                picking.total_net_weight = 0.0
                picking.total_net_weight_display = "0 KG"

    def action_view_weighing_records(self):
        self.ensure_one()
        if self.picking_type_code == 'incoming':
            context = {
                'default_partner_id': self.partner_id.id,
                'default_picking_id': self.id,
                'default_operation_type': 'incoming',
                'create': True
            }
            return {
                'name': 'Weighing Records',
                'type': 'ir.actions.act_window',
                'res_model': 'truck.weighing',
                'view_mode': 'list,form',
                'domain': [('picking_id', '=', self.id)],
                'context': context
            }
        return super().action_view_weighing_records()
