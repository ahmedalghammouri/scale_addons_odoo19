/** @odoo-module **/

import { Component, onWillStart, onMounted, useState, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";

export class WeighingOverviewDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            data: {},
            loading: true,
            activeTab: 'records',
            timePeriod: 'week'
        });
        this.recordsChartRef = useRef("recordsChart");
        this.recordsStatusChartRef = useRef("recordsStatusChart");
        this.weightsChartRef = useRef("weightsChart");
        this.timeTrackingChartRef = useRef("timeTrackingChart");
        this.productsChartRef = useRef("productsChart");
        this.productsWeightChartRef = useRef("productsWeightChart");
        this.productsTimeChartRef = useRef("productsTimeChart");
        this.productsTrendChartRef = useRef("productsTrendChart");
        this.stockChartRef = useRef("stockChart");
        this.waitingChartRef = useRef("waitingChart");
        this.truckChartRef = useRef("truckChart");
        this.charts = {};

        onWillStart(async () => {
            await this.loadData();
        });

        onMounted(() => {
            this.renderCharts();
        });
    }

    setActiveTab(tab) {
        this.state.activeTab = tab;
        setTimeout(() => this.renderCharts(), 100);
    }

    async setTimePeriod(period, ev) {
        if (ev) ev.preventDefault();
        this.state.timePeriod = period;
        const trendData = await this.orm.call("weighing.overview", "get_overview_data", [], {period: period});
        this.state.data.trend_data = trendData.trend_data;
        setTimeout(() => this.renderCharts(), 100);
    }

    renderProductsChart() {
        if (this.charts.products) this.charts.products.destroy();
        const ctx = this.productsChartRef.el.getContext('2d');
        const data = this.state.data.stock_performance || {};
        this.charts.products = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Products Weighed', 'Receipts', 'Deliveries'],
                datasets: [{
                    label: 'Count',
                    data: [
                        data.products_count || 0,
                        data.receipts_count || 0,
                        data.deliveries_count || 0
                    ],
                    backgroundColor: [
                        'rgba(52, 152, 219, 0.8)',
                        'rgba(46, 204, 113, 0.8)',
                        'rgba(231, 76, 60, 0.8)'
                    ],
                    borderColor: ['#3498db', '#2ecc71', '#e74c3c'],
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' } } }
            }
        });
    }

    renderProductsWeightChart() {
        if (this.charts.productsWeight) this.charts.productsWeight.destroy();
        const ctx = this.productsWeightChartRef.el.getContext('2d');
        const trendData = this.state.data.trend_data || {};
        
        const labels = trendData.labels || [];
        const receivedData = trendData.received_weights || [];
        const deliveredData = trendData.delivered_weights || [];
        
        this.charts.productsWeight = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Received (Tons)',
                    data: receivedData,
                    backgroundColor: 'rgba(46, 204, 113, 0.2)',
                    borderColor: '#2ecc71',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 6
                }, {
                    label: 'Delivered (Tons)',
                    data: deliveredData,
                    backgroundColor: 'rgba(231, 76, 60, 0.2)',
                    borderColor: '#e74c3c',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: true, position: 'top', labels: { font: { size: 12, weight: 'bold' } } } },
                scales: { y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' }, ticks: { callback: (value) => value.toFixed(1) + ' T' } } }
            }
        });
    }

    renderProductsTimeChart() {
        if (this.charts.productsTime) this.charts.productsTime.destroy();
        const ctx = this.productsTimeChartRef.el.getContext('2d');
        const data = this.state.data.waiting_time_analysis || {};
        this.charts.productsTime = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Fast (<30min)', 'Normal (30-60min)', 'Slow (>60min)'],
                datasets: [{
                    label: 'Processing Count',
                    data: [
                        data.fast_count || 0,
                        data.normal_count || 0,
                        data.slow_count || 0
                    ],
                    backgroundColor: [
                        'rgba(46, 204, 113, 0.8)',
                        'rgba(241, 196, 15, 0.8)',
                        'rgba(231, 76, 60, 0.8)'
                    ],
                    borderColor: ['#2ecc71', '#f1c40f', '#e74c3c'],
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' } } }
            }
        });
    }

    renderProductsTrendChart() {
        if (this.charts.productsTrend) this.charts.productsTrend.destroy();
        const ctx = this.productsTrendChartRef.el.getContext('2d');
        const trendData = this.state.data.trend_data || {};
        
        const labels = trendData.labels || [];
        const opsData = trendData.operations_count || [];
        const waitData = trendData.avg_wait_times || [];
        
        this.charts.productsTrend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Operations Count',
                    data: opsData,
                    backgroundColor: 'rgba(52, 152, 219, 0.2)',
                    borderColor: '#3498db',
                    borderWidth: 3,
                    yAxisID: 'y',
                    tension: 0.4,
                    pointRadius: 6
                }, {
                    label: 'Avg Wait Time (min)',
                    data: waitData,
                    backgroundColor: 'rgba(155, 89, 182, 0.2)',
                    borderColor: '#9b59b6',
                    borderWidth: 3,
                    yAxisID: 'y1',
                    tension: 0.4,
                    pointRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: { legend: { display: true, position: 'top', labels: { font: { size: 12, weight: 'bold' } } } },
                scales: {
                    y: { type: 'linear', display: true, position: 'left', beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' } },
                    y1: { type: 'linear', display: true, position: 'right', beginAtZero: true, grid: { drawOnChartArea: false } }
                }
            }
        });
    }

    renderCharts() {
        if (this.state.activeTab === 'records' && this.recordsChartRef.el) {
            this.renderRecordsChart();
            this.renderRecordsStatusChart();
            this.renderWeightsChart();
            this.renderTimeTrackingChart();
        } else if (this.state.activeTab === 'products' && this.productsChartRef.el) {
            this.renderProductsChart();
            this.renderProductsWeightChart();
            this.renderProductsTimeChart();
            this.renderProductsTrendChart();
        } else if (this.state.activeTab === 'stock' && this.stockChartRef.el) {
            this.renderStockChart();
        } else if (this.state.activeTab === 'waiting' && this.waitingChartRef.el) {
            this.renderWaitingChart();
        } else if (this.state.activeTab === 'truck' && this.truckChartRef.el) {
            this.renderTruckChart();
        }
    }

    renderRecordsChart() {
        if (this.charts.records) this.charts.records.destroy();
        const ctx = this.recordsChartRef.el.getContext('2d');
        const data = this.state.data;
        this.charts.records = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Awaiting Initial', 'First Captured', 'Second Captured', 'Completed'],
                datasets: [{
                    label: 'Incoming',
                    data: [
                        data.draft_details?.incoming_count || 0,
                        data.in_progress_incoming?.first_count || 0,
                        data.in_progress_incoming?.second_count || 0,
                        data.all_records?.completed_today || 0
                    ],
                    backgroundColor: 'rgba(52, 152, 219, 0.8)',
                    borderColor: '#3498db',
                    borderWidth: 2,
                    borderRadius: 8
                }, {
                    label: 'Outgoing',
                    data: [
                        data.draft_details?.outgoing_count || 0,
                        data.in_progress_outgoing?.first_count || 0,
                        data.in_progress_outgoing?.second_count || 0,
                        data.all_records?.completed_week || 0
                    ],
                    backgroundColor: 'rgba(230, 126, 34, 0.8)',
                    borderColor: '#e67e22',
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: true, position: 'top', labels: { font: { size: 12, weight: 'bold' } } } },
                scales: { y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' } } }
            }
        });
    }

    renderRecordsStatusChart() {
        if (this.charts.recordsStatus) this.charts.recordsStatus.destroy();
        const ctx = this.recordsStatusChartRef.el.getContext('2d');
        const data = this.state.data.all_records || {};
        this.charts.recordsStatus = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Draft', 'First Weigh', 'Second Weigh', 'Done'],
                datasets: [{
                    data: [
                        data.draft_percent || 0,
                        data.first_percent || 0,
                        data.second_percent || 0,
                        data.done_percent || 0
                    ],
                    backgroundColor: [
                        'rgba(52, 152, 219, 0.8)',
                        'rgba(155, 89, 182, 0.8)',
                        'rgba(241, 196, 15, 0.8)',
                        'rgba(46, 204, 113, 0.8)'
                    ],
                    borderWidth: 3,
                    borderColor: '#fff',
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true, position: 'right', labels: { font: { size: 12, weight: 'bold' }, padding: 15 } }
                }
            }
        });
    }

    renderWeightsChart() {
        if (this.charts.weights) this.charts.weights.destroy();
        const ctx = this.weightsChartRef.el.getContext('2d');
        const data = this.state.data.stock_performance || {};
        const received = (data.total_received || 0) / 1000;
        const delivered = (data.total_delivered || 0) / 1000;
        this.charts.weights = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Received', 'Delivered'],
                datasets: [{
                    label: 'Total Weight (Tons)',
                    data: [received, delivered],
                    backgroundColor: [
                        'rgba(46, 204, 113, 0.8)',
                        'rgba(231, 76, 60, 0.8)'
                    ],
                    borderColor: ['#2ecc71', '#e74c3c'],
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { 
                    legend: { display: true, position: 'top', labels: { font: { size: 12, weight: 'bold' } } },
                    tooltip: {
                        callbacks: {
                            label: (context) => `${context.parsed.y.toFixed(2)} Tons`
                        }
                    }
                },
                scales: { y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' }, ticks: { callback: (value) => value.toFixed(1) + ' T' } } }
            }
        });
    }

    renderTimeTrackingChart() {
        if (this.charts.timeTracking) this.charts.timeTracking.destroy();
        const ctx = this.timeTrackingChartRef.el.getContext('2d');
        const data = this.state.data.waiting_time_analysis || {};
        this.charts.timeTracking = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['To First', 'To Second', 'To Done', 'Total Avg'],
                datasets: [{
                    label: 'Average Time (minutes)',
                    data: [
                        data.avg_to_first || 0,
                        data.avg_to_second || 0,
                        data.avg_to_done || 0,
                        data.avg_total || 0
                    ],
                    backgroundColor: 'rgba(155, 89, 182, 0.2)',
                    borderColor: '#9b59b6',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#9b59b6',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: true, position: 'top', labels: { font: { size: 12, weight: 'bold' } } } },
                scales: { y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' } } }
            }
        });
    }

    renderStockChart() {
        if (this.charts.stock) this.charts.stock.destroy();
        const ctx = this.stockChartRef.el.getContext('2d');
        const data = this.state.data.stock_performance || {};
        this.charts.stock = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['High Fulfillment', 'Exact Match', 'Over Delivered', 'Under Delivered'],
                datasets: [{
                    label: 'Records Count',
                    data: [
                        data.high_fulfillment || 0,
                        data.exact_match || 0,
                        data.over_delivered || 0,
                        data.under_delivered || 0
                    ],
                    backgroundColor: ['#28a745', '#007bff', '#17a2b8', '#ffc107'],
                    borderRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true } }
            }
        });
    }

    renderWaitingChart() {
        if (this.charts.waiting) this.charts.waiting.destroy();
        const ctx = this.waitingChartRef.el.getContext('2d');
        const data = this.state.data.waiting_time_analysis || {};
        this.charts.waiting = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Fast (<30min)', 'Normal (30-60min)', 'Slow (>60min)'],
                datasets: [{
                    label: 'Processing Speed Distribution',
                    data: [
                        data.fast_count || 0,
                        data.normal_count || 0,
                        data.slow_count || 0
                    ],
                    backgroundColor: 'rgba(102, 126, 234, 0.2)',
                    borderColor: '#667eea',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true } }
            }
        });
    }

    renderTruckChart() {
        if (this.charts.truck) this.charts.truck.destroy();
        const ctx = this.truckChartRef.el.getContext('2d');
        const data = this.state.data.truck_performance || {};
        this.charts.truck = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['High Activity', 'Moderate Activity', 'Idle Trucks'],
                datasets: [{
                    label: 'Truck Distribution',
                    data: [
                        data.high_activity || 0,
                        data.moderate_activity || 0,
                        data.idle_trucks || 0
                    ],
                    backgroundColor: ['#28a745', '#ffc107', '#dc3545'],
                    borderRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true } }
            }
        });
    }

    async loadData() {
        this.state.loading = true;
        try {
            const data = await this.orm.call("weighing.overview", "get_overview_data", [], {period: this.state.timePeriod});
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