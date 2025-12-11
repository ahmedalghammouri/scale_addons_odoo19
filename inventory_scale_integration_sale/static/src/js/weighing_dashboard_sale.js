/** @odoo-module **/

import { WeighingOverviewDashboard } from "@inventory_scale_integration_stock/js/weighing_dashboard";
import { patch } from "@web/core/utils/patch";

patch(WeighingOverviewDashboard.prototype, {
    async onCardAction(actionName) {
        const saleActions = {
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
            'new_weighing_sale': {
                name: 'New Weighing from Sale',
                res_model: 'truck.weighing',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'current',
                context: { 'default_from_sale': true }
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
