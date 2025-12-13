# -*- coding: utf-8 -*-
from odoo import models, fields

class WeighingScale(models.Model):
    _inherit = 'weighing.scale'
    
    zpl_printer_ids = fields.Many2many('zpl.printer', string='ZPL Printers', help='Printers assigned to this scale')
