/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class WeighingOverviewDashboardOut extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ data: {}, loading: true });

        onWillStart(async () => {
            await this.loadData();
        });
    }

    async loadData() {
        this.state.loading = true;
        try {
            const data = await this.orm.call("weighing.overview.outgoing", "get_overview_data", []);
            this.state.data = data;
        } catch (error) {
            console.error("Error loading dashboard data:", error);
            this.state.data = {};
        } finally {
            this.state.loading = false;
        }
    }

    async onCardAction(actionName) {
        const actions = {
            'deliveries_to_weigh': {
                name: 'Deliveries to Weigh',
                res_model: 'stock.picking',
                view_mode: 'list,form',
                domain: async () => {
                    const ids = await this.orm.call('weighing.overview.outgoing', 'get_deliveries_to_weigh_ids', []);
                    return [['id', 'in', ids]];
                }
            },
            'in_progress_outgoing': {
                name: 'In Progress - Outgoing',
                res_model: 'truck.weighing',
                view_mode: 'list,form',
                domain: [['state', 'in', ['draft', 'first', 'second']], ['operation_type', '=', 'outgoing']]
            },
            'all_records': {
                name: 'All Outgoing Records',
                res_model: 'truck.weighing',
                view_mode: 'list,form',
                domain: [['operation_type', '=', 'outgoing']]
            }
        };

        const actionConfig = actions[actionName];
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
        }
    }

    async refreshData() {
        await this.loadData();
    }

    formatWeight(weight) {
        if (weight > 2000) {
            return `${(weight / 1000).toFixed(1)} T`;
        }
        return `${weight.toLocaleString()} KG`;
    }
}

WeighingOverviewDashboardOut.template = "inventory_scale_integration_stock_out.WeighingDashboardTemplate";

registry.category("actions").add("weighing_overview_dashboard_out", WeighingOverviewDashboardOut);
