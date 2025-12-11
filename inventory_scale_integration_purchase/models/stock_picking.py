from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    weighing_count = fields.Integer(compute='_compute_weighing_data')
    total_net_weight = fields.Float(compute='_compute_weighing_data', string='Total Net Weight')
    total_net_weight_display = fields.Char(compute='_compute_weighing_data', string='Weight Display')
    has_weighable_products = fields.Boolean(compute='_compute_has_weighable_products')

    @api.depends('move_ids.product_id.is_weighable')
    def _compute_has_weighable_products(self):
        for picking in self:
            picking.has_weighable_products = any(move.product_id.is_weighable for move in picking.move_ids)

    def _compute_weighing_data(self):
        for picking in self:
            weighings = self.env['truck.weighing'].search([('picking_id', '=', picking.id)])
            picking.weighing_count = len(weighings)
            picking.total_net_weight = sum(weighings.mapped('net_weight'))
            if picking.total_net_weight > 2000:
                picking.total_net_weight_display = f"{picking.total_net_weight / 1000:.1f} T"
            else:
                picking.total_net_weight_display = f"{picking.total_net_weight:.0f} KG"

    def action_view_weighing_records(self):
        weighings = self.env['truck.weighing'].search([('picking_id', '=', self.id)])
        return {
            'type': 'ir.actions.act_window',
            'name': 'Weighing Records',
            'res_model': 'truck.weighing',
            'view_mode': 'list,form',
            'domain': [('id', 'in', weighings.ids)],
            'context': {'default_picking_id': self.id}
        }