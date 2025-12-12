/** @odoo-module **/

import { WeighingOverviewDashboard } from "@inventory_scale_integration_stock/js/weighing_dashboard";
import { patch } from "@web/core/utils/patch";

patch(WeighingOverviewDashboard.prototype, {
    async onCardAction(actionName) {
        const purchaseActions = {
            'purchase_orders': {
                name: 'Purchase Orders with Weighable Products',
                res_model: 'purchase.order',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [
                    ['state', 'in', ['draft', 'sent', 'to approve', 'purchase']],
                    ['order_line.product_id.is_weighable', '=', true]
                ],
            },
            'purchase_urgent': {
                name: 'Urgent Purchase Orders',
                res_model: 'purchase.order',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [
                    ['state', 'in', ['draft', 'sent', 'to approve', 'purchase']],
                    ['order_line.product_id.is_weighable', '=', true],
                    ['date_planned', '<=', new Date().toISOString().split('T')[0]]
                ],
            },
            'purchase_by_vendor': {
                name: 'Purchase Orders by Vendor',
                res_model: 'purchase.order',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [
                    ['state', 'in', ['draft', 'sent', 'to approve', 'purchase']],
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
