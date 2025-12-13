# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class TruckWeighing(models.Model):
    _inherit = 'truck.weighing'
    
    picking_id = fields.Many2one('stock.picking', string='Receipt', ondelete='restrict', tracking=True, domain="[('picking_type_code', '=', 'incoming')]")
    location_dest_id = fields.Many2one('stock.location', string='Destination Location')
    
    demand_qty = fields.Float(string='Demand Qty', compute='_compute_picking_info', store=False)
    product_uom = fields.Char(string='Unit', compute='_compute_picking_info', store=False)
    source_document = fields.Char(string='Source Document', compute='_compute_picking_info', store=False)
    scheduled_date = fields.Datetime(string='Scheduled Date', compute='_compute_picking_info', store=False)
    
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
        
        if self.picking_id and self.picking_id.picking_type_code == 'incoming':
            self._update_receipt_quantity()
            self.message_post(body=_("Receipt updated: %s KG of %s") % (self.net_weight, self.product_id.name))
        else:
            raise UserError(_("Please select a receipt first."))
        
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
    
    def _is_incoming_picking(self, picking):
        if not picking or not picking.move_ids:
            return False
        move = picking.move_ids[0]
        return move.location_id.usage in ('customer', 'supplier') or (
            move.location_id.usage == 'transit' and not move.location_id.company_id
        )
    
    @api.onchange('picking_id')
    def _onchange_picking_id(self):
        if self.picking_id:
            self.operation_type = 'incoming'
            self.partner_id = self.picking_id.partner_id
            self.location_dest_id = self.picking_id.location_dest_id
            weighable_moves = self.picking_id.move_ids.filtered(lambda m: m.product_id.is_weighable)
            if weighable_moves:
                self.product_id = weighable_moves[0].product_id
            elif self.picking_id.move_ids:
                self.product_id = self.picking_id.move_ids[0].product_id
                return {'warning': {
                    'title': _('No Weighable Products'),
                    'message': _('This picking has no weighable products. Using first product from moves.')
                }}
    
    def action_view_picking(self):
        self.ensure_one()
        return {
            'name': 'Receipt',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': self.picking_id.id,
        }
    
    @api.depends('picking_id', 'product_id', 'operation_type')
    def _compute_picking_info(self):
        for rec in self:
            if rec.picking_id and rec.product_id and rec.operation_type == 'incoming':
                move = rec.picking_id.move_ids.filtered(lambda m: m.product_id == rec.product_id)
                if move:
                    rec.demand_qty = move[0].product_uom_qty
                    rec.product_uom = move[0].product_uom.name
                else:
                    rec.demand_qty = 0.0
                    rec.product_uom = rec.product_id.uom_id.name if rec.product_id else ''
                rec.source_document = rec.picking_id.origin or rec.picking_id.name
                rec.scheduled_date = rec.picking_id.scheduled_date
            else:
                rec.demand_qty = 0.0
                rec.product_uom = ''
                rec.source_document = ''
                rec.scheduled_date = False
    
    @api.depends('demand_qty', 'net_weight', 'operation_type')
    def _compute_variance_info(self):
        for rec in self:
            if rec.operation_type == 'incoming' and rec.demand_qty > 0 and rec.net_weight > 0:
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
            if vals.get('picking_id') and not vals.get('product_id'):
                picking = self.env['stock.picking'].browse(vals['picking_id'])
                if self._is_incoming_picking(picking):
                    weighable_moves = picking.move_ids.filtered(lambda m: m.product_id.is_weighable)
                    move_to_use = weighable_moves[0] if weighable_moves else (picking.move_ids[0] if picking.move_ids else False)
                    if move_to_use:
                        vals['product_id'] = move_to_use.product_id.id
                        if not vals.get('partner_id'):
                            vals['partner_id'] = picking.partner_id.id
                        if not vals.get('operation_type'):
                            vals['operation_type'] = 'incoming'
                        if not vals.get('location_dest_id'):
                            vals['location_dest_id'] = picking.location_dest_id.id
        return super().create(vals_list)
    
    def write(self, vals):
        for rec in self:
            if vals.get('picking_id') and 'product_id' not in vals and not rec.product_id:
                picking = self.env['stock.picking'].browse(vals['picking_id'])
                if rec._is_incoming_picking(picking):
                    weighable_moves = picking.move_ids.filtered(lambda m: m.product_id.is_weighable)
                    move_to_use = weighable_moves[0] if weighable_moves else (picking.move_ids[0] if picking.move_ids else False)
                    if move_to_use:
                        vals['product_id'] = move_to_use.product_id.id
                        if not rec.partner_id and 'partner_id' not in vals:
                            vals['partner_id'] = picking.partner_id.id
                        if not rec.operation_type and 'operation_type' not in vals:
                            vals['operation_type'] = 'incoming'
                        if not rec.location_dest_id and 'location_dest_id' not in vals:
                            vals['location_dest_id'] = picking.location_dest_id.id
        return super().write(vals)
