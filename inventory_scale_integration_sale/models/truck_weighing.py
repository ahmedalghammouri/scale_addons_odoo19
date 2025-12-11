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
            self.operation_type = 'outgoing'
            
            weighable_lines = self.sale_order_id.order_line.filtered(lambda l: l.product_id.is_weighable)
            if weighable_lines:
                first_line = weighable_lines[0]
                self.sale_line_id = first_line
                self.product_id = first_line.product_id
            
            existing_picking = self.env['stock.picking'].search([
                ('origin', '=', self.sale_order_id.name),
                ('state', 'in', ['draft', 'waiting', 'confirmed', 'assigned']),
                ('picking_type_code', '=', 'outgoing')
            ], limit=1)
            
            if existing_picking:
                self.delivery_id = existing_picking
        else:
            self.sale_line_id = False
    
    @api.onchange('sale_line_id')
    def _onchange_sale_line_id(self):
        if self.sale_line_id:
            self.product_id = self.sale_line_id.product_id
            self.sale_order_id = self.sale_line_id.order_id
    
    @api.onchange('delivery_id')
    def _onchange_delivery_id_sale(self):
        if self.delivery_id and self.delivery_id.origin:
            so = self.env['sale.order'].search([('name', '=', self.delivery_id.origin)], limit=1)
            if so:
                self.sale_order_id = so
    
    def action_view_sale_order(self):
        self.ensure_one()
        return {
            'name': 'Sale Order',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.sale_order_id.id,
        }
