# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class TruckWeighing(models.Model):
    _name = 'truck.weighing'
    _description = 'Truck Weighing Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'weighing_date desc, id desc'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    barcode = fields.Char(string='Barcode', compute='_compute_barcode', store=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    scale_id = fields.Many2one('weighing.scale', string='Weighing Scale', domain="[('is_enabled', '=', True), ('id', 'in', user_scale_ids)]", tracking=True)
    user_scale_ids = fields.Many2many('weighing.scale', compute='_compute_user_scales')
    
    truck_id = fields.Many2one('truck.fleet', string='Truck', required=True, tracking=True)
    truck_plate = fields.Char(string='Plate Number', related='truck_id.plate_number', store=True, readonly=True)
    driver_name = fields.Char(string='Driver Name', related='truck_id.driver_name', readonly=False)
    
    partner_id = fields.Many2one('res.partner', string='Partner', tracking=True)
    product_id = fields.Many2one('product.product', string='Product', required=True, tracking=True)
    operation_type = fields.Selection([
        ('incoming', 'Incoming'),
        ('outgoing', 'Outgoing')
    ], string='Operation Type', tracking=True)

    live_weight = fields.Float(string='Live Weight (KG)', readonly=True)
    gross_weight = fields.Float(string='Gross Weight (KG)', tracking=True)
    tare_weight = fields.Float(string='Tare Weight (KG)', tracking=True)
    net_weight = fields.Float(string='Net Weight (KG)', compute='_compute_net_weight', store=True, tracking=True)
    
    weighing_date = fields.Datetime(string='Weighing Date', default=fields.Datetime.now, tracking=True)
    gross_date = fields.Datetime(string='Gross Weight Date', readonly=True)
    tare_date = fields.Datetime(string='Tare Weight Date', readonly=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('first', 'First Weighing Captured'),
        ('second', 'Second Weighing Captured'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    first_time = fields.Datetime(string='First Weighing Time', readonly=True)
    second_time = fields.Datetime(string='Second Weighing Time', readonly=True)
    done_time = fields.Datetime(string='Done Time', readonly=True)
    
    waiting_time_to_first = fields.Float(string='Waiting Time to First Weigh (minutes)', compute='_compute_waiting_times', store=True)
    waiting_time_to_second = fields.Float(string='Waiting Time to Second Weigh (minutes)', compute='_compute_waiting_times', store=True)
    waiting_time_to_done = fields.Float(string='Waiting Time to Update Inventory (minutes)', compute='_compute_waiting_times', store=True)
    total_waiting_time = fields.Float(string='Total Waiting Time (minutes)', compute='_compute_waiting_times', store=True)
    
    notes = fields.Text(string='Notes')
    
    @api.depends('name')
    def _compute_barcode(self):
        for record in self:
            record.barcode = record.name
    
    @api.depends('create_date', 'first_time', 'second_time', 'done_time')
    def _compute_waiting_times(self):
        for record in self:
            if record.create_date and record.first_time:
                record.waiting_time_to_first = (record.first_time - record.create_date).total_seconds() / 60
            else:
                record.waiting_time_to_first = 0.0
            
            if record.first_time and record.second_time:
                record.waiting_time_to_second = (record.second_time - record.first_time).total_seconds() / 60
            else:
                record.waiting_time_to_second = 0.0
            
            if record.second_time and record.done_time:
                record.waiting_time_to_done = (record.done_time - record.second_time).total_seconds() / 60
            else:
                record.waiting_time_to_done = 0.0
            
            record.total_waiting_time = record.waiting_time_to_first + record.waiting_time_to_second + record.waiting_time_to_done
    
    @api.depends('gross_weight', 'tare_weight')
    def _compute_net_weight(self):
        for record in self:
            if record.gross_weight > 0 and record.tare_weight > 0:
                record.net_weight = record.gross_weight - record.tare_weight
            else:
                record.net_weight = 0.0
    
    @api.depends('create_uid')
    def _compute_user_scales(self):
        for record in self:
            user = record.create_uid or self.env.user
            record.user_scale_ids = user.assigned_scale_ids
    
    @api.onchange('user_scale_ids')
    def _onchange_user_scale_ids(self):
        if self.user_scale_ids and not self.scale_id:
            self.scale_id = self.user_scale_ids[0]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('truck.weighing.sequence') or _('New')
            if not vals.get('scale_id'):
                if self.env.user.default_scale_id:
                    vals['scale_id'] = self.env.user.default_scale_id.id
                elif self.env.user.assigned_scale_ids:
                    vals['scale_id'] = self.env.user.assigned_scale_ids[0].id
        return super(TruckWeighing, self).create(vals_list)

    def action_fetch_live_weight(self):
        self.ensure_one()
        if not self.scale_id:
            raise UserError(_("Please select a weighing scale first."))
        
        try:
            weight = self.scale_id.get_weight()
            self.live_weight = weight
            self.message_post(body=_("Live weight fetched from %s: %s KG") % (self.scale_id.name, self.live_weight))
        except Exception as e:
            raise UserError(_("Error: %s") % str(e))

    def action_set_first_weight(self):
        self.ensure_one()
        if self.live_weight <= 0:
            raise UserError(_("Please fetch live weight first."))
        
        # Incoming: First weight is GROSS (truck full)
        # Outgoing: First weight is TARE (truck empty)
        if self.operation_type == 'incoming':
            self.gross_weight = self.live_weight
            self.gross_date = fields.Datetime.now()
            self.message_post(body=_("First weight (Gross - Full truck): %s KG") % self.gross_weight)
        else:  # outgoing
            self.tare_weight = self.live_weight
            self.tare_date = fields.Datetime.now()
            self.message_post(body=_("First weight (Tare - Empty truck): %s KG") % self.tare_weight)
        
        self.first_time = fields.Datetime.now()
        self.state = 'first'

    def action_set_second_weight(self):
        self.ensure_one()
        if self.live_weight <= 0:
            raise UserError(_("Please fetch live weight first."))
        
        # Incoming: Second weight is TARE (truck empty after unloading)
        # Outgoing: Second weight is GROSS (truck full after loading)
        if self.operation_type == 'incoming':
            if self.live_weight >= self.gross_weight:
                raise UserError(_("Second weight (empty truck) must be less than first weight (full truck)."))
            self.tare_weight = self.live_weight
            self.tare_date = fields.Datetime.now()
            self.message_post(body=_("Second weight (Tare - Empty truck): %s KG") % self.tare_weight)
        else:  # outgoing
            if self.live_weight <= self.tare_weight:
                raise UserError(_("Second weight (full truck) must be greater than first weight (empty truck)."))
            self.gross_weight = self.live_weight
            self.gross_date = fields.Datetime.now()
            self.message_post(body=_("Second weight (Gross - Full truck): %s KG") % self.gross_weight)
        
        self.second_time = fields.Datetime.now()
        self.state = 'second'

    # Keep old methods for backward compatibility
    def action_set_gross_from_live(self):
        return self.action_set_first_weight()

    def action_set_tare_from_live(self):
        return self.action_set_second_weight()
    
    def action_mark_done(self):
        self.ensure_one()
        if self.state == 'second' and self.net_weight > 0:
            self.done_time = fields.Datetime.now()
            self.state = 'done'
        else:
            raise UserError(_("Cannot mark as done. Complete tare weighing first."))
    
    def action_print_driver_ticket(self):
        self.ensure_one()
        return self.env.ref('inventory_scale_integration_base.action_report_driver_ticket').report_action(self)
    
    def action_print_certificate(self):
        self.ensure_one()
        return self.env.ref('inventory_scale_integration_base.action_report_weighing_certificate').report_action(self)
    
    @api.onchange('truck_id')
    def _onchange_truck_id(self):
        if self.truck_id:
            self.driver_name = self.truck_id.driver_name
