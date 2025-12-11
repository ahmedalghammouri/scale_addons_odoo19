# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class TruckWeighing(models.Model):
    _inherit = 'truck.weighing'
    
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', ondelete='restrict', tracking=True)
    sale_line_id = fields.Many2one('sale.order.line', string='Sale Order Line', ondelete='restrict')
    
    @api.onchange('sale_order_id')
    def _onchange_sale_order_id(self):
        if self.sale_order_id:
            self.partner_id = self.sale_order_id.partner_id
            for line in self.sale_order_id.order_line.filtered(lambda l: l.product_id.is_weighable):
                remaining_qty = line.product_uom_qty - line.qty_delivered
                if remaining_qty > 0:
                    self.sale_line_id = line
                    self.product_id = line.product_id
                    break
            
            existing_picking = self.env['stock.picking'].search([
                ('origin', '=', self.sale_order_id.name),
                ('state', 'in', ['draft', 'waiting', 'confirmed', 'assigned']),
                ('picking_type_code', '=', 'outgoing')
            ], limit=1)
            
            if existing_picking:
                self.delivery_id = existing_picking
    
    @api.onchange('sale_line_id')
    def _onchange_sale_line_id(self):
        if self.sale_line_id:
            self.product_id = self.sale_line_id.product_id
            self.sale_order_id = self.sale_line_id.order_id
    
    def action_view_sale_order(self):
        self.ensure_one()
        return {
            'name': 'Sale Order',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.sale_order_id.id,
        }
