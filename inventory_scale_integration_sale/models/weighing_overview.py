# -*- coding: utf-8 -*-
from odoo import models, fields, api

class WeighingOverview(models.TransientModel):
    _inherit = 'weighing.overview'

    @api.model
    def get_overview_data(self):
        """Extend overview data with sales-specific information"""
        data = super().get_overview_data()
        
        # Add deliveries data
        deliveries_to_weigh_ids = self.get_deliveries_to_weigh_ids()
        deliveries_to_weigh = self.env['stock.picking'].browse(deliveries_to_weigh_ids)
        
        data['deliveries_to_weigh'] = {
            'count': len(deliveries_to_weigh),
            'total_qty': sum(deliveries_to_weigh.mapped('move_ids.product_uom_qty')),
            'urgent_count': len(deliveries_to_weigh.filtered(lambda d: d.scheduled_date and d.scheduled_date.date() <= self.env.context.get('today', fields.Date.today()))),
            'partners': len(deliveries_to_weigh.mapped('partner_id')),
        }
        
        # Add SO data
        sales_to_weigh_ids = self.get_sales_to_weigh_ids()
        sales_to_weigh = self.env['sale.order'].browse(sales_to_weigh_ids)
        
        data['sales_to_weigh'] = {
            'count': len(sales_to_weigh),
            'total_amount': sum(sales_to_weigh.mapped('amount_total')),
            'pending_qty': sum(sales_to_weigh.mapped('order_line.product_uom_qty')) - sum(sales_to_weigh.mapped('order_line.qty_delivered')),
            'partners': len(sales_to_weigh.mapped('partner_id')),
        }
        
        return data

    @api.model
    def get_deliveries_to_weigh_ids(self):
        """Get delivery IDs that need weighing"""
        all_deliveries = self.env['stock.picking'].search([
            ('state', 'in', ['assigned', 'confirmed']),
            ('picking_type_code', '=', 'outgoing'),
            ('move_ids.product_id.is_weighable', '=', True)
        ])
        # Filter out those with existing weighing records
        deliveries_to_weigh = all_deliveries.filtered(lambda d: 
            not self.env['truck.weighing'].search([('picking_id', '=', d.id)], limit=1)
        )
        return deliveries_to_weigh.ids

    @api.model
    def get_sales_to_weigh_ids(self):
        """Get sales order IDs that need weighing"""
        sales_to_weigh = self.env['sale.order'].search([
            ('state', 'in', ['sale', 'done']),
            ('order_line.product_id.is_weighable', '=', True)
        ])
        return sales_to_weigh.ids