/** @odoo-module **/

import { WeighingOverviewDashboard } from "@inventory_scale_integration_stock/js/weighing_dashboard";
import { patch } from "@web/core/utils/patch";

patch(WeighingOverviewDashboard.prototype, {
    async onCardAction(actionName) {
        const purchaseActions = {
            'pos_to_weigh': {
                name: 'Purchase Orders to Weigh',
                res_model: 'purchase.order',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: async () => {
                    const ids = await this.orm.call('weighing.overview', 'get_pos_to_weigh_ids', []);
                    return [['id', 'in', ids]];
                },
                context: { 'create': true }
            },
            'new_weighing_po': {
                name: 'New Weighing from PO',
                res_model: 'truck.weighing',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'current',
                context: { 'default_from_po': true }
            },
            'pos_by_amount': {
                name: 'Purchase Orders by Amount',
                res_model: 'purchase.order',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [
                    ['state', 'in', ['purchase', 'done']],
                    ['order_line.product_id.is_weighable', '=', true]
                ],
                context: { 'group_by': 'amount_total' }
            },
            'pos_pending_qty': {
                name: 'POs with Pending Quantity',
                res_model: 'purchase.order',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [
                    ['state', 'in', ['purchase', 'done']],
                    ['order_line.product_id.is_weighable', '=', true]
                ],
            },
            'pos_by_supplier': {
                name: 'Purchase Orders by Supplier',
                res_model: 'purchase.order',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [
                    ['state', 'in', ['purchase', 'done']],
                    ['order_line.product_id.is_weighable', '=', true]
                ],
                context: { 'group_by': 'partner_id' }
            },
        };

        const actionConfig = purchaseActions[actionName];
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
