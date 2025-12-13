# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class TruckWeighing(models.Model):
    _inherit = 'truck.weighing'
    
    delivery_id = fields.Many2one('stock.picking', string='Delivery', ondelete='restrict', tracking=True, domain="[('picking_type_code', '=', 'outgoing')]")
    location_dest_id = fields.Many2one('stock.location', string='Destination Location')
    
    demand_qty = fields.Float(string='Demand Qty', compute='_compute_delivery_info', store=False)
    product_uom = fields.Char(string='Unit', compute='_compute_delivery_info', store=False)
    source_document = fields.Char(string='Source Document', compute='_compute_delivery_info', store=False)
    scheduled_date = fields.Datetime(string='Scheduled Date', compute='_compute_delivery_info', store=False)
    
    remaining_qty = fields.Float(string='Remaining Qty', compute='_compute_variance_info', store=False)
    variance_qty = fields.Float(string='Variance', compute='_compute_variance_info', store=False)
    variance_percent = fields.Float(string='Variance %', compute='_compute_variance_info', store=False)
    fulfillment_percent = fields.Float(string='Fulfillment %', compute='_compute_variance_info', store=False)

    def action_update_inventory(self):
        self.ensure_one()
        if self.state != 'second' or self.net_weight <= 0.0:
            raise UserError(_("Cannot update inventory. Net weight must be positive."))
        if not self.product_id:
            raise UserError(_("Product is required."))
        
        if self.delivery_id and self.delivery_id.picking_type_code == 'outgoing':
            self._update_delivery_quantity()
            self.message_post(body=_("Delivery updated: %s KG of %s") % (self.net_weight, self.product_id.name))
        else:
            raise UserError(_("Please select a delivery first."))
        
        self.state = 'done'
    
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
    
    @api.onchange('delivery_id')
    def _onchange_delivery_id(self):
        if self.delivery_id:
            self.operation_type = 'outgoing'
            self.partner_id = self.delivery_id.partner_id
            self.location_dest_id = self.delivery_id.location_dest_id
            weighable_moves = self.delivery_id.move_ids.filtered(lambda m: m.product_id.is_weighable)
            if weighable_moves:
                self.product_id = weighable_moves[0].product_id
            elif self.delivery_id.move_ids:
                self.product_id = self.delivery_id.move_ids[0].product_id
                return {'warning': {
                    'title': _('No Weighable Products'),
                    'message': _('This delivery has no weighable products. Using first product from moves.')
                }}
    
    def action_view_delivery(self):
        self.ensure_one()
        return {
            'name': 'Delivery',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': self.delivery_id.id,
        }
    
    @api.depends('delivery_id', 'product_id')
    def _compute_delivery_info(self):
        for rec in self:
            if rec.delivery_id and rec.product_id:
                move = rec.delivery_id.move_ids.filtered(lambda m: m.product_id == rec.product_id)
                if move:
                    rec.demand_qty = move[0].product_uom_qty
                    rec.product_uom = move[0].product_uom.name
                else:
                    rec.demand_qty = 0.0
                    rec.product_uom = rec.product_id.uom_id.name if rec.product_id else ''
                rec.source_document = rec.delivery_id.origin or rec.delivery_id.name
                rec.scheduled_date = rec.delivery_id.scheduled_date
            else:
                rec.demand_qty = 0.0
                rec.product_uom = ''
                rec.source_document = ''
                rec.scheduled_date = False
    
    @api.depends('demand_qty', 'net_weight')
    def _compute_variance_info(self):
        for rec in self:
            if rec.demand_qty > 0 and rec.net_weight > 0:
                rec.remaining_qty = rec.demand_qty - rec.net_weight
                rec.variance_qty = rec.net_weight - rec.demand_qty
                rec.variance_percent = rec.variance_qty / rec.demand_qty
                rec.fulfillment_percent = rec.net_weight / rec.demand_qty
            else:
                rec.remaining_qty = 0.0
                rec.variance_qty = 0.0
                rec.variance_percent = 0.0
                rec.fulfillment_percent = 0.0
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('delivery_id') and not vals.get('product_id'):
                delivery = self.env['stock.picking'].browse(vals['delivery_id'])
                weighable_moves = delivery.move_ids.filtered(lambda m: m.product_id.is_weighable)
                move_to_use = weighable_moves[0] if weighable_moves else (delivery.move_ids[0] if delivery.move_ids else False)
                if move_to_use:
                    vals['product_id'] = move_to_use.product_id.id
                    if not vals.get('partner_id'):
                        vals['partner_id'] = delivery.partner_id.id
                    if not vals.get('operation_type'):
                        vals['operation_type'] = 'outgoing'
                    if not vals.get('location_dest_id'):
                        vals['location_dest_id'] = delivery.location_dest_id.id
        return super().create(vals_list)
    
    def write(self, vals):
        for rec in self:
            if vals.get('delivery_id') and 'product_id' not in vals and not rec.product_id:
                delivery = self.env['stock.picking'].browse(vals['delivery_id'])
                weighable_moves = delivery.move_ids.filtered(lambda m: m.product_id.is_weighable)
                move_to_use = weighable_moves[0] if weighable_moves else (delivery.move_ids[0] if delivery.move_ids else False)
                if move_to_use:
                    vals['product_id'] = move_to_use.product_id.id
                    if not rec.partner_id and 'partner_id' not in vals:
                        vals['partner_id'] = delivery.partner_id.id
                    if not rec.operation_type and 'operation_type' not in vals:
                        vals['operation_type'] = 'outgoing'
                    if not rec.location_dest_id and 'location_dest_id' not in vals:
                        vals['location_dest_id'] = delivery.location_dest_id.id
        return super().write(vals)
