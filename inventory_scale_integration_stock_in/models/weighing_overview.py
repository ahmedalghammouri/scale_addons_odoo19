# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta

class WeighingOverview(models.TransientModel):
    _name = 'weighing.overview.incoming'
    _description = 'Weighing Incoming Operations Overview Dashboard'

    @api.model
    def get_overview_data(self):
        today = fields.Date.today()
        week_ago = today - timedelta(days=7)
        
        receipts_to_weigh_ids = self.get_receipts_to_weigh_ids()
        receipts_to_weigh = self.env['stock.picking'].browse(receipts_to_weigh_ids)
        
        in_progress_incoming = self.env['truck.weighing'].search([
            ('state', 'in', ['draft', 'first', 'second']),
            ('operation_type', '=', 'incoming')
        ])
        
        all_records = self.env['truck.weighing'].search([('operation_type', '=', 'incoming')])
        completed_today = all_records.filtered(lambda r: r.state == 'done' and r.weighing_date.date() == today)
        completed_week = all_records.filtered(lambda r: r.state == 'done' and r.weighing_date.date() >= week_ago)
        
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
            'all_records': {
                'total_count': len(all_records),
                'completed_today': len(completed_today),
                'completed_week': len(completed_week),
                'total_weight_today': sum(completed_today.mapped('net_weight')),
                'total_weight_week': sum(completed_week.mapped('net_weight')),
                'avg_weight': sum(all_records.filtered(lambda r: r.state == 'done').mapped('net_weight')) / max(len(all_records.filtered(lambda r: r.state == 'done')), 1),
            },
            'stock_performance': self._get_stock_performance_data(all_records, completed_week)
        }
    
    def _calculate_avg_processing_time(self, records):
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
        all_receipts = self.env['stock.picking'].search([
            ('state', 'in', ['assigned', 'confirmed']),
            ('picking_type_code', '=', 'incoming'),
            ('move_ids.product_id.is_weighable', '=', True)
        ])
        receipts_to_weigh = all_receipts.filtered(lambda r: 
            not self.env['truck.weighing'].search([('picking_id', '=', r.id)], limit=1)
        )
        return receipts_to_weigh.ids
    
    def _get_stock_performance_data(self, all_records, completed_week):
        completed_with_stock = all_records.filtered(lambda r: r.state == 'done' and r.picking_id)
        
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
                'products_count': 0,
                'accuracy_rate': 0,
            }
        
        high_fulfillment = 0
        over_delivered = 0
        exact_match = 0
        under_delivered = 0
        total_fulfillment = 0
        total_variance = 0
        accuracy_count = 0
        
        for rec in completed_with_stock:
            if not rec.picking_id:
                continue
            move = rec.picking_id.move_ids.filtered(lambda m: m.product_id == rec.product_id)
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
            if fulfillment >= 0.95:
                high_fulfillment += 1
            if variance > 0:
                over_delivered += 1
            elif variance == 0:
                exact_match += 1
            else:
                under_delivered += 1
            if abs(variance_percent) <= 0.05:
                accuracy_count += 1
        
        return {
            'total_completed': len(completed_with_stock),
            'high_fulfillment': high_fulfillment,
            'over_delivered': over_delivered,
            'exact_match': exact_match,
            'under_delivered': under_delivered,
            'avg_fulfillment': round((total_fulfillment / max(len(completed_with_stock), 1)) * 100, 1),
            'total_variance': round(total_variance, 2),
            'total_received': round(sum(completed_with_stock.mapped('net_weight')), 2),
            'receipts_count': len(completed_with_stock),
            'products_count': len(completed_with_stock.mapped('product_id')),
            'accuracy_rate': round((accuracy_count / max(len(completed_with_stock), 1)) * 100, 1),
        }
