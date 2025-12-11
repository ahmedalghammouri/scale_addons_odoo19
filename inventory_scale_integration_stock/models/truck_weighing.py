# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class TruckWeighing(models.Model):
    _inherit = 'truck.weighing'
    
    picking_id = fields.Many2one('stock.picking', string='Receipt', ondelete='restrict', tracking=True)
    delivery_id = fields.Many2one('stock.picking', string='Delivery', ondelete='restrict', tracking=True, domain="[('picking_type_code', '=', 'outgoing')]")
    location_dest_id = fields.Many2one('stock.location', string='Destination Location')
    
    # Computed fields for picking/delivery info
    demand_qty = fields.Float(string='Demand Qty', compute='_compute_picking_info', store=False)
    product_uom = fields.Char(string='Unit', compute='_compute_picking_info', store=False)
    source_document = fields.Char(string='Source Document', compute='_compute_picking_info', store=False)
    scheduled_date = fields.Datetime(string='Scheduled Date', compute='_compute_picking_info', store=False)

    def action_update_inventory(self):
        self.ensure_one()
        if self.state != 'tare' or self.net_weight <= 0.0:
            raise UserError(_("Cannot update inventory. Net weight must be positive."))
        if not self.product_id:
            raise UserError(_("Product is required."))
        
        if self.picking_id and self.picking_id.picking_type_code == 'incoming':
            self._update_receipt_quantity()
            self.message_post(body=_("Receipt updated: %s KG of %s") % (self.net_weight, self.product_id.name))
        elif self.delivery_id and self.delivery_id.picking_type_code == 'outgoing':
            self._update_delivery_quantity()
            self.message_post(body=_("Delivery updated: %s KG of %s") % (self.net_weight, self.product_id.name))
        elif self.picking_id and self.picking_id.picking_type_code == 'outgoing':
            self.delivery_id = self.picking_id
            self._update_delivery_quantity()
            self.message_post(body=_("Delivery updated: %s KG of %s") % (self.net_weight, self.product_id.name))
        else:
            raise UserError(_("Please select a receipt or delivery first."))
        
        self.state = 'done'
    
    def _update_receipt_quantity(self):
        move = self.picking_id.move_ids.filtered(lambda m: m.product_id == self.product_id)
        if not move:
            raise UserError(_("Product %s not found in receipt.") % self.product_id.name)
        
        if self.picking_id.state == 'draft':
            self.picking_id.action_confirm()
        if self.picking_id.state in ['confirmed', 'waiting']:
            self.picking_id.action_assign()
        
        if move[0].move_line_ids:
            for ml in move[0].move_line_ids:
                ml.quantity = self.net_weight
        else:
            self.env['stock.move.line'].create({
                'move_id': move[0].id,
                'product_id': self.product_id.id,
                'product_uom_id': self.product_id.uom_id.id,
                'location_id': self.picking_id.location_id.id,
                'location_dest_id': self.picking_id.location_dest_id.id,
                'quantity': self.net_weight,
                'picking_id': self.picking_id.id,
            })
        
        demand_qty = move[0].product_uom_qty
        if self.net_weight > demand_qty:
            status = _("Over-delivery: +%s KG") % (self.net_weight - demand_qty)
        elif self.net_weight < demand_qty:
            status = _("Under-delivery: -%s KG") % (demand_qty - self.net_weight)
        else:
            status = _("Exact delivery")
        
        self.picking_id.message_post(
            body=_("Received: %s KG of %s (Demand: %s KG) - %s (from weighing %s)") % 
            (self.net_weight, self.product_id.name, demand_qty, status, self.name)
        )
    
    def _update_delivery_quantity(self):
        move = self.delivery_id.move_ids.filtered(lambda m: m.product_id == self.product_id)
        if not move:
            raise UserError(_("Product %s not found in delivery.") % self.product_id.name)
        
        if self.delivery_id.state == 'draft':
            self.delivery_id.action_confirm()
        if self.delivery_id.state in ['confirmed', 'waiting']:
            self.delivery_id.action_assign()
        
        if move[0].move_line_ids:
            for ml in move[0].move_line_ids:
                ml.quantity = self.net_weight
        else:
            self.env['stock.move.line'].create({
                'move_id': move[0].id,
                'product_id': self.product_id.id,
                'product_uom_id': self.product_id.uom_id.id,
                'location_id': self.delivery_id.location_id.id,
                'location_dest_id': self.delivery_id.location_dest_id.id,
                'quantity': self.net_weight,
                'picking_id': self.delivery_id.id,
            })
        
        demand_qty = move[0].product_uom_qty
        if self.net_weight > demand_qty:
            status = _("Over-delivery: +%s KG") % (self.net_weight - demand_qty)
        elif self.net_weight < demand_qty:
            status = _("Under-delivery: -%s KG") % (demand_qty - self.net_weight)
        else:
            status = _("Exact delivery")
        
        self.delivery_id.message_post(
            body=_("Delivered: %s KG of %s (Demand: %s KG) - %s (from weighing %s)") % 
            (self.net_weight, self.product_id.name, demand_qty, status, self.name)
        )
    
    @api.onchange('picking_id')
    def _onchange_picking_id(self):
        if self.picking_id:
            self.operation_type = self.picking_id.picking_type_code
            self.partner_id = self.picking_id.partner_id
            self.location_dest_id = self.picking_id.location_dest_id
            weighable_moves = self.picking_id.move_ids.filtered(lambda m: m.product_id.is_weighable)
            if weighable_moves:
                self.product_id = weighable_moves[0].product_id
                if self.picking_id.picking_type_code == 'outgoing':
                    self.delivery_id = self.picking_id
    
    @api.onchange('delivery_id')
    def _onchange_delivery_id(self):
        if self.delivery_id:
            self.operation_type = 'outgoing'
            self.partner_id = self.delivery_id.partner_id
            self.location_dest_id = self.delivery_id.location_dest_id
            weighable_moves = self.delivery_id.move_ids.filtered(lambda m: m.product_id.is_weighable)
            if weighable_moves:
                self.product_id = weighable_moves[0].product_id
    
    def action_view_picking(self):
        self.ensure_one()
        return {
            'name': 'Receipt',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': self.picking_id.id,
        }
    
    def action_view_delivery(self):
        self.ensure_one()
        return {
            'name': 'Delivery',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': self.delivery_id.id,
        }
    
    @api.depends('picking_id', 'delivery_id', 'product_id')
    def _compute_picking_info(self):
        for rec in self:
            picking = rec.picking_id or rec.delivery_id
            if picking and rec.product_id:
                move = picking.move_ids.filtered(lambda m: m.product_id == rec.product_id)
                if move:
                    rec.demand_qty = move[0].product_uom_qty
                    rec.product_uom = move[0].product_uom.name
                else:
                    rec.demand_qty = 0.0
                    rec.product_uom = rec.product_id.uom_id.name if rec.product_id else ''
                rec.source_document = picking.origin or picking.name
                rec.scheduled_date = picking.scheduled_date
            else:
                rec.demand_qty = 0.0
                rec.product_uom = ''
                rec.source_document = ''
                rec.scheduled_date = False
