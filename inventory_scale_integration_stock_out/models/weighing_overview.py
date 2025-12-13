# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta

class WeighingOverview(models.TransientModel):
    _inherit = 'weighing.overview'

    @api.model
    def get_overview_data(self, **kwargs):
        data = super().get_overview_data(**kwargs)
        today = fields.Date.today()
        
        deliveries_to_weigh_ids = self.get_deliveries_to_weigh_ids()
        deliveries_to_weigh = self.env['stock.picking'].browse(deliveries_to_weigh_ids)
        
        in_progress_outgoing = self.env['truck.weighing'].search([
            ('state', 'in', ['draft', 'first', 'second']),
            ('operation_type', '=', 'outgoing')
        ])
        
        data.update({
            'deliveries_to_weigh': {
                'count': len(deliveries_to_weigh),
                'total_qty': sum(deliveries_to_weigh.mapped('move_ids.product_uom_qty')),
                'urgent_count': len(deliveries_to_weigh.filtered(lambda d: d.scheduled_date and d.scheduled_date.date() <= today)),
                'partners': len(deliveries_to_weigh.mapped('partner_id')),
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
        })
        return data
    
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
    def get_deliveries_to_weigh_ids(self):
        all_deliveries = self.env['stock.picking'].search([
            ('state', 'in', ['assigned', 'confirmed']),
            ('picking_type_code', '=', 'outgoing'),
            ('move_ids.product_id.is_weighable', '=', True)
        ])
        deliveries_to_weigh = all_deliveries.filtered(lambda d: 
            not self.env['truck.weighing'].search([('delivery_id', '=', d.id)], limit=1)
        )
        return deliveries_to_weigh.ids
