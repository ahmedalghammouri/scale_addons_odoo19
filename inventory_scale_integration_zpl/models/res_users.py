# -*- coding: utf-8 -*-
from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    default_zpl_printer_id = fields.Many2one('zpl.printer', string='Default ZPL Printer')
    assigned_zpl_printer_ids = fields.Many2many('zpl.printer', 'zpl_printer_user_rel', 'user_id', 'printer_id', string='Assigned ZPL Printers')
