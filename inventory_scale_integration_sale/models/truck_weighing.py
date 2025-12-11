# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class TruckWeighing(models.Model):
    _inherit = 'truck.weighing'

    # Sales Links (stock fields inherited from purchase module)
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', ondelete='restrict', tracking=True)
    sale_line_id = fields.Many2one('sale.order.line', string='Sale Order Line', ondelete='restrict')
    
    # Readonly flags for sales
    is_so_readonly = fields.Boolean(compute='_compute_so_readonly_flags')
    
    @api.depends('picking_id', 'sale_order_id')
    def _compute_so_readonly_flags(self):
        for record in self:
            record.is_so_readonly = bool(record.picking_id)
    
    @api.onchange('picking_id')
    def _onchange_picking_id(self):
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
                if hasattr(move, 'sale_line_id') and move.sale_line_id:
                    if not self.sale_line_id:
                        self.sale_line_id = move.sale_line_id
                    if not self.sale_order_id:
                        self.sale_order_id = move.sale_line_id.order_id
                elif self.picking_id.origin and not self.sale_order_id:
                    so = self.env['sale.order'].search([('name', '=', self.picking_id.origin)], limit=1)
                    if so:
                        self.sale_order_id = so
                        if not self.sale_line_id:
                            so_line = so.order_line.filtered(lambda l: l.product_id == move.product_id)
                            if so_line:
                                self.sale_line_id = so_line[0]


    @api.onchange('sale_order_id')
    def _onchange_sale_order_id(self):
        if self.sale_order_id:
            if not self.partner_id:
                self.partner_id = self.sale_order_id.partner_id
            if not self.sale_line_id or not self.product_id:
                for line in self.sale_order_id.order_line.filtered(lambda l: l.product_id.is_weighable):
                    remaining_qty = line.product_uom_qty - line.qty_delivered
                    if remaining_qty > 0:
                        if not self.sale_line_id:
                            self.sale_line_id = line
                        if not self.product_id:
                            self.product_id = line.product_id
                        break
            
            if not self.picking_id:
                existing_picking = self.env['stock.picking'].search([
                    ('origin', '=', self.sale_order_id.name),
                    ('state', 'in', ['draft', 'waiting', 'confirmed', 'assigned']),
                    ('picking_type_code', '=', 'outgoing')
                ], limit=1)
                
                if existing_picking:
                    self.picking_id = existing_picking
                else:
                    self._create_draft_delivery_from_so()

    @api.onchange('sale_line_id')
    def _onchange_sale_line_id(self):
        if self.sale_line_id:
            if not self.product_id:
                self.product_id = self.sale_line_id.product_id
            if not self.sale_order_id:
                self.sale_order_id = self.sale_line_id.order_id

    def _create_draft_delivery_from_so(self):
        """ Create draft delivery from sale order """
        if not self.sale_order_id:
            return
        
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'outgoing'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)
        
        if not picking_type:
            return
        
        location_dest = self.sale_order_id.partner_id.property_stock_customer
        
        picking = self.env['stock.picking'].create({
            'partner_id': self.partner_id.id,
            'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': location_dest.id,
            'origin': self.sale_order_id.name,
        })
        
        # Create moves for lines with remaining quantity
        for line in self.sale_order_id.order_line:
            remaining_qty = line.product_uom_qty - line.qty_delivered
            if remaining_qty > 0:
                self.env['stock.move'].create({
                    'product_id': line.product_id.id,
                    'product_uom_qty': remaining_qty,
                    'product_uom': line.product_id.uom_id.id,
                    'picking_id': picking.id,
                    'location_id': picking_type.default_location_src_id.id,
                    'location_dest_id': location_dest.id,
                    'sale_line_id': line.id,
                })
        
        picking.action_confirm()
        self.picking_id = picking
        self.location_dest_id = location_dest

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('picking_id') and not vals.get('sale_order_id'):
                picking = self.env['stock.picking'].browse(vals['picking_id'])
                weighable_moves = picking.move_ids.filtered(lambda m: m.product_id.is_weighable)
                if weighable_moves and hasattr(weighable_moves[0], 'sale_line_id') and weighable_moves[0].sale_line_id:
                    vals['sale_line_id'] = weighable_moves[0].sale_line_id.id
                    vals['sale_order_id'] = weighable_moves[0].sale_line_id.order_id.id
        return super(TruckWeighing, self).create(vals_list)

    def action_view_sale_order(self):
        self.ensure_one()
        return {
            'name': 'Sale Order',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.sale_order_id.id,
        }
    
