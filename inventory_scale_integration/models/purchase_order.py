from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    weighing_count = fields.Integer(compute='_compute_weighing_data')
    total_net_weight = fields.Float(compute='_compute_weighing_data', string='Total Net Weight')
    total_net_weight_display = fields.Char(compute='_compute_weighing_data', string='Weight Display')
    has_weighable_products = fields.Boolean(compute='_compute_has_weighable_products')

    @api.depends('order_line.product_id.is_weighable')
    def _compute_has_weighable_products(self):
        for order in self:
            order.has_weighable_products = any(line.product_id.is_weighable for line in order.order_line)

    def _compute_weighing_data(self):
        for order in self:
            weighings = self.env['truck.weighing'].search([('purchase_order_id', '=', order.id)])
            order.weighing_count = len(weighings)
            order.total_net_weight = sum(weighings.mapped('net_weight'))
            if order.total_net_weight > 2000:
                order.total_net_weight_display = f"{order.total_net_weight / 1000:.1f} T"
            else:
                order.total_net_weight_display = f"{order.total_net_weight:.0f} KG"

    def action_view_weighing_records(self):
        weighings = self.env['truck.weighing'].search([('purchase_order_id', '=', self.id)])
        return {
            'type': 'ir.actions.act_window',
            'name': 'Weighing Records',
            'res_model': 'truck.weighing',
            'view_mode': 'list,form',
            'domain': [('id', 'in', weighings.ids)],
            'context': {'default_purchase_order_id': self.id}
        }