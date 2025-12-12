# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class WeighingCashier(models.Model):
    _name = 'weighing.cashier'
    _description = 'Weighing Cashier Session'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    name = fields.Char(string='Session', compute='_compute_name', store=True)
    user_id = fields.Many2one('res.users', string='Operator', default=lambda self: self.env.user, required=True)
    scale_id = fields.Many2one('weighing.scale', string='Scale', required=True, domain="[('is_enabled', '=', True)]")
    state = fields.Selection([
        ('open', 'Open'),
        ('closed', 'Closed')
    ], default='open', string='Status')
    
    weighing_ids = fields.One2many('truck.weighing', 'cashier_session_id', string='Weighings')
    weighing_count = fields.Integer(compute='_compute_weighing_count')
    
    @api.depends('user_id', 'scale_id', 'create_date')
    def _compute_name(self):
        for rec in self:
            if rec.user_id and rec.scale_id:
                rec.name = f"{rec.user_id.name} - {rec.scale_id.name} - {fields.Datetime.now().strftime('%Y-%m-%d %H:%M')}"
            else:
                rec.name = 'New Session'
    
    @api.depends('weighing_ids')
    def _compute_weighing_count(self):
        for rec in self:
            rec.weighing_count = len(rec.weighing_ids)
    
    def action_close_session(self):
        self.state = 'closed'

class TruckWeighing(models.Model):
    _inherit = 'truck.weighing'
    
    cashier_session_id = fields.Many2one('weighing.cashier', string='Cashier Session', ondelete='set null')
    
    def action_quick_weigh_from_picking(self, picking_id):
        """Quick create weighing from picking - opens wizard if no truck"""
        picking = self.env['stock.picking'].browse(picking_id)
        
        weighable_moves = picking.move_ids.filtered(lambda m: m.product_id.is_weighable)
        if not weighable_moves:
            raise UserError(_("No weighable products found in this order."))
        
        if hasattr(picking, 'truck_id') and picking.truck_id:
            return self.action_quick_weigh_from_picking_with_truck(picking_id, picking.truck_id.id)
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Select Truck',
            'res_model': 'truck.selection.wizard',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
            'context': {'default_picking_id': picking_id}
        }
    
    def action_quick_weigh_from_picking_with_truck(self, picking_id, truck_id):
        """Create weighing from picking with specified truck"""
        picking = self.env['stock.picking'].browse(picking_id)
        weighable_moves = picking.move_ids.filtered(lambda m: m.product_id.is_weighable)
        
        vals = {
            'truck_id': truck_id,
            'partner_id': picking.partner_id.id,
            'product_id': weighable_moves[0].product_id.id,
            'operation_type': picking.picking_type_code,
            'picking_id': picking.id if picking.picking_type_code == 'incoming' else False,
            'delivery_id': picking.id if picking.picking_type_code == 'outgoing' else False,
            'scale_id': self.env.user.default_scale_id.id if self.env.user.default_scale_id else False,
        }
        
        # Try to link sale order or purchase order from origin
        if picking.origin:
            if 'sale_order_id' in self.env['truck.weighing']._fields:
                sale_order = self.env['sale.order'].search([('name', '=', picking.origin)], limit=1)
                if sale_order:
                    vals['sale_order_id'] = sale_order.id
            
            if 'purchase_order_id' in self.env['truck.weighing']._fields:
                purchase_order = self.env['purchase.order'].search([('name', '=', picking.origin)], limit=1)
                if purchase_order:
                    vals['purchase_order_id'] = purchase_order.id
        
        return self.create(vals)
    
    def action_scan_barcode(self, barcode):
        """Find weighing record by barcode"""
        weighing = self.search([('barcode', '=', barcode), ('state', '=', 'gross')], limit=1)
        if not weighing:
            raise UserError(_("No pending weighing found with barcode: %s") % barcode)
        return weighing
