# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import socket
import logging

_logger = logging.getLogger(__name__)

class ZPLPrinter(models.Model):
    _name = 'zpl.printer'
    _description = 'ZPL Thermal Printer'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Printer Name', required=True, tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    # Connection
    connection_type = fields.Selection([
        ('network', 'Network (IP)'),
        ('usb', 'USB/Serial')
    ], string='Connection Type', default='network', required=True, tracking=True)
    
    ip_address = fields.Char(string='IP Address', tracking=True)
    port = fields.Integer(string='Port', default=9100, tracking=True)
    usb_device = fields.Char(string='USB Device Path', help='e.g., /dev/usb/lp0 or COM1')
    
    # Printer Settings
    dpi = fields.Selection([
        ('203', '203 DPI'),
        ('300', '300 DPI'),
        ('600', '600 DPI')
    ], string='Resolution', default='203', tracking=True)
    
    label_width = fields.Integer(string='Label Width (mm)', default=100, tracking=True)
    label_height = fields.Integer(string='Label Height (mm)', default=150, tracking=True)
    
    print_speed = fields.Selection([
        ('2', 'Slow (2 ips)'),
        ('4', 'Medium (4 ips)'),
        ('6', 'Fast (6 ips)'),
        ('8', 'Very Fast (8 ips)')
    ], string='Print Speed', default='4', tracking=True)
    
    darkness = fields.Integer(string='Darkness', default=15, help='0-30, higher = darker', tracking=True)
    
    # Auto-print Settings
    auto_print_label = fields.Boolean(string='Auto-print Label', default=False, tracking=True)
    auto_print_ticket = fields.Boolean(string='Auto-print Ticket', default=False, tracking=True)
    auto_print_certificate = fields.Boolean(string='Auto-print Certificate', default=False, tracking=True)
    
    # Language Support
    support_arabic = fields.Boolean(string='Support Arabic Text', default=False, tracking=True, 
                                    help='Enable if printer has Arabic fonts installed. Disable to skip Arabic text fields.')
    
    # Assignments
    scale_ids = fields.Many2many('weighing.scale', string='Assigned Scales')
    user_ids = fields.Many2many('res.users', 'zpl_printer_user_rel', 'printer_id', 'user_id', string='Assigned Users')
    
    # Status
    is_enabled = fields.Boolean(string='Enabled', default=True, tracking=True)
    connection_status = fields.Selection([
        ('connected', 'Connected'),
        ('disconnected', 'Disconnected'),
        ('error', 'Error')
    ], string='Status', default='disconnected', readonly=True)
    last_check_date = fields.Datetime(string='Last Check', readonly=True)
    error_message = fields.Text(string='Last Error', readonly=True)
    
    print_count = fields.Integer(string='Total Prints', compute='_compute_print_count')
    notes = fields.Text(string='Notes')

    @api.constrains('ip_address', 'port', 'connection_type')
    def _check_connection_settings(self):
        for rec in self:
            if rec.connection_type == 'network' and (not rec.ip_address or not rec.port):
                raise UserError(_("IP Address and Port are required for network printers."))
            if rec.connection_type == 'usb' and not rec.usb_device:
                raise UserError(_("USB Device Path is required for USB printers."))

    def _compute_print_count(self):
        for rec in self:
            rec.print_count = self.env['zpl.print.job'].search_count([('printer_id', '=', rec.id)])

    def action_test_connection(self):
        self.ensure_one()
        try:
            test_zpl = "^XA^FO50,50^ADN,36,20^FDTest Print^FS^XZ"
            result = self._send_to_printer(test_zpl)
            
            self.write({
                'connection_status': 'connected',
                'last_check_date': fields.Datetime.now(),
                'error_message': False
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Test print sent successfully!'),
                    'type': 'success',
                    'sticky': False,
                }
            }
        except Exception as e:
            error_msg = str(e)
            self.write({
                'connection_status': 'error',
                'last_check_date': fields.Datetime.now(),
                'error_message': error_msg
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Failed'),
                    'message': error_msg,
                    'type': 'danger',
                    'sticky': True,
                }
            }

    def _send_to_printer(self, zpl_code):
        self.ensure_one()
        if not self.is_enabled:
            raise UserError(_("Printer '%s' is disabled.") % self.name)
        
        if self.connection_type == 'network':
            return self._send_network(zpl_code)
        elif self.connection_type == 'usb':
            return self._send_usb(zpl_code)

    def _send_network(self, zpl_code):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        try:
            sock.connect((self.ip_address, self.port))
            sock.sendall(zpl_code.encode('utf-8'))
            self.write({
                'connection_status': 'connected',
                'last_check_date': fields.Datetime.now(),
                'error_message': False
            })
            return True
        finally:
            sock.close()

    def _send_usb(self, zpl_code):
        with open(self.usb_device, 'wb') as printer:
            printer.write(zpl_code.encode('utf-8'))
        self.write({
            'connection_status': 'connected',
            'last_check_date': fields.Datetime.now(),
            'error_message': False
        })
        return True

    def action_enable(self):
        self.write({'is_enabled': True})

    def action_disable(self):
        self.write({'is_enabled': False})

    def action_view_print_jobs(self):
        return {
            'name': _('Print Jobs'),
            'type': 'ir.actions.act_window',
            'res_model': 'zpl.print.job',
            'view_mode': 'list,form',
            'domain': [('printer_id', '=', self.id)],
            'context': {'default_printer_id': self.id}
        }


class ZPLPrintJob(models.Model):
    _name = 'zpl.print.job'
    _description = 'ZPL Print Job'
    _order = 'create_date desc'

    name = fields.Char(string='Job Name', required=True)
    printer_id = fields.Many2one('zpl.printer', string='Printer', required=True, ondelete='cascade')
    weighing_id = fields.Many2one('truck.weighing', string='Weighing Record', ondelete='set null')
    
    print_type = fields.Selection([
        ('label', 'Label'),
        ('ticket', 'Ticket'),
        ('certificate', 'Certificate'),
        ('custom', 'Custom')
    ], string='Print Type', required=True)
    
    zpl_code = fields.Text(string='ZPL Code', required=True)
    
    state = fields.Selection([
        ('pending', 'Pending'),
        ('printing', 'Printing'),
        ('done', 'Done'),
        ('failed', 'Failed')
    ], string='Status', default='pending')
    
    error_message = fields.Text(string='Error Message')
    print_date = fields.Datetime(string='Print Date')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)

    def action_print(self):
        for job in self:
            try:
                job.state = 'printing'
                job.printer_id._send_to_printer(job.zpl_code)
                job.write({
                    'state': 'done',
                    'print_date': fields.Datetime.now(),
                    'error_message': False
                })
            except Exception as e:
                job.write({
                    'state': 'failed',
                    'error_message': str(e)
                })
                raise

    def action_retry(self):
        self.filtered(lambda j: j.state == 'failed').action_print()
