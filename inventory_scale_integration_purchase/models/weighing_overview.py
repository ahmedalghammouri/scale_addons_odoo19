# -*- coding: utf-8 -*-
from odoo import models, fields, api

class WeighingOverview(models.TransientModel):
    _inherit = 'weighing.overview'

    @api.model
    def get_overview_data(self):
        """Extend overview data with purchase-specific information"""
        data = super().get_overview_data()
        
        # Add receipts data
        receipts_to_weigh_ids = self.get_receipts_to_weigh_ids()
        receipts_to_weigh = self.env['stock.picking'].browse(receipts_to_weigh_ids)
        
        data['receipts_to_weigh'] = {
            'count': len(receipts_to_weigh),
            'total_qty': sum(receipts_to_weigh.mapped('move_ids.product_uom_qty')),
            'urgent_count': len(receipts_to_weigh.filtered(lambda r: r.scheduled_date and r.scheduled_date.date() <= self.env.context.get('today', fields.Date.today()))),
            'partners': len(receipts_to_weigh.mapped('partner_id')),
        }
        
        # Add PO data
        pos_to_weigh_ids = self.get_pos_to_weigh_ids()
        pos_to_weigh = self.env['purchase.order'].browse(pos_to_weigh_ids)
        
        data['pos_to_weigh'] = {
            'count': len(pos_to_weigh),
            'total_amount': sum(pos_to_weigh.mapped('amount_total')),
            'pending_qty': sum(pos_to_weigh.mapped('order_line.product_qty')) - sum(pos_to_weigh.mapped('order_line.qty_received')),
            'partners': len(pos_to_weigh.mapped('partner_id')),
        }
        
        return data

    @api.model
    def get_receipts_to_weigh_ids(self):
        """Get receipt IDs that need weighing"""
        all_receipts = self.env['stock.picking'].search([
            ('state', 'in', ['assigned', 'confirmed']),
            ('picking_type_code', '=', 'incoming'),
            ('move_ids.product_id.is_weighable', '=', True)
        ])
        # Filter out those with existing weighing records
        receipts_to_weigh = all_receipts.filtered(lambda r: 
            not self.env['truck.weighing'].search([('picking_id', '=', r.id)], limit=1)
        )
        return receipts_to_weigh.ids

    @api.model
    def get_pos_to_weigh_ids(self):
        """Get purchase order IDs that need weighing"""
        pos_to_weigh = self.env['purchase.order'].search([
            ('state', 'in', ['purchase', 'done']),
            ('order_line.product_id.is_weighable', '=', True)
        ])
        return pos_to_weigh.ids