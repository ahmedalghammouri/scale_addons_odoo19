# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class TruckWeighing(models.Model):
    _inherit = 'truck.weighing'

    # Purchase Links
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order')
    purchase_line_id = fields.Many2one('purchase.order.line', string='Purchase Order Line')
    
    # Readonly flags
    is_po_readonly = fields.Boolean(compute='_compute_readonly_flags')
    is_product_readonly = fields.Boolean(compute='_compute_readonly_flags')
    
    @api.depends('picking_id', 'purchase_order_id')
    def _compute_readonly_flags(self):
        for record in self:
            record.is_po_readonly = bool(record.picking_id)
            record.is_product_readonly = bool(record.picking_id or record.purchase_order_id)
    
    @api.onchange('picking_id')
    def _onchange_picking_id_(self):
        if self.picking_id:
            if not self.partner_id:
                self.partner_id = self.picking_id.partner_id
            if not self.location_dest_id:
                self.location_dest_id = self.picking_id.location_dest_id
            if not self.operation_type:
                self.operation_type = 'incoming' if self.picking_id.picking_type_code == 'incoming' else 'outgoing'
            weighable_moves = self.picking_id.move_ids.filtered(lambda m: m.product_id.is_weighable)
            if weighable_moves:
                move = weighable_moves[0]
                if not self.product_id:
                    self.product_id = move.product_id
                if hasattr(move, 'purchase_line_id') and move.purchase_line_id:
                    if not self.purchase_line_id:
                        self.purchase_line_id = move.purchase_line_id
                    if not self.purchase_order_id:
                        self.purchase_order_id = move.purchase_line_id.order_id
                elif self.picking_id.origin and not self.purchase_order_id:
                    po = self.env['purchase.order'].search([('name', '=', self.picking_id.origin)], limit=1)
                    if po:
                        self.purchase_order_id = po
                        if not self.purchase_line_id:
                            po_line = po.order_line.filtered(lambda l: l.product_id == move.product_id)
                            if po_line:
                                self.purchase_line_id = po_line[0]

    @api.onchange('purchase_order_id')
    def _onchange_purchase_order_id(self):
        if self.purchase_order_id:
            if not self.partner_id:
                self.partner_id = self.purchase_order_id.partner_id
            if not self.purchase_line_id or not self.product_id:
                for line in self.purchase_order_id.order_line.filtered(lambda l: l.product_id.is_weighable):
                    remaining_qty = line.product_qty - line.qty_received
                    if remaining_qty > 0:
                        if not self.purchase_line_id:
                            self.purchase_line_id = line
                        if not self.product_id:
                            self.product_id = line.product_id
                        break
            
            if not self.picking_id:
                existing_picking = self.env['stock.picking'].search([
                    ('origin', '=', self.purchase_order_id.name),
                    ('state', 'in', ['draft', 'waiting', 'confirmed', 'assigned']),
                    ('picking_type_code', '=', 'incoming')
                ], limit=1)
                
                if existing_picking:
                    self.picking_id = existing_picking
                else:
                    self._create_draft_receipt_from_po()

    @api.onchange('purchase_line_id')
    def _onchange_purchase_line_id(self):
        if self.purchase_line_id:
            if not self.product_id:
                self.product_id = self.purchase_line_id.product_id
            if not self.purchase_order_id:
                self.purchase_order_id = self.purchase_line_id.order_id

    def _create_draft_receipt_from_po(self):
        """ Create draft receipt from purchase order """
        if not self.purchase_order_id:
            return
        
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'incoming'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)
        
        if not picking_type:
            return
        
        location_dest = picking_type.default_location_dest_id
        
        picking = self.env['stock.picking'].create({
            'partner_id': self.partner_id.id,
            'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': location_dest.id,
            'origin': self.purchase_order_id.name,
        })
        
        # Create moves for lines with remaining quantity
        for line in self.purchase_order_id.order_line:
            remaining_qty = line.product_qty - line.qty_received
            if remaining_qty > 0:
                self.env['stock.move'].create({
                    'product_id': line.product_id.id,
                    'product_uom_qty': remaining_qty,
                    'product_uom': line.product_id.uom_id.id,
                    'picking_id': picking.id,
                    'location_id': picking_type.default_location_src_id.id,
                    'location_dest_id': location_dest.id,
                    'purchase_line_id': line.id,
                })
        
        picking.action_confirm()
        self.picking_id = picking
        self.location_dest_id = location_dest

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('picking_id') and not vals.get('purchase_order_id'):
                picking = self.env['stock.picking'].browse(vals['picking_id'])
                weighable_moves = picking.move_ids.filtered(lambda m: m.product_id.is_weighable)
                if weighable_moves and hasattr(weighable_moves[0], 'purchase_line_id') and weighable_moves[0].purchase_line_id:
                    vals['purchase_line_id'] = weighable_moves[0].purchase_line_id.id
                    vals['purchase_order_id'] = weighable_moves[0].purchase_line_id.order_id.id
        return super(TruckWeighing, self).create(vals_list)

    def action_view_purchase_order(self):
        self.ensure_one()
        return {
            'name': 'Purchase Order',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'res_id': self.purchase_order_id.id,
        }