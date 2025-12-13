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
            'receipts_to_weigh': {
                name: 'Receipts to Weigh',
                res_model: 'stock.picking',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: async () => {
                    const ids = await this.orm.call('weighing.overview', 'get_receipts_to_weigh_ids', []);
                    return [['id', 'in', ids]];
                },
                context: { 'create': true }
            },

            'in_progress': {
                name: 'Weighing In Progress',
                res_model: 'truck.weighing',
                view_mode: 'kanban,list,form',
                views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
                domain: [['state', 'in', ['draft', 'first', 'second']]],
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
            'new_weighing_receipt': {
                name: 'New Weighing from Receipt',
                res_model: 'truck.weighing',
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'current',
                context: { 'default_from_receipt': true }
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
            // Receipts filtered actions
            'receipts_urgent': {
                name: 'Urgent Receipts to Weigh',
                res_model: 'stock.picking',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [
                    ['state', 'in', ['assigned', 'confirmed']],
                    ['picking_type_code', '=', 'incoming'],
                    ['move_ids.product_id.is_weighable', '=', true],
                    ['scheduled_date', '<=', new Date().toISOString().split('T')[0]]
                ],
            },
            'receipts_by_vendor': {
                name: 'Receipts to Weigh by Vendor',
                res_model: 'stock.picking',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [
                    ['state', 'in', ['assigned', 'confirmed']],
                    ['picking_type_code', '=', 'incoming'],
                    ['move_ids.product_id.is_weighable', '=', true]
                ],
                context: { 'group_by': 'partner_id' }
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
                name: 'First Weighing Captured',
                res_model: 'truck.weighing',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['state', '=', 'first']],
            },
            'weighing_tare': {
                name: 'Second Weighing Captured',
                res_model: 'truck.weighing',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['state', '=', 'second']],
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

            'truck_receipts': {
                name: 'Truck-Related Receipts',
                res_model: 'stock.picking',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [
                    ['picking_type_code', '=', 'incoming'],
                    ['move_ids.product_id.is_weighable', '=', true]
                ],
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
            },
            // Stock Performance Analytics Actions
            'high_fulfillment': {
                name: 'High Fulfillment Records (≥95%)',
                res_model: 'truck.weighing',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [
                    ['state', '=', 'done'],
                    '|', ['picking_id', '!=', false], ['delivery_id', '!=', false]
                ],
            },
            'over_delivered': {
                name: 'Over-Delivered Records',
                res_model: 'truck.weighing',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [
                    ['state', '=', 'done'],
                    '|', ['picking_id', '!=', false], ['delivery_id', '!=', false]
                ],
            },
            'exact_match': {
                name: 'Exact Match Records',
                res_model: 'truck.weighing',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [
                    ['state', '=', 'done'],
                    '|', ['picking_id', '!=', false], ['delivery_id', '!=', false]
                ],
            },
            'under_delivered': {
                name: 'Under-Delivered Records',
                res_model: 'truck.weighing',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [
                    ['state', '=', 'done'],
                    '|', ['picking_id', '!=', false], ['delivery_id', '!=', false]
                ],
            },
            'avg_fulfillment': {
                name: 'Fulfillment Analysis',
                res_model: 'truck.weighing',
                view_mode: 'graph,pivot',
                views: [[false, 'graph'], [false, 'pivot']],
                domain: [
                    ['state', '=', 'done'],
                    '|', ['picking_id', '!=', false], ['delivery_id', '!=', false]
                ],
            },
            'total_variance': {
                name: 'Variance Analysis',
                res_model: 'truck.weighing',
                view_mode: 'list,graph',
                views: [[false, 'list'], [false, 'graph']],
                domain: [
                    ['state', '=', 'done'],
                    '|', ['picking_id', '!=', false], ['delivery_id', '!=', false]
                ],
            },
            'total_received': {
                name: 'Total Received Weight',
                res_model: 'truck.weighing',
                view_mode: 'list,graph',
                views: [[false, 'list'], [false, 'graph']],
                domain: [
                    ['state', '=', 'done'],
                    ['picking_id', '!=', false]
                ],
                context: { 'group_by': 'product_id' }
            },
            'total_delivered': {
                name: 'Total Delivered Weight',
                res_model: 'truck.weighing',
                view_mode: 'list,graph',
                views: [[false, 'list'], [false, 'graph']],
                domain: [
                    ['state', '=', 'done'],
                    ['delivery_id', '!=', false]
                ],
                context: { 'group_by': 'product_id' }
            },
            'top_products': {
                name: 'Products Weighed',
                res_model: 'truck.weighing',
                view_mode: 'list,graph,pivot',
                views: [[false, 'list'], [false, 'graph'], [false, 'pivot']],
                domain: [
                    ['state', '=', 'done'],
                    '|', ['picking_id', '!=', false], ['delivery_id', '!=', false]
                ],
                context: { 'group_by': 'product_id' }
            },
            'accuracy_rate': {
                name: 'Accuracy Rate Analysis',
                res_model: 'truck.weighing',
                view_mode: 'graph,pivot',
                views: [[false, 'graph'], [false, 'pivot']],
                domain: [
                    ['state', '=', 'done'],
                    '|', ['picking_id', '!=', false], ['delivery_id', '!=', false]
                ],
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
            // New state-based actions
            'weighing_draft_incoming': {
                name: 'Draft Weighing - Incoming',
                res_model: 'truck.weighing',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['state', '=', 'draft'], ['operation_type', '=', 'incoming']],
            },
            'weighing_draft_outgoing': {
                name: 'Draft Weighing - Outgoing',
                res_model: 'truck.weighing',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['state', '=', 'draft'], ['operation_type', '=', 'outgoing']],
            },
            'weighing_first': {
                name: 'Loaded & Ready - All',
                res_model: 'truck.weighing',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['state', '=', 'first']],
            },
            'weighing_first_incoming': {
                name: 'Loaded & Ready - Incoming',
                res_model: 'truck.weighing',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['state', '=', 'first'], ['operation_type', '=', 'incoming']],
            },
            'weighing_first_outgoing': {
                name: 'Loaded & Ready - Outgoing',
                res_model: 'truck.weighing',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['state', '=', 'first'], ['operation_type', '=', 'outgoing']],
            },
            'weighing_second': {
                name: 'Unloaded & Pending - All',
                res_model: 'truck.weighing',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['state', '=', 'second']],
            },
            'weighing_second_incoming': {
                name: 'Unloaded & Pending - Incoming',
                res_model: 'truck.weighing',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['state', '=', 'second'], ['operation_type', '=', 'incoming']],
            },
            'weighing_second_outgoing': {
                name: 'Unloaded & Pending - Outgoing',
                res_model: 'truck.weighing',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['state', '=', 'second'], ['operation_type', '=', 'outgoing']],
            },
            'in_progress_incoming': {
                name: 'In Progress - Incoming',
                res_model: 'truck.weighing',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['state', 'in', ['draft', 'first', 'second']], ['operation_type', '=', 'incoming']],
            },
            'in_progress_outgoing': {
                name: 'In Progress - Outgoing',
                res_model: 'truck.weighing',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['state', 'in', ['draft', 'first', 'second']], ['operation_type', '=', 'outgoing']],
            },
            'waiting_time_fast': {
                name: 'Fast Processing (<30 min)',
                res_model: 'truck.weighing',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['state', '=', 'done'], ['total_waiting_time', '<', 30]],
            },
            'waiting_time_normal': {
                name: 'Normal Processing (30-60 min)',
                res_model: 'truck.weighing',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['state', '=', 'done'], ['total_waiting_time', '>=', 30], ['total_waiting_time', '<=', 60]],
            },
            'waiting_time_slow': {
                name: 'Slow Processing (>60 min)',
                res_model: 'truck.weighing',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['state', '=', 'done'], ['total_waiting_time', '>', 60]],
            },
            'waiting_time_analysis': {
                name: 'Waiting Time Analysis',
                res_model: 'truck.weighing',
                view_mode: 'graph,pivot',
                views: [[false, 'graph'], [false, 'pivot']],
                domain: [['state', '=', 'done'], ['total_waiting_time', '>', 0]],
            },
            'truck_performance': {
                name: 'Truck Performance Analysis',
                res_model: 'truck.weighing',
                view_mode: 'graph,pivot',
                views: [[false, 'graph'], [false, 'pivot']],
                domain: [['state', '=', 'done'], ['truck_id', '!=', false]],
                context: { 'group_by': 'truck_id' }
            },
            'idle_trucks': {
                name: 'Idle Trucks',
                res_model: 'truck.fleet',
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['active', '=', true]],
            },
            'busy_trucks': {
                name: 'High Activity Trucks',
                res_model: 'truck.weighing',
                view_mode: 'list,graph',
                views: [[false, 'list'], [false, 'graph']],
                domain: [['state', '=', 'done'], ['truck_id', '!=', false]],
                context: { 'group_by': 'truck_id' }
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

    formatTime(minutes) {
        if (minutes < 60) {
            return `${minutes.toFixed(1)} min`;
        }
        const hours = Math.floor(minutes / 60);
        const mins = Math.round(minutes % 60);
        return `${hours}h ${mins}m`;
    }

    getProgressColor(percent) {
        if (percent >= 80) return 'success';
        if (percent >= 50) return 'warning';
        return 'danger';
    }
}

WeighingOverviewDashboard.template = "inventory_scale_integration.WeighingDashboardTemplate";

registry.category("actions").add("weighing_overview_dashboard", WeighingOverviewDashboard);