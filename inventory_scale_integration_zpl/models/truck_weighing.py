# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime

class TruckWeighing(models.Model):
    _inherit = 'truck.weighing'
    
    zpl_printer_id = fields.Many2one('zpl.printer', string='ZPL Printer', compute='_compute_zpl_printer', store=False)
    print_job_ids = fields.One2many('zpl.print.job', 'weighing_id', string='Print Jobs')
    print_job_count = fields.Integer(compute='_compute_print_job_count')

    @api.depends('scale_id', 'create_uid')
    def _compute_zpl_printer(self):
        for rec in self:
            printer = False
            # Priority 1: User's default printer
            if rec.create_uid and rec.create_uid.default_zpl_printer_id:
                printer = rec.create_uid.default_zpl_printer_id
            # Priority 2: Scale's assigned printer
            elif rec.scale_id and rec.scale_id.zpl_printer_ids:
                printer = rec.scale_id.zpl_printer_ids[0]
            # Priority 3: First enabled printer
            else:
                printer = self.env['zpl.printer'].search([('is_enabled', '=', True)], limit=1)
            rec.zpl_printer_id = printer

    def _compute_print_job_count(self):
        for rec in self:
            rec.print_job_count = len(rec.print_job_ids)

    def action_print_zpl_label(self):
        self.ensure_one()
        if not self.zpl_printer_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('No ZPL printer configured. Please configure a printer first.'),
                    'type': 'danger',
                    'sticky': True,
                }
            }
        
        try:
            zpl_code = self._generate_zpl_label()
            job = self.env['zpl.print.job'].create({
                'name': f'Label - {self.name}',
                'printer_id': self.zpl_printer_id.id,
                'weighing_id': self.id,
                'print_type': 'label',
                'zpl_code': zpl_code,
            })
            job.action_print()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Label sent to printer: %s') % self.zpl_printer_id.name,
                    'type': 'success',
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Print Failed'),
                    'message': str(e),
                    'type': 'danger',
                    'sticky': True,
                }
            }

    def action_print_zpl_ticket(self):
        self.ensure_one()
        if not self.zpl_printer_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('No ZPL printer configured.'),
                    'type': 'danger',
                    'sticky': True,
                }
            }
        
        try:
            zpl_code = self._generate_zpl_ticket()
            job = self.env['zpl.print.job'].create({
                'name': f'Ticket - {self.name}',
                'printer_id': self.zpl_printer_id.id,
                'weighing_id': self.id,
                'print_type': 'ticket',
                'zpl_code': zpl_code,
            })
            job.action_print()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Ticket sent to printer: %s') % self.zpl_printer_id.name,
                    'type': 'success',
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Print Failed'),
                    'message': str(e),
                    'type': 'danger',
                    'sticky': True,
                }
            }

    def action_print_zpl_certificate(self):
        self.ensure_one()
        if not self.zpl_printer_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('No ZPL printer configured.'),
                    'type': 'danger',
                    'sticky': True,
                }
            }
        
        try:
            zpl_code = self._generate_zpl_certificate()
            job = self.env['zpl.print.job'].create({
                'name': f'Certificate - {self.name}',
                'printer_id': self.zpl_printer_id.id,
                'weighing_id': self.id,
                'print_type': 'certificate',
                'zpl_code': zpl_code,
            })
            job.action_print()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Certificate sent to printer: %s') % self.zpl_printer_id.name,
                    'type': 'success',
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Print Failed'),
                    'message': str(e),
                    'type': 'danger',
                    'sticky': True,
                }
            }

    def _generate_zpl_label(self):
        """Generate ZPL code for weighing label"""
        self.ensure_one()
        
        dpi_factor = 8 if self.zpl_printer_id.dpi == '203' else 12
        width_dots = self.zpl_printer_id.label_width * dpi_factor
        height_dots = self.zpl_printer_id.label_height * dpi_factor
        
        # Handle Arabic support
        if self.zpl_printer_id.support_arabic:
            product_text = self.product_id.name if self.product_id else 'N/A'
        else:
            product_text = f"ID: {self.product_id.id}" if self.product_id else 'N/A'
        
        zpl = f"^XA^PW{width_dots}^LL{height_dots}\n"
        zpl += f"^FO30,20^A0N,50,50^FD{self.name}^FS\n"
        zpl += f"^FO30,80^GB{width_dots-60},2,2^FS\n"
        zpl += f"^FO30,95^A0N,35,35^FDPlate: {self.truck_plate or 'N/A'}^FS\n"
        zpl += f"^FO30,135^A0N,30,30^FDProduct: {product_text}^FS\n"
        zpl += f"^FO30,175^GB{width_dots-60},2,2^FS\n"
        zpl += f"^FO30,190^A0N,60,60^FDNET: {self.net_weight:.0f} KG^FS\n"
        zpl += f"^FO30,260^A0N,25,25^FDGross: {self.gross_weight:.0f} KG  Tare: {self.tare_weight:.0f} KG^FS\n"
        zpl += f"^FO30,295^A0N,20,20^FD{self.weighing_date.strftime('%Y-%m-%d %H:%M') if self.weighing_date else ''}^FS\n"
        zpl += f"^FO30,325^BY2^BCN,80,Y,N,N^FD{self.barcode or self.name}^FS\n"
        zpl += "^XZ"
        return zpl

    def _generate_zpl_ticket(self):
        """Generate ZPL code for driver ticket"""
        self.ensure_one()
        
        dpi_factor = 8 if self.zpl_printer_id.dpi == '203' else 12
        width_dots = self.zpl_printer_id.label_width * dpi_factor
        height_dots = self.zpl_printer_id.label_height * dpi_factor
        
        # Determine first weight label based on operation type
        if self.operation_type == 'incoming':
            first_label = 'Gross'
            first_weight = self.gross_weight
        else:  # outgoing
            first_label = 'Tare'
            first_weight = self.tare_weight
        
        zpl = f"^XA^PW{width_dots}^LL{height_dots}\n"
        zpl += "^FO20,15^A0N,35,35^FDDRIVER TICKET^FS\n"
        zpl += f"^FO20,55^GB{width_dots-40},2,2^FS\n"
        zpl += f"^FO20,65^A0N,25,25^FDWeighing: {self.name}^FS\n"
        zpl += f"^FO20,95^A0N,25,25^FDPlate: {self.truck_plate or 'N/A'}^FS\n"
        zpl += f"^FO20,125^A0N,20,20^FDDate: {self.weighing_date.strftime('%Y-%m-%d %H:%M') if self.weighing_date else ''}^FS\n"
        zpl += f"^FO20,150^A0N,25,25^FD{first_label}: {first_weight:.0f} KG^FS\n"
        zpl += f"^FO20,185^BY2^BCN,70,Y,N,N^FD{self.barcode or self.name}^FS\n"
        zpl += "^XZ"
        return zpl

    def _generate_zpl_certificate(self):
        """Generate ZPL code for weighing certificate"""
        self.ensure_one()
        
        dpi_factor = 8 if self.zpl_printer_id.dpi == '203' else 12
        width_dots = self.zpl_printer_id.label_width * dpi_factor
        height_dots = self.zpl_printer_id.label_height * dpi_factor
        
        # Handle Arabic support
        if self.zpl_printer_id.support_arabic:
            driver_text = self.driver_name or 'N/A'
            partner_text = self.partner_id.name if self.partner_id else 'N/A'
            product_text = self.product_id.name if self.product_id else 'N/A'
        else:
            driver_text = 'See Reference'
            partner_text = f"ID: {self.partner_id.id}" if self.partner_id else 'N/A'
            product_text = f"ID: {self.product_id.id}" if self.product_id else 'N/A'
        
        zpl = f"^XA^PW{width_dots}^LL{height_dots}\n"
        zpl += "^FO30,20^A0N,40,40^FDWEIGHING CERTIFICATE^FS\n"
        zpl += f"^FO30,70^GB{width_dots-60},2,2^FS\n"
        zpl += f"^FO30,85^A0N,25,25^FDReference: {self.name}^FS\n"
        zpl += f"^FO30,115^A0N,25,25^FDDate: {self.weighing_date.strftime('%Y-%m-%d %H:%M') if self.weighing_date else ''}^FS\n"
        zpl += f"^FO30,150^GB{width_dots-60},2,2^FS\n"
        zpl += f"^FO30,165^A0N,25,25^FDPlate: {self.truck_plate or 'N/A'}^FS\n"
        zpl += f"^FO30,195^A0N,25,25^FDDriver: {driver_text}^FS\n"
        zpl += f"^FO30,225^A0N,25,25^FDPartner: {partner_text}^FS\n"
        zpl += f"^FO30,255^A0N,25,25^FDProduct: {product_text}^FS\n"
        zpl += f"^FO30,290^GB{width_dots-60},2,2^FS\n"
        zpl += f"^FO30,305^A0N,30,30^FDGross: {self.gross_weight:.2f} KG^FS\n"
        zpl += f"^FO30,340^A0N,30,30^FDTare: {self.tare_weight:.2f} KG^FS\n"
        zpl += f"^FO30,380^GB{width_dots-60},3,3^FS\n"
        zpl += f"^FO30,395^A0N,45,45^FDNET: {self.net_weight:.2f} KG^FS\n"
        zpl += "^XZ"
        return zpl

    def action_view_print_jobs(self):
        return {
            'name': _('Print Jobs'),
            'type': 'ir.actions.act_window',
            'res_model': 'zpl.print.job',
            'view_mode': 'list,form',
            'domain': [('weighing_id', '=', self.id)],
            'context': {'default_weighing_id': self.id}
        }

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if record.zpl_printer_id and record.zpl_printer_id.auto_print_label and record.state == 'done':
                try:
                    record.action_print_zpl_label()
                except:
                    pass
        return records

    def write(self, vals):
        res = super().write(vals)
        if vals.get('state') == 'first':
            for record in self:
                if record.zpl_printer_id and record.zpl_printer_id.auto_print_ticket:
                    try:
                        record.action_print_zpl_ticket()
                    except:
                        pass
        elif vals.get('state') == 'done':
            for record in self:
                if record.zpl_printer_id:
                    if record.zpl_printer_id.auto_print_certificate:
                        try:
                            record.action_print_zpl_certificate()
                        except:
                            pass
                    if record.zpl_printer_id.auto_print_label:
                        try:
                            record.action_print_zpl_label()
                        except:
                            pass
        return res
