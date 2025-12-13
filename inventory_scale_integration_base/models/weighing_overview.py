# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta

class WeighingOverview(models.TransientModel):
    _name = 'weighing.overview'
    _description = 'Weighing Operations Overview Dashboard'

    avg_waiting_time_to_first = fields.Float(string='Avg Wait to First Weigh', compute='_compute_waiting_times')
    avg_waiting_time_to_second = fields.Float(string='Avg Wait to Second Weigh', compute='_compute_waiting_times')
    avg_waiting_time_to_done = fields.Float(string='Avg Wait to Done', compute='_compute_waiting_times')
    avg_total_waiting_time = fields.Float(string='Avg Total Waiting Time', compute='_compute_waiting_times')
    max_waiting_time = fields.Float(string='Max Waiting Time', compute='_compute_waiting_times')
    min_waiting_time = fields.Float(string='Min Waiting Time', compute='_compute_waiting_times')

    @api.depends()
    def _compute_waiting_times(self):
        for rec in self:
            weighings = self.env['truck.weighing'].search([('state', '=', 'done')])
            if weighings:
                rec.avg_waiting_time_to_first = sum(weighings.mapped('waiting_time_to_first')) / len(weighings)
                rec.avg_waiting_time_to_second = sum(weighings.mapped('waiting_time_to_second')) / len(weighings)
                rec.avg_waiting_time_to_done = sum(weighings.mapped('waiting_time_to_done')) / len(weighings)
                rec.avg_total_waiting_time = sum(weighings.mapped('total_waiting_time')) / len(weighings)
                total_times = weighings.mapped('total_waiting_time')
                rec.max_waiting_time = max(total_times) if total_times else 0.0
                rec.min_waiting_time = min([t for t in total_times if t > 0]) if total_times else 0.0
            else:
                rec.avg_waiting_time_to_first = 0.0
                rec.avg_waiting_time_to_second = 0.0
                rec.avg_waiting_time_to_done = 0.0
                rec.avg_total_waiting_time = 0.0
                rec.max_waiting_time = 0.0
                rec.min_waiting_time = 0.0

    def get_waiting_time_data(self):
        weighings = self.env['truck.weighing'].search([('state', '=', 'done')], order='create_date desc', limit=50)
        return {
            'labels': [w.name for w in weighings],
            'to_first': weighings.mapped('waiting_time_to_first'),
            'to_second': weighings.mapped('waiting_time_to_second'),
            'to_done': weighings.mapped('waiting_time_to_done'),
            'total': weighings.mapped('total_waiting_time'),
        }
