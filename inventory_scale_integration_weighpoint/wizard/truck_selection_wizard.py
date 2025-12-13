from odoo import models, fields, api, _
from odoo.exceptions import UserError

class TruckSelectionWizard(models.TransientModel):
    _name = 'truck.selection.wizard'
    _description = 'Truck Selection Wizard'

    picking_id = fields.Many2one('stock.picking', string='Picking Order', required=True)
    truck_id = fields.Many2one('truck.fleet', string='Truck', required=True)
    
    def action_confirm(self):
        weighing = self.env['truck.weighing'].action_quick_weigh_from_picking_with_truck(
            self.picking_id.id, 
            self.truck_id.id
        )
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'truck.weighing',
            'res_id': weighing.id,
            'view_mode': 'form',
            'view_id': self.env.ref('inventory_scale_integration_weighpoint.truck_weighing_view_form_weighpoint').id,
            'target': 'current',
        }
