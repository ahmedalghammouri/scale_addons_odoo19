# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta

class WeighingOverview(models.TransientModel):
    _name = 'weighing.overview'
    _description = 'Weighing Operations Overview Dashboard'

    @api.model
    def get_overview_data(self):
        """Get comprehensive overview data for dashboard cards"""
        today = fields.Date.today()
        week_ago = today - timedelta(days=7)
        
        # Get IDs for consistent filtering
        receipts_to_weigh_ids = self.get_receipts_to_weigh_ids()
        deliveries_to_weigh_ids = self.get_deliveries_to_weigh_ids()
        
        receipts_to_weigh = self.env['stock.picking'].browse(receipts_to_weigh_ids)
        deliveries_to_weigh = self.env['stock.picking'].browse(deliveries_to_weigh_ids)
        
        # In Progress Weighings
        in_progress = self.env['truck.weighing'].search([
            ('state', 'in', ['draft', 'gross', 'tare'])
        ])
        
        # All Records
        all_records = self.env['truck.weighing'].search([])
        completed_today = all_records.filtered(lambda r: r.state == 'done' and r.weighing_date.date() == today)
        completed_week = all_records.filtered(lambda r: r.state == 'done' and r.weighing_date.date() >= week_ago)
        
        # Truck Management Data
        all_trucks = self.env['truck.fleet'].search([])
        active_trucks = all_trucks.filtered(lambda t: t.active)
        trucks_with_weighing = all_trucks.filtered(lambda t: self.env['truck.weighing'].search([('truck_id', '=', t.id)], limit=1))
        trucks_today = self.env['truck.weighing'].search([('weighing_date', '>=', today)]).mapped('truck_id')
        
        # Truck performance metrics
        total_weighings = len(all_records)
        avg_weighings_per_truck = total_weighings / max(len(trucks_with_weighing), 1)
        
        # Truck-related Receipts
        truck_receipts = self.env['stock.picking'].search_count([
            ('state', 'in', ['assigned', 'confirmed', 'done']),
            ('picking_type_code', '=', 'incoming'),
            ('move_ids.product_id.is_weighable', '=', True)
        ])
        
        # Weekly truck activity
        weekly_truck_activity = self.env['truck.weighing'].search_count([
            ('weighing_date', '>=', week_ago),
            ('state', '=', 'done')
        ])
        
        return {
            'receipts_to_weigh': {
                'count': len(receipts_to_weigh),
                'total_qty': sum(receipts_to_weigh.mapped('move_ids.product_uom_qty')),
                'urgent_count': len(receipts_to_weigh.filtered(lambda r: r.scheduled_date and r.scheduled_date.date() <= today)),
                'partners': len(receipts_to_weigh.mapped('partner_id')),
            },

            'in_progress': {
                'count': len(in_progress),
                'draft_count': len(in_progress.filtered(lambda r: r.state == 'draft')),
                'gross_count': len(in_progress.filtered(lambda r: r.state == 'gross')),
                'tare_count': len(in_progress.filtered(lambda r: r.state == 'tare')),
                'avg_time': self._calculate_avg_processing_time(in_progress),
            },
            'all_records': {
                'total_count': len(all_records),
                'completed_today': len(completed_today),
                'completed_week': len(completed_week),
                'total_weight_today': sum(completed_today.mapped('net_weight')),
                'total_weight_week': sum(completed_week.mapped('net_weight')),
                'avg_weight': sum(all_records.filtered(lambda r: r.state == 'done').mapped('net_weight')) / max(len(all_records.filtered(lambda r: r.state == 'done')), 1),
            },
            'truck_management': {
                'total_trucks': len(all_trucks),
                'active_trucks': len(active_trucks),
                'trucks_with_weighing': len(trucks_with_weighing),
                'trucks_today': len(trucks_today),
                'utilization_rate': round((len(trucks_with_weighing) / max(len(active_trucks), 1)) * 100, 1),
                'total_weighings': total_weighings,
                'avg_weighings_per_truck': round(avg_weighings_per_truck, 1),

                'truck_receipts': truck_receipts,
                'weekly_activity': weekly_truck_activity,
                'efficiency_score': round((weekly_truck_activity / max(len(active_trucks), 1)), 1),
            },

            'deliveries_to_weigh': {
                'count': len(deliveries_to_weigh),
                'total_qty': sum(deliveries_to_weigh.mapped('move_ids.product_uom_qty')),
                'urgent_count': len(deliveries_to_weigh.filtered(lambda d: d.scheduled_date and d.scheduled_date.date() <= today)),
                'partners': len(deliveries_to_weigh.mapped('partner_id')),
            }
        }
    
    def _calculate_avg_processing_time(self, records):
        """Calculate average processing time in hours"""
        if not records:
            return 0
        
        total_hours = 0
        count = 0
        now = datetime.now()
        
        for record in records:
            if record.weighing_date:
                hours = (now - record.weighing_date).total_seconds() / 3600
                total_hours += hours
                count += 1
        
        return round(total_hours / max(count, 1), 1)
    
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
    def get_deliveries_to_weigh_ids(self):
        """Get Delivery IDs that need weighing"""
        all_deliveries = self.env['stock.picking'].search([
            ('state', 'in', ['assigned', 'confirmed']),
            ('picking_type_code', '=', 'outgoing'),
            ('move_ids.product_id.is_weighable', '=', True)
        ])
        # Filter out those with existing weighing records
        deliveries_to_weigh = all_deliveries.filtered(lambda d: 
            not self.env['truck.weighing'].search([('delivery_id', '=', d.id)], limit=1)
        )
        return deliveries_to_weigh.ids