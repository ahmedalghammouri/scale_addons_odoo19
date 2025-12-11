# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import requests
from datetime import datetime

_logger = logging.getLogger(__name__)

class WeighingScale(models.Model):
    _name = 'weighing.scale'
    _description = 'Weighing Scale Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Scale Name', required=True, tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    # Connection Settings
    ip_address = fields.Char(string='IP Address', required=True, tracking=True)
    port = fields.Integer(string='Port', required=True, default=5000, tracking=True)
    timeout = fields.Integer(string='Timeout (seconds)', default=2)
    
    # Status & Monitoring
    is_enabled = fields.Boolean(string='Enabled', default=True, tracking=True)
    connection_status = fields.Selection([
        ('connected', 'Connected'),
        ('disconnected', 'Disconnected'),
        ('error', 'Error')
    ], string='Connection Status', default='disconnected', readonly=True)
    last_check_date = fields.Datetime(string='Last Check', readonly=True)
    last_read_weight = fields.Float(string='Last Read Weight (KG)', readonly=True)
    last_read_date = fields.Datetime(string='Last Read Date', readonly=True)
    error_message = fields.Text(string='Last Error', readonly=True)
    
    # User Assignment
    user_ids = fields.Many2many('res.users', 'scale_user_rel', 'scale_id', 'user_id', string='Assigned Users')
    
    # Notes
    notes = fields.Text(string='Notes')
    
    # Related Records
    weighing_count = fields.Integer(string='Weighing Records', compute='_compute_weighing_count')
    
    def _compute_weighing_count(self):
        for record in self:
            record.weighing_count = self.env['truck.weighing'].search_count([('scale_id', '=', record.id)])

    @api.constrains('ip_address', 'port')
    def _check_ip_port(self):
        for record in self:
            if not record.ip_address or not record.port:
                raise UserError(_("IP Address and Port are required."))

    def action_test_connection(self):
        """ Test connection to the scale """
        self.ensure_one()
        try:
            url = f"http://{self.ip_address}:{self.port}/get_weight"
            response = requests.get(url, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                weight = data.get('weight', 0.0)
                self.write({
                    'connection_status': 'connected',
                    'last_check_date': fields.Datetime.now(),
                    'last_read_weight': weight,
                    'last_read_date': fields.Datetime.now(),
                    'error_message': False
                })
                self.message_post(body=_("Connection successful. Weight: %s KG") % weight)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Connected successfully. Weight: %s KG') % weight,
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise Exception(_("Invalid response from scale"))
        except Exception as e:
            self.write({
                'connection_status': 'error',
                'last_check_date': fields.Datetime.now(),
                'error_message': str(e)
            })
            raise UserError(_("Connection failed: %s") % str(e))

    def get_weight(self):
        """ Get current weight from scale """
        self.ensure_one()
        if not self.is_enabled:
            raise UserError(_("Scale '%s' is disabled.") % self.name)
        
        try:
            url = f"http://{self.ip_address}:{self.port}/get_weight"
            response = requests.get(url, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                weight = data.get('weight', 0.0)
                self.write({
                    'connection_status': 'connected',
                    'last_check_date': fields.Datetime.now(),
                    'last_read_weight': weight,
                    'last_read_date': fields.Datetime.now(),
                    'error_message': False
                })
                return weight
            else:
                raise Exception(_("Invalid response from scale"))
        except Exception as e:
            self.write({
                'connection_status': 'error',
                'last_check_date': fields.Datetime.now(),
                'error_message': str(e)
            })
            raise UserError(_("Error reading from scale '%s': %s") % (self.name, str(e)))

    def action_enable(self):
        """ Enable scale """
        self.write({'is_enabled': True})

    def action_disable(self):
        """ Disable scale """
        self.write({'is_enabled': False})
    
    def action_view_weighing_records(self):
        """ View all truck weighing records for this scale """
        self.ensure_one()
        return {
            'name': _('Weighing Records'),
            'type': 'ir.actions.act_window',
            'res_model': 'truck.weighing',
            'view_mode': 'list,form',
            'domain': [('scale_id', '=', self.id)],
            'context': {'default_scale_id': self.id}
        }