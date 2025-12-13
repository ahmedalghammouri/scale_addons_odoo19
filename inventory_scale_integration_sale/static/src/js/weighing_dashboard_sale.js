/** @odoo-module **/

import { WeighingOverviewDashboard } from "@inventory_scale_integration_dashboard/js/weighing_dashboard";
import { patch } from "@web/core/utils/patch";

patch(WeighingOverviewDashboard.prototype, {
    async onCardAction(actionName) {
        const saleActions = {
            'sale_orders': {
                name: 'Sale Orders with Weighable Products',
                res_model: 'sale.order',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [
                    ['state', 'in', ['draft', 'sent', 'sale']],
                    ['order_line.product_id.is_weighable', '=', true]
                ],
            },
            'sale_urgent': {
                name: 'Urgent Sale Orders',
                res_model: 'sale.order',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [
                    ['state', 'in', ['draft', 'sent', 'sale']],
                    ['order_line.product_id.is_weighable', '=', true],
                    ['commitment_date', '<=', new Date().toISOString().split('T')[0]]
                ],
            },
            'sale_by_customer': {
                name: 'Sale Orders by Customer',
                res_model: 'sale.order',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [
                    ['state', 'in', ['draft', 'sent', 'sale']],
                    ['order_line.product_id.is_weighable', '=', true]
                ],
                context: { 'group_by': 'partner_id' }
            },
        };

        const actionConfig = saleActions[actionName];
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
