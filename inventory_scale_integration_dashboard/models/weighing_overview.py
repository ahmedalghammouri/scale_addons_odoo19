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
        
        # Get IDs - will return empty if modules not installed
        receipts_to_weigh_ids = self.get_receipts_to_weigh_ids()
        deliveries_to_weigh_ids = self.get_deliveries_to_weigh_ids()
        
        receipts_to_weigh = self.env['stock.picking'].browse(receipts_to_weigh_ids)
        deliveries_to_weigh = self.env['stock.picking'].browse(deliveries_to_weigh_ids)
        
        # In Progress Weighings - will be empty if modules not installed
        in_progress_incoming = self.env['truck.weighing'].search([
            ('state', 'in', ['draft', 'first', 'second']),
            ('operation_type', '=', 'incoming')
        ])
        
        in_progress_outgoing = self.env['truck.weighing'].search([
            ('state', 'in', ['draft', 'first', 'second']),
            ('operation_type', '=', 'outgoing')
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

            'in_progress_incoming': {
                'count': len(in_progress_incoming),
                'draft_count': len(in_progress_incoming.filtered(lambda r: r.state == 'draft')),
                'first_count': len(in_progress_incoming.filtered(lambda r: r.state == 'first')),
                'second_count': len(in_progress_incoming.filtered(lambda r: r.state == 'second')),
                'avg_time': self._calculate_avg_processing_time(in_progress_incoming),
                'first_weight': sum(in_progress_incoming.filtered(lambda r: r.state == 'first').mapped('gross_weight')),
                'second_weight': sum(in_progress_incoming.filtered(lambda r: r.state == 'second').mapped('tare_weight')),
            },
            'in_progress_outgoing': {
                'count': len(in_progress_outgoing),
                'draft_count': len(in_progress_outgoing.filtered(lambda r: r.state == 'draft')),
                'first_count': len(in_progress_outgoing.filtered(lambda r: r.state == 'first')),
                'second_count': len(in_progress_outgoing.filtered(lambda r: r.state == 'second')),
                'avg_time': self._calculate_avg_processing_time(in_progress_outgoing),
                'first_weight': sum(in_progress_outgoing.filtered(lambda r: r.state == 'first').mapped('tare_weight')),
                'second_weight': sum(in_progress_outgoing.filtered(lambda r: r.state == 'second').mapped('gross_weight')),
            },
            'draft_details': {
                'incoming_count': len(in_progress_incoming.filtered(lambda r: r.state == 'draft')),
                'outgoing_count': len(in_progress_outgoing.filtered(lambda r: r.state == 'draft')),
                'with_truck': len((in_progress_incoming + in_progress_outgoing).filtered(lambda r: r.state == 'draft' and r.truck_id)),
                'without_truck': len((in_progress_incoming + in_progress_outgoing).filtered(lambda r: r.state == 'draft' and not r.truck_id)),
                'expected_weight': self._get_draft_expected_weight(in_progress_incoming, in_progress_outgoing),
                'avg_waiting_time': self._calculate_avg_processing_time((in_progress_incoming + in_progress_outgoing).filtered(lambda r: r.state == 'draft')),
            },
            'all_records': {
                'total_count': len(all_records),
                'completed_today': len(completed_today),
                'completed_week': len(completed_week),
                'total_weight_today': sum(completed_today.mapped('net_weight')),
                'total_weight_week': sum(completed_week.mapped('net_weight')),
                'avg_weight': sum(all_records.filtered(lambda r: r.state == 'done').mapped('net_weight')) / max(len(all_records.filtered(lambda r: r.state == 'done')), 1),
                'draft_percent': round((len(all_records.filtered(lambda r: r.state == 'draft')) / max(len(all_records), 1)) * 100, 1),
                'first_percent': round((len(all_records.filtered(lambda r: r.state == 'first')) / max(len(all_records), 1)) * 100, 1),
                'second_percent': round((len(all_records.filtered(lambda r: r.state == 'second')) / max(len(all_records), 1)) * 100, 1),
                'done_percent': round((len(all_records.filtered(lambda r: r.state == 'done')) / max(len(all_records), 1)) * 100, 1),
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
            },
            'stock_performance': self._get_stock_performance_data(all_records, completed_week)
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
    
    def _get_draft_expected_weight(self, incoming, outgoing):
        """Calculate expected weight for draft records from linked pickings"""
        draft_records = (incoming + outgoing).filtered(lambda r: r.state == 'draft')
        total_weight = 0
        
        for record in draft_records:
            picking = (hasattr(record, 'picking_id') and record.picking_id) or (hasattr(record, 'delivery_id') and record.delivery_id)
            if picking and picking.move_ids:
                for move in picking.move_ids.filtered(lambda m: m.product_id.is_weighable):
                    total_weight += move.product_uom_qty
        
        return round(total_weight, 2)
    
    @api.model
    def get_receipts_to_weigh_ids(self):
        """Get receipt IDs that need weighing - Override in stock_in module"""
        return []
    
    @api.model
    def get_deliveries_to_weigh_ids(self):
        """Get Delivery IDs that need weighing - Override in stock_out module"""
        return []
    
    def _get_stock_performance_data(self, all_records, completed_week):
        """Calculate stock performance analytics"""
        # Get completed weighings with picking/delivery
        completed_with_stock = all_records.filtered(lambda r: r.state == 'done' and (hasattr(r, 'picking_id') and r.picking_id or hasattr(r, 'delivery_id') and r.delivery_id))
        
        if not completed_with_stock:
            return {
                'total_completed': 0,
                'high_fulfillment': 0,
                'over_delivered': 0,
                'exact_match': 0,
                'under_delivered': 0,
                'avg_fulfillment': 0,
                'total_variance': 0,
                'total_received': 0,
                'receipts_count': 0,
                'total_delivered': 0,
                'deliveries_count': 0,
                'products_count': 0,
                'accuracy_rate': 0,
            }
        
        # Calculate variance metrics (using net_weight vs demand_qty logic)
        high_fulfillment = 0
        over_delivered = 0
        exact_match = 0
        under_delivered = 0
        total_fulfillment = 0
        total_variance = 0
        accuracy_count = 0
        
        for rec in completed_with_stock:
            picking = (hasattr(rec, 'picking_id') and rec.picking_id) or (hasattr(rec, 'delivery_id') and rec.delivery_id)
            if not picking:
                continue
            
            move = picking.move_ids.filtered(lambda m: m.product_id == rec.product_id)
            if not move:
                continue
            
            demand_qty = move[0].product_uom_qty
            if demand_qty <= 0:
                continue
            
            variance = rec.net_weight - demand_qty
            variance_percent = variance / demand_qty
            fulfillment = rec.net_weight / demand_qty
            
            total_variance += abs(variance)
            total_fulfillment += fulfillment
            
            # Categorize
            if fulfillment >= 0.95:
                high_fulfillment += 1
            
            if variance > 0:
                over_delivered += 1
            elif variance == 0:
                exact_match += 1
            else:
                under_delivered += 1
            
            # Accuracy (within ±5%)
            if abs(variance_percent) <= 0.05:
                accuracy_count += 1
        
        # Calculate totals
        receipts = completed_with_stock.filtered(lambda r: hasattr(r, 'picking_id') and r.picking_id)
        deliveries = completed_with_stock.filtered(lambda r: hasattr(r, 'delivery_id') and r.delivery_id)
        
        return {
            'total_completed': len(completed_with_stock),
            'high_fulfillment': high_fulfillment,
            'over_delivered': over_delivered,
            'exact_match': exact_match,
            'under_delivered': under_delivered,
            'avg_fulfillment': round((total_fulfillment / max(len(completed_with_stock), 1)) * 100, 1),
            'total_variance': round(total_variance, 2),
            'total_received': round(sum(receipts.mapped('net_weight')), 2),
            'receipts_count': len(receipts),
            'total_delivered': round(sum(deliveries.mapped('net_weight')), 2),
            'deliveries_count': len(deliveries),
            'products_count': len(completed_with_stock.mapped('product_id')),
            'accuracy_rate': round((accuracy_count / max(len(completed_with_stock), 1)) * 100, 1),
        }