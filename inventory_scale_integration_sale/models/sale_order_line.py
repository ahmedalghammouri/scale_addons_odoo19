# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    weighing_ids = fields.One2many('truck.weighing', 'sale_line_id', string='Weighing Records')
    total_delivered_weight = fields.Float(string='Total Delivered (KG)', compute='_compute_total_delivered_weight', store=True)
    
    @api.depends('weighing_ids.net_weight', 'weighing_ids.state')
    def _compute_total_delivered_weight(self):
        for line in self:
            done_weighings = line.weighing_ids.filtered(lambda w: w.state == 'done')
            line.total_delivered_weight = sum(done_weighings.mapped('net_weight'))
