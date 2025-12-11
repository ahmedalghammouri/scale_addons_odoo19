/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";

export class WeighingOverviewDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            data: {},
            loading: true
        });

        onWillStart(async () => {
            await this.loadData();
        });
    }

    async loadData() {
        this.state.loading = true;
        try {
            const data = await this.orm.call("weighing.overview", "get_overview_data", []);
            this.state.data = data;
        } catch (error) {
            console.error("Error loading dashboard data:", error);
            this.state.data = {}; // Fallback to empty data
        } finally {
            this.state.loading = false;
        }
    }

    async onCardAction(actionName) {
        const actions = {

            'in_progress': {
                name: 'Weighing In Progress',
                res_model: 'truck.weighing',
                view_mode: 'kanban,list,form',
                views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
                domain: [['state', 'in', ['draft', 'gross', 'tare']]],
            },
            'all_records': {
                name: 'All Weighing Records',
                res_model: 'truck.weighing',
                view_mode: 'kanban,list,form',
                views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
                domain: [],
            },
            'new_weighing': {
                name: 'New Weighing Record',
                res_model: 'truck.weighing',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'current',
            },


            'truck_fleet': {
                name: 'Truck Fleet',
                res_model: 'truck.fleet',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [],
            },
            'scale_settings': {
                name: 'Weighing Scales',
                res_model: 'weighing.scale',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [],
            },
            'reports': {
                name: 'Weighing Analysis',
                res_model: 'truck.weighing',
                view_mode: 'graph,pivot',
                views: [[false, 'graph'], [false, 'pivot']],
                domain: [['state', '=', 'done']],
            },


            // Weighing state filtered actions
            'weighing_draft': {
                name: 'Draft Weighing Records',
                res_model: 'truck.weighing',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['state', '=', 'draft']],
            },
            'weighing_gross': {
                name: 'Gross Weight Captured',
                res_model: 'truck.weighing',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['state', '=', 'gross']],
            },
            'weighing_tare': {
                name: 'Tare Weight Captured',
                res_model: 'truck.weighing',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['state', '=', 'tare']],
            },
            // Time-based filtered actions
            'completed_today': {
                name: 'Completed Today',
                res_model: 'truck.weighing',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [
                    ['state', '=', 'done'],
                    ['weighing_date', '>=', new Date().toISOString().split('T')[0]]
                ],
            },
            'completed_week': {
                name: 'Completed This Week',
                res_model: 'truck.weighing',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [
                    ['state', '=', 'done'],
                    ['weighing_date', '>=', new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]]
                ],
            },
            // Truck management actions
            'all_trucks': {
                name: 'All Trucks',
                res_model: 'truck.fleet',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [],
            },

            'active_trucks': {
                name: 'Active Trucks',
                res_model: 'truck.fleet',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['active', '=', true]],
            },
            'trucks_with_weighing': {
                name: 'Trucks Used in Weighing',
                res_model: 'truck.fleet',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [], // Will be filtered by weighing records
            },
            'trucks_today': {
                name: 'Trucks Active Today',
                res_model: 'truck.weighing',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [
                    ['weighing_date', '>=', new Date().toISOString().split('T')[0]]
                ],
                context: { 'group_by': 'truck_id' }
            },
            'truck_utilization': {
                name: 'Truck Utilization Analysis',
                res_model: 'truck.weighing',
                view_mode: 'graph,pivot',
                views: [[false, 'graph'], [false, 'pivot']],
                domain: [['state', '=', 'done']],
                context: { 'group_by': 'truck_id' }
            },
            'new_truck': {
                name: 'New Truck',
                res_model: 'truck.fleet',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'current',
            },
            // Additional truck management actions
            'truck_weighings': {
                name: 'All Truck Weighings',
                res_model: 'truck.weighing',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['state', '=', 'done']],
                context: { 'group_by': 'truck_id' }
            },


            'truck_efficiency': {
                name: 'Truck Efficiency Analysis',
                res_model: 'truck.weighing',
                view_mode: 'graph,pivot',
                views: [[false, 'graph'], [false, 'pivot']],
                domain: [['state', '=', 'done']],
                context: { 'group_by': ['truck_id', 'weighing_date:week'] }
            },
            'weekly_truck_activity': {
                name: 'Weekly Truck Activity',
                res_model: 'truck.weighing',
                view_mode: 'list,graph',
                views: [[false, 'list'], [false, 'graph']],
                domain: [
                    ['weighing_date', '>=', new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]],
                    ['state', '=', 'done']
                ],
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

WeighingOverviewDashboard.template = "inventory_scale_integration_base.WeighingDashboardTemplate";

registry.category("actions").add("weighing_overview_dashboard", WeighingOverviewDashboard);