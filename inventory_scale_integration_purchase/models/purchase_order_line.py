# -*- coding: utf-8 -*-
from odoo import models, fields, api

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    weighing_ids = fields.One2many('truck.weighing', 'purchase_line_id', string='Weighing Records')
    total_received_weight = fields.Float(string='Total Received (KG)', compute='_compute_total_received_weight', store=True)
    
    @api.depends('weighing_ids.net_weight', 'weighing_ids.state')
    def _compute_total_received_weight(self):
        for line in self:
            done_weighings = line.weighing_ids.filtered(lambda w: w.state == 'done')
            line.total_received_weight = sum(done_weighings.mapped('net_weight'))
