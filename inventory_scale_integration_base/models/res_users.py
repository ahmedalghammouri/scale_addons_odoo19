# -*- coding: utf-8 -*-
from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    default_scale_id = fields.Many2one('weighing.scale', string='Default Weighing Scale')
    assigned_scale_ids = fields.Many2many('weighing.scale', 'scale_user_rel', 'user_id', 'scale_id', string='Assigned Scales')