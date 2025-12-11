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
        ('gross', 'Gross Captured'),
        ('tare', 'Tare Captured'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    notes = fields.Text(string='Notes')
    
    @api.depends('name')
    def _compute_barcode(self):
        for record in self:
            record.barcode = record.name
    
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

    def action_set_gross_from_live(self):
        self.ensure_one()
        if self.live_weight > 0:
            self.gross_weight = self.live_weight
            self.gross_date = fields.Datetime.now()
            self.state = 'gross'
            self.message_post(body=_("Gross weight set: %s KG") % self.gross_weight)
        else:
            raise UserError(_("Please fetch live weight first."))

    def action_set_tare_from_live(self):
        self.ensure_one()
        if self.live_weight > 0:
            if self.live_weight >= self.gross_weight:
                raise UserError(_("Tare weight must be less than gross weight."))
            self.tare_weight = self.live_weight
            self.tare_date = fields.Datetime.now()
            self.state = 'tare'
            self.message_post(body=_("Tare weight set: %s KG") % self.tare_weight)
        else:
            raise UserError(_("Please fetch live weight first."))
    
    def action_mark_done(self):
        self.ensure_one()
        if self.state == 'tare' and self.net_weight > 0:
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
