# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class WeighingDashboard(http.Controller):
    
    @http.route('/weighing/dashboard', type='http', auth='user', website=True)
    def weighing_dashboard(self, **kwargs):
        # Get counts
        receipts_count = request.env['stock.picking'].search_count([
            ('picking_type_code', '=', 'incoming'),
            ('state', 'in', ['assigned', 'confirmed'])
        ])
        
        draft_count = request.env['truck.weighing'].search_count([('state', '=', 'draft')])
        gross_count = request.env['truck.weighing'].search_count([('state', '=', 'gross')])
        tare_count = request.env['truck.weighing'].search_count([('state', '=', 'tare')])
        in_progress_count = draft_count + gross_count + tare_count
        
        done_records = request.env['truck.weighing'].search([('state', '=', 'done')])
        done_count = len(done_records)
        total_weight = round(sum(done_records.mapped('net_weight')), 2)
        
        values = {
            'receipts_count': receipts_count,
            'in_progress_count': in_progress_count,
            'draft_count': draft_count,
            'gross_count': gross_count,
            'tare_count': tare_count,
            'done_count': done_count,
            'total_weight': total_weight,
        }
        
        return request.render('inventory_scale_integration_base.weighing_dashboard', values)