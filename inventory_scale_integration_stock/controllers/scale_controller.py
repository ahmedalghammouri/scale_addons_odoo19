# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

class ScaleController(http.Controller):

    @http.route('/scale/receive_weight', type='http', auth='none', methods=['POST'], csrf=False)
    def receive_weight_from_scale(self, **kwargs):
        """
        API Endpoint to receive raw weight data from the external Python middleware.
        The middleware must send 'weight' only.
        """
        try:
            data = json.loads(request.httprequest.data.decode('utf-8'))
            weight = data.get('weight')
            if not weight:
                return json.dumps({'error': "Missing 'weight' in the request payload.", 'success': False})

            weight = float(weight)

            _logger.info("Received weight: %s KG", weight)

            # البحث عن أحدث عملية موازنة مفتوحة
            weighing_record = request.env['truck.weighing'].sudo().search([
                ('state', 'in', ['draft', 'first'])
            ], limit=1, order='create_date desc')

            if not weighing_record:
                return json.dumps({'error': "No active weighing record found. Please create a weighing record first.", 'success': False})

            # 1. تسجيل الوزن القائم (Gross)
            if weighing_record.state == 'draft':
                weighing_record.sudo().write({
                    'gross_weight': weight,
                    'state': 'first',
                })
                message = f"Gross Weight ({weight} KG) recorded for {weighing_record.name} - Truck: {weighing_record.truck_plate}."
            
            # 2. تسجيل الوزن الفارغ (Tare)
            elif weighing_record.state == 'first':
                if weight >= weighing_record.gross_weight:
                    # تفريغ غير مكتمل أو خطأ في الميزان
                    return json.dumps({'error': f"Tare Weight ({weight} KG) must be less than Gross Weight ({weighing_record.gross_weight} KG). Please re-weigh the empty truck.", 'success': False})
                    
                weighing_record.sudo().write({
                    'tare_weight': weight,
                    'state': 'second',
                })
                # بعد تسجيل الوزن الفارغ، يتم حساب الوزن الصافي وتحديث المخزون
                weighing_record.sudo().action_update_inventory()
                message = f"Tare Weight ({weight} KG) recorded. Net Weight: {weighing_record.net_weight} KG. Inventory updated for {weighing_record.name} - Truck: {weighing_record.truck_plate}."

            else:
                 return json.dumps({'error': f"Weighing record {weighing_record.name} is in an unexpected state: {weighing_record.state}.", 'success': False})

            return json.dumps({'message': message, 'success': True})

        except Exception as e:
            _logger.error("Error receiving weight data: %s", str(e))
            return json.dumps({'error': str(e), 'success': False})