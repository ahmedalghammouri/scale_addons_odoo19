# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

class ZPLPrintController(http.Controller):

    @http.route('/zpl/print', type='jsonrpc', auth='user', methods=['POST'])
    def print_zpl(self, printer_id, zpl_code, job_name='Manual Print', **kwargs):
        """API endpoint to send ZPL code to printer"""
        try:
            printer = request.env['zpl.printer'].browse(printer_id)
            if not printer.exists():
                return {'success': False, 'error': 'Printer not found'}
            
            job = request.env['zpl.print.job'].create({
                'name': job_name,
                'printer_id': printer_id,
                'print_type': 'custom',
                'zpl_code': zpl_code,
            })
            
            job.action_print()
            
            return {
                'success': True,
                'job_id': job.id,
                'message': f'Print job sent to {printer.name}'
            }
        except Exception as e:
            _logger.error(f"ZPL print error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route('/zpl/printer/status/<int:printer_id>', type='jsonrpc', auth='user')
    def get_printer_status(self, printer_id, **kwargs):
        """Get printer status"""
        try:
            printer = request.env['zpl.printer'].browse(printer_id)
            if not printer.exists():
                return {'success': False, 'error': 'Printer not found'}
            
            return {
                'success': True,
                'status': printer.connection_status,
                'name': printer.name,
                'is_enabled': printer.is_enabled,
                'last_check': printer.last_check_date.isoformat() if printer.last_check_date else None,
                'error': printer.error_message
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
