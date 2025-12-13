# -*- coding: utf-8 -*-
from odoo import models, api

class WeighingOverview(models.TransientModel):
    _inherit = 'weighing.overview'

    @api.model
    def get_overview_data(self, **kwargs):
        from datetime import date
        data = super().get_overview_data(**kwargs)
        today = date.today()
        
        # Get all POs with weighable products
        all_pos = self.env['purchase.order'].search([
            ('state', 'in', ['draft', 'sent', 'to approve', 'purchase']),
            ('order_line.product_id.is_weighable', '=', True)
        ])
        
        # Calculate total expected weight
        total_qty = sum(all_pos.mapped('order_line.product_qty'))
        urgent_pos = all_pos.filtered(lambda p: p.date_planned and p.date_planned.date() <= today)
        
        data['purchase_orders'] = {
            'count': len(all_pos),
            'total_qty': total_qty,
            'urgent_count': len(urgent_pos),
            'vendors': len(all_pos.mapped('partner_id')),
            'total_amount': sum(all_pos.mapped('amount_total')),
        }
        
        return data
    
    @api.model
    def get_pos_to_weigh_ids(self):
        """Get PO IDs that need weighing"""
        all_pos = self.env['purchase.order'].search([
            ('state', 'in', ['purchase', 'done']),
            ('order_line.product_id.is_weighable', '=', True)
        ])
        pos_to_weigh = all_pos.filtered(lambda p: 
            not self.env['truck.weighing'].search([('purchase_order_id', '=', p.id)], limit=1)
        )
        return pos_to_weigh.ids
