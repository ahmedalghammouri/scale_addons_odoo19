# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class TruckWeighing(models.Model):
    _inherit = 'truck.weighing'
    
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order')
    purchase_line_id = fields.Many2one('purchase.order.line', string='Purchase Order Line')
    
    @api.onchange('purchase_order_id')
    def _onchange_purchase_order_id(self):
        if self.purchase_order_id:
            self.partner_id = self.purchase_order_id.partner_id
            self.operation_type = 'incoming'
            
            weighable_lines = self.purchase_order_id.order_line.filtered(lambda l: l.product_id.is_weighable)
            if weighable_lines:
                first_line = weighable_lines[0]
                self.purchase_line_id = first_line
                self.product_id = first_line.product_id
            
            existing_picking = self.env['stock.picking'].search([
                ('origin', '=', self.purchase_order_id.name),
                ('state', 'in', ['draft', 'waiting', 'confirmed', 'assigned']),
                ('picking_type_code', '=', 'incoming')
            ], limit=1)
            
            if existing_picking:
                self.picking_id = existing_picking
        else:
            self.purchase_line_id = False
    
    @api.onchange('purchase_line_id')
    def _onchange_purchase_line_id(self):
        if self.purchase_line_id:
            self.product_id = self.purchase_line_id.product_id
            self.purchase_order_id = self.purchase_line_id.order_id
    
    @api.onchange('picking_id')
    def _onchange_picking_id_purchase(self):
        if self.picking_id and self.picking_id.origin:
            po = self.env['purchase.order'].search([('name', '=', self.picking_id.origin)], limit=1)
            if po:
                self.purchase_order_id = po
    
    def action_view_purchase_order(self):
        self.ensure_one()
        return {
            'name': 'Purchase Order',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'res_id': self.purchase_order_id.id,
        }
