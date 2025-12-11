# -*- coding: utf-8 -*-
from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    is_weighable = fields.Boolean(
        string='Weighable Product',
        default=False,
        help='Enable this product for weighbridge operations. Only weighable products will appear in POs and receipts for weighing.'
    )