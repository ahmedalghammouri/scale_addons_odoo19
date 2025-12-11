# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class TruckFleet(models.Model):
    _name = 'truck.fleet'
    _description = 'Truck Fleet Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'plate_number'

    plate_number = fields.Char(string='Plate Number', required=True, index=True, tracking=True)
    truck_type_ids = fields.Many2many('truck.type', string='Truck Types')
    driver_name = fields.Char(string='Default Driver')
    driver_phone = fields.Char(string='Driver Phone')
    
    # Trailer Information
    trailer_count = fields.Integer(string='Number of Trailers', default=1, tracking=True)
    max_weight_per_trailer = fields.Float(string='Max Weight per Trailer (KG)', tracking=True)
    total_max_weight = fields.Float(string='Total Max Weight (KG)', compute='_compute_total_max_weight', store=True, tracking=True)
    tare_weight = fields.Float(string='Empty Truck Weight (KG)', help="Weight of empty truck", tracking=True)
    
    # Company & Status
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    
    # Statistics
    weighing_count = fields.Integer(string='Weighing Records', compute='_compute_weighing_count')
    last_weighing_date = fields.Datetime(string='Last Weighing', compute='_compute_weighing_count')
    
    # Additional Info
    notes = fields.Text(string='Notes')
    
    @api.depends('trailer_count', 'max_weight_per_trailer')
    def _compute_total_max_weight(self):
        for truck in self:
            truck.total_max_weight = truck.trailer_count * truck.max_weight_per_trailer
    
    def _compute_weighing_count(self):
        for truck in self:
            weighings = self.env['truck.weighing'].search([('truck_id', '=', truck.id)])
            truck.weighing_count = len(weighings)
            truck.last_weighing_date = weighings[0].weighing_date if weighings else False
    
    def action_view_weighing_records(self):
        return {
            'name': 'Weighing Records',
            'type': 'ir.actions.act_window',
            'res_model': 'truck.weighing',
            'view_mode': 'list,form',
            'domain': [('truck_id', '=', self.id)],
            'context': {'default_truck_id': self.id}
        }
    
    @api.constrains('plate_number')
    def _check_plate_number(self):
        for truck in self:
            if truck.plate_number:
                existing = self.search([('plate_number', '=', truck.plate_number), ('id', '!=', truck.id)])
                if existing:
                    raise ValidationError(_('Plate number %s already exists!') % truck.plate_number)
    
    _sql_constraints = [
        ('plate_number_unique', 'unique(plate_number)', 'Plate number must be unique!')
    ]


class TruckType(models.Model):
    _name = 'truck.type'
    _description = 'Truck Type'
    
    name = fields.Char(string='Type Name', required=True)
    color = fields.Integer(string='Color')
    
    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Truck type name must be unique!')
    ]
