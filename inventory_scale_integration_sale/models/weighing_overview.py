# -*- coding: utf-8 -*-
from odoo import models, api

class WeighingOverview(models.TransientModel):
    _inherit = 'weighing.overview'

    @api.model
    def get_overview_data(self):
        data = super().get_overview_data()
        
        # Add SO data
        sales_to_weigh_ids = self.get_sales_to_weigh_ids()
        sales_to_weigh = self.env['sale.order'].browse(sales_to_weigh_ids)
        
        data['sales_to_weigh'] = {
            'count': len(sales_to_weigh),
            'total_amount': sum(sales_to_weigh.mapped('amount_total')),
            'pending_qty': sum(line.product_uom_qty - line.qty_delivered for so in sales_to_weigh for line in so.order_line),
            'partners': len(sales_to_weigh.mapped('partner_id')),
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
