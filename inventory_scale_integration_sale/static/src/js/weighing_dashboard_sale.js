/** @odoo-module **/

import { WeighingOverviewDashboard } from "@inventory_scale_integration_base/js/weighing_dashboard";
import { patch } from "@web/core/utils/patch";

patch(WeighingOverviewDashboard.prototype, {
    async onCardAction(actionName) {
        const salesActions = {
            'deliveries_to_weigh': {
                name: 'Deliveries to Weigh',
                res_model: 'stock.picking',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: async () => {
                    const ids = await this.orm.call('weighing.overview', 'get_deliveries_to_weigh_ids', []);
                    return [['id', 'in', ids]];
                },
                context: { 'create': true }
            },
            'deliveries_urgent': {
                name: 'Urgent Deliveries to Weigh',
                res_model: 'stock.picking',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [
                    ['state', 'in', ['assigned', 'confirmed']],
                    ['picking_type_code', '=', 'outgoing'],
                    ['move_ids.product_id.is_weighable', '=', true],
                    ['scheduled_date', '<=', new Date().toISOString().split('T')[0]]
                ],
            },
            'deliveries_by_customer': {
                name: 'Deliveries to Weigh by Customer',
                res_model: 'stock.picking',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [
                    ['state', 'in', ['assigned', 'confirmed']],
                    ['picking_type_code', '=', 'outgoing'],
                    ['move_ids.product_id.is_weighable', '=', true]
                ],
                context: { 'group_by': 'partner_id' }
            },
            'new_weighing_delivery': {
                name: 'New Weighing from Delivery',
                res_model: 'truck.weighing',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'current',
                context: { 'default_from_delivery': true }
            },
            'sales_to_weigh': {
                name: 'Sales Orders to Weigh',
                res_model: 'sale.order',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: async () => {
                    const ids = await this.orm.call('weighing.overview', 'get_sales_to_weigh_ids', []);
                    return [['id', 'in', ids]];
                },
                context: { 'create': true }
            },
            'sales_by_amount': {
                name: 'Sales Orders by Amount',
                res_model: 'sale.order',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [
                    ['state', 'in', ['sale', 'done']],
                    ['order_line.product_id.is_weighable', '=', true]
                ],
                context: { 'group_by': 'amount_total' }
            },
            'sales_pending_qty': {
                name: 'Sales with Pending Quantity',
                res_model: 'sale.order',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [
                    ['state', 'in', ['sale', 'done']],
                    ['order_line.product_id.is_weighable', '=', true]
                ],
            },
            'sales_by_customer': {
                name: 'Sales Orders by Customer',
                res_model: 'sale.order',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [
                    ['state', 'in', ['sale', 'done']],
                    ['order_line.product_id.is_weighable', '=', true]
                ],
                context: { 'group_by': 'partner_id' }
            },
            'new_weighing_sale': {
                name: 'New Weighing from Sale',
                res_model: 'truck.weighing',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'current',
                context: { 'default_from_sale': true }
            },
        };

        const actionConfig = salesActions[actionName];
        if (actionConfig) {
            let domain = actionConfig.domain;
            if (typeof domain === 'function') {
                domain = await domain();
            }
            await this.action.doAction({
                type: 'ir.actions.act_window',
                ...actionConfig,
                domain: domain
            });
        } else {
            await super.onCardAction(actionName);
        }
    }
});