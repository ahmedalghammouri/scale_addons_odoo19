# -*- coding: utf-8 -*-
from odoo import models, api

class WeighingOverview(models.TransientModel):
    _inherit = 'weighing.overview'

    @api.model
    def get_overview_data(self):
        data = super().get_overview_data()
        
        # Add PO data
        pos_to_weigh_ids = self.get_pos_to_weigh_ids()
        pos_to_weigh = self.env['purchase.order'].browse(pos_to_weigh_ids)
        
        data['pos_to_weigh'] = {
            'count': len(pos_to_weigh),
            'total_amount': sum(pos_to_weigh.mapped('amount_total')),
            'pending_qty': sum(line.product_qty - line.qty_received for po in pos_to_weigh for line in po.order_line),
            'partners': len(pos_to_weigh.mapped('partner_id')),
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
