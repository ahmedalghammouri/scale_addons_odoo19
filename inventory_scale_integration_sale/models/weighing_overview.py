# -*- coding: utf-8 -*-
from odoo import models, api

class WeighingOverview(models.TransientModel):
    _inherit = 'weighing.overview'

    @api.model
    def get_overview_data(self):
        from datetime import date
        data = super().get_overview_data()
        today = date.today()
        
        # Get all SOs with weighable products
        all_sos = self.env['sale.order'].search([
            ('state', 'in', ['draft', 'sent', 'sale']),
            ('order_line.product_id.is_weighable', '=', True)
        ])
        
        # Calculate total expected weight
        total_qty = sum(all_sos.mapped('order_line.product_uom_qty'))
        urgent_sos = all_sos.filtered(lambda s: s.commitment_date and s.commitment_date.date() <= today)
        
        data['sale_orders'] = {
            'count': len(all_sos),
            'total_qty': total_qty,
            'urgent_count': len(urgent_sos),
            'customers': len(all_sos.mapped('partner_id')),
            'total_amount': sum(all_sos.mapped('amount_total')),
        }
        
        return data
    
    @api.model
    def get_sales_to_weigh_ids(self):
        """Get Sales Order IDs that need weighing"""
        all_sales = self.env['sale.order'].search([
            ('state', 'in', ['sale', 'done']),
            ('order_line.product_id.is_weighable', '=', True)
        ])
        sales_to_weigh = all_sales.filtered(lambda s: 
            not self.env['truck.weighing'].search([('sale_order_id', '=', s.id)], limit=1)
        )
        return sales_to_weigh.ids
