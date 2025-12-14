/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart, onMounted, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class WeighingWeighPointInterface extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        
        this.state = useState({
            activeTab: 'overview',
            barcode: "",
            pickings: [],
            pickingsWithWeighing: [],
            recentWeighings: [],
            pickingFilter: "all",
            searchText: "",
            selectedWeighing: null,
            advancedFilters: {
                truck: "",
                product: "",
                partner: "",
                state: ""
            },
            showAdvancedFilters: false,
            truckQueue: [],
            analytics: {
                completed_today: 0,
                in_progress: 0,
                avg_wait_time: "0m",
                waiting_count: 0,
                urgent_count: 0,
                efficiency_rate: 0,
                hourly_data: [],
                peak_hour: "--",
                total_weight_today: 0,
                avg_processing_time: "0m",
            },
            recentActivity: [],
            quickStats: {
                draft: 0,
                first: 0,
                second: 0,
            },
            loading: false,
            lastRefresh: new Date(),
        });

        this.refreshInterval = null;

        onWillStart(async () => {
            await this.loadPendingPickings();
            await this.loadWeighings();
            await this.loadAnalytics();
            await this.loadRecentActivity();
        });

        onMounted(() => {
            this.refreshInterval = setInterval(() => {
                this.refreshData();
            }, 60000);
            document.addEventListener('keydown', this.handleKeyPress.bind(this));
        });

        onWillUnmount(() => {
            if (this.refreshInterval) clearInterval(this.refreshInterval);
            document.removeEventListener('keydown', this.handleKeyPress.bind(this));
        });
    }

    async loadPendingPickings() {
        let domain = [["state", "!=", "done"]];
        
        if (this.state.pickingFilter === "incoming") {
            domain.push(["picking_type_code", "=", "incoming"]);
        } else if (this.state.pickingFilter === "outgoing") {
            domain.push(["picking_type_code", "=", "outgoing"]);
        }
        
        if (this.state.searchText) {
            domain.push(["name", "ilike", this.state.searchText]);
        }
        
        const allPickings = await this.orm.searchRead(
            "stock.picking",
            domain,
            ["name", "partner_id", "scheduled_date", "picking_type_code", "origin"],
            { limit: 50, order: "scheduled_date desc" }
        );
        
        // Get all weighing records (including done)
        const weighings = await this.orm.searchRead(
            "truck.weighing",
            [],
            ["picking_id", "delivery_id", "state"],
            { limit: 200 }
        );
        
        const pickingIdsWithWeighing = new Set();
        const pickingIdsWithInProgressWeighing = new Set();
        weighings.forEach(w => {
            const pickingId = w.picking_id ? w.picking_id[0] : (w.delivery_id ? w.delivery_id[0] : null);
            if (pickingId) {
                pickingIdsWithWeighing.add(pickingId);
                if (w.state !== 'done') {
                    pickingIdsWithInProgressWeighing.add(pickingId);
                }
            }
        });
        
        this.state.pickings = allPickings.filter(p => !pickingIdsWithWeighing.has(p.id));
        this.state.pickingsWithWeighing = allPickings.filter(p => pickingIdsWithInProgressWeighing.has(p.id));
    }

    async loadWeighings() {
        let domain = [["state", "in", ["draft", "first", "second"]]];
        
        if (this.state.searchText) {
            domain.push(["name", "ilike", this.state.searchText]);
        }
        
        if (this.state.advancedFilters.truck) {
            domain.push(["truck_plate", "ilike", this.state.advancedFilters.truck]);
        }
        if (this.state.advancedFilters.product) {
            domain.push(["product_id", "ilike", this.state.advancedFilters.product]);
        }
        if (this.state.advancedFilters.partner) {
            domain.push(["partner_id", "ilike", this.state.advancedFilters.partner]);
        }
        if (this.state.advancedFilters.state) {
            domain = [["state", "=", this.state.advancedFilters.state]];
        }
        
        this.state.recentWeighings = await this.orm.searchRead(
            "truck.weighing",
            domain,
            ["name", "truck_plate", "state", "operation_type", "barcode", "partner_id", "product_id", "net_weight", "gross_weight", "tare_weight", "create_date"],
            { limit: 30, order: "create_date asc" }
        );
        
        this.buildTruckQueue();
    }
    
    buildTruckQueue() {
        const queue = [];
        const now = Date.now();
        let cumulativeWait = 0;
        const avgProcessTime = 15;
        
        this.state.recentWeighings
            .filter(w => w.state === 'draft' || w.state === 'first')
            .forEach((w, idx) => {
                const createDate = new Date(w.create_date + ' UTC').getTime();
                const waitTime = Math.floor((now - createDate) / 60000);
                const estimatedWait = cumulativeWait + avgProcessTime;
                
                queue.push({
                    id: w.id,
                    position: idx + 1,
                    name: w.name,
                    truck: w.truck_plate,
                    state: w.state,
                    waitTime: waitTime,
                    estimatedWait: estimatedWait,
                    isUrgent: estimatedWait > 45
                });
                
                cumulativeWait += avgProcessTime;
            });
        
        this.state.truckQueue = queue;
    }

    async onBarcodeInput(ev) {
        if (ev.key === "Enter" && this.state.barcode) {
            await this.scanBarcode();
        }
    }

    async scanBarcode() {
        if (!this.state.barcode) return;
        
        try {
            // Try to find weighing record first by barcode
            const weighings = await this.orm.searchRead(
                "truck.weighing",
                [["barcode", "=", this.state.barcode], ["state", "in", ["draft", "first", "second"]]],
                ["id"],
                { limit: 1 }
            );
            
            if (weighings.length > 0) {
                this.action.doAction({
                    type: "ir.actions.act_window",
                    res_model: "truck.weighing",
                    res_id: weighings[0].id,
                    views: [[false, "form"]],
                    view_mode: "form",
                    target: "current",
                });
                this.state.barcode = "";
                return;
            }
            
            // Try to find by name (reference number)
            const weighingsByName = await this.orm.searchRead(
                "truck.weighing",
                [["name", "=", this.state.barcode], ["state", "in", ["draft", "first", "second"]]],
                ["id"],
                { limit: 1 }
            );
            
            if (weighingsByName.length > 0) {
                this.action.doAction({
                    type: "ir.actions.act_window",
                    res_model: "truck.weighing",
                    res_id: weighingsByName[0].id,
                    views: [[false, "form"]],
                    view_mode: "form",
                    target: "current",
                });
                this.state.barcode = "";
                return;
            }
            
            // Try to find picking order
            const pickings = await this.orm.searchRead(
                "stock.picking",
                [["name", "=", this.state.barcode], ["state", "in", ["assigned", "confirmed"]]],
                ["id"],
                { limit: 1 }
            );
            
            if (pickings.length > 0) {
                await this.createWeighingFromPicking(pickings[0].id);
                this.state.barcode = "";
                return;
            }
            
            this.notification.add("Barcode not found: " + this.state.barcode, { type: "danger" });
        } catch (error) {
            this.notification.add(error.message || "Error scanning barcode", { type: "danger" });
        }
        this.state.barcode = "";
    }

    async createWeighingFromPicking(pickingId) {
        try {
            const result = await this.orm.call(
                "truck.weighing",
                "action_quick_weigh_from_picking",
                [[], pickingId]
            );
            
            if (result && typeof result === 'object' && result.type) {
                this.action.doAction(result);
            } else if (result && result.id) {
                this.action.doAction({
                    type: "ir.actions.act_window",
                    res_model: "truck.weighing",
                    res_id: result.id,
                    views: [[false, "form"]],
                    view_mode: "form",
                    target: "current",
                });
            }
        } catch (error) {
            this.notification.add(error.message || "Error creating weighing", { type: "danger" });
        }
    }

    async openWeighing(weighingId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "truck.weighing",
            res_id: weighingId,
            views: [[false, "form"]],
            view_mode: "form",
            target: "current",
        });
    }

    async createNewWeighing() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "truck.weighing",
            views: [[false, "form"]],
            view_mode: "form",
            target: "current",
        });
    }
    
    async onPickingFilterChange(filter) {
        this.state.pickingFilter = filter;
        await this.loadPendingPickings();
    }
    
    async onSearchChange(ev) {
        this.state.searchText = ev.target.value;
    }
    
    async onSearch() {
        await this.loadPendingPickings();
        await this.loadWeighings();
    }
    
    toggleAdvancedFilters() {
        this.state.showAdvancedFilters = !this.state.showAdvancedFilters;
    }
    
    async applyAdvancedFilters() {
        await this.loadWeighings();
        this.notification.add('Filters applied', { type: 'success' });
    }
    
    async clearAdvancedFilters() {
        this.state.advancedFilters = { truck: "", product: "", partner: "", state: "" };
        await this.loadWeighings();
        this.notification.add('Filters cleared', { type: 'info' });
    }
    
    setActiveTab(tab) {
        this.state.activeTab = tab;
    }
    
    getQueueColor(estimatedWait) {
        if (estimatedWait <= 30) return 'success';
        if (estimatedWait <= 45) return 'warning';
        return 'danger';
    }
    
    formatTime(minutes) {
        const h = Math.floor(minutes / 60);
        const m = minutes % 60;
        return h > 0 ? `${h}:${m.toString().padStart(2, '0')}` : `${m}m`;
    }
    
    isOverdue(scheduledDate) {
        if (!scheduledDate) return false;
        return new Date(scheduledDate) < new Date();
    }
    
    getStateLabel(state) {
        const labels = {
            draft: 'Waiting',
            first: '1st Weigh',
            second: '2nd Weigh',
            done: 'Completed'
        };
        return labels[state] || state;
    }
    
    async loadAnalytics() {
        try {
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            const todayStr = today.toISOString().split('T')[0] + ' 00:00:00';
            
            const completedToday = await this.orm.searchRead(
                "truck.weighing",
                [["state", "=", "done"], ["create_date", ">=", todayStr]],
                ["net_weight", "create_date", "write_date"],
                { limit: 500 }
            );
            
            const inProgressRecords = await this.orm.searchRead(
                "truck.weighing",
                [["state", "in", ["draft", "first", "second"]]],
                ["state", "create_date"],
                { limit: 100 }
            );
            
            const draftRecords = inProgressRecords.filter(r => r.state === 'draft');
            const firstRecords = inProgressRecords.filter(r => r.state === 'first');
            const secondRecords = inProgressRecords.filter(r => r.state === 'second');
            
            let totalWaitMinutes = 0;
            const now = Date.now();
            draftRecords.forEach(record => {
                if (record.create_date) {
                    const createDate = new Date(record.create_date + ' UTC').getTime();
                    const waitMinutes = Math.floor((now - createDate) / 60000);
                    totalWaitMinutes += waitMinutes;
                }
            });
            const avgWaitMinutes = draftRecords.length > 0 ? Math.floor(totalWaitMinutes / draftRecords.length) : 0;
            const avgWaitTime = avgWaitMinutes < 60 ? `${avgWaitMinutes}m` : `${Math.floor(avgWaitMinutes / 60)}h ${avgWaitMinutes % 60}m`;
            
            let totalWeight = 0;
            let totalProcessMinutes = 0;
            const hourCounts = {};
            completedToday.forEach(record => {
                if (record.net_weight) totalWeight += record.net_weight;
                if (record.create_date && record.write_date) {
                    const created = new Date(record.create_date + ' UTC').getTime();
                    const completed = new Date(record.write_date + ' UTC').getTime();
                    totalProcessMinutes += Math.floor((completed - created) / 60000);
                }
                const hour = new Date(record.create_date).getHours();
                hourCounts[hour] = (hourCounts[hour] || 0) + 1;
            });
            
            const peakHour = Object.keys(hourCounts).length > 0 
                ? Object.entries(hourCounts).sort((a, b) => b[1] - a[1])[0][0] + ':00'
                : '--';
            
            const avgProcessMinutes = completedToday.length > 0 ? Math.floor(totalProcessMinutes / completedToday.length) : 0;
            const avgProcessTime = avgProcessMinutes < 60 ? `${avgProcessMinutes}m` : `${Math.floor(avgProcessMinutes / 60)}h ${avgProcessMinutes % 60}m`;
            
            const urgentCount = await this.orm.searchCount(
                "stock.picking",
                [["state", "in", ["assigned", "confirmed"]]]
            );
            
            const totalToday = completedToday.length + inProgressRecords.length;
            const efficiencyRate = totalToday > 0 ? Math.round((completedToday.length / totalToday) * 100) : 0;
            
            this.state.analytics = {
                completed_today: completedToday.length,
                in_progress: inProgressRecords.length,
                avg_wait_time: avgWaitTime,
                waiting_count: draftRecords.length,
                urgent_count: urgentCount,
                efficiency_rate: efficiencyRate,
                hourly_data: [],
                peak_hour: peakHour,
                total_weight_today: Math.round(totalWeight / 1000),
                avg_processing_time: avgProcessTime,
            };
            
            this.state.quickStats = {
                draft: draftRecords.length,
                first: firstRecords.length,
                second: secondRecords.length,
            };
        } catch (error) {
            console.error("Error loading analytics:", error);
        }
    }
    
    async loadRecentActivity() {
        try {
            const recentWeighings = await this.orm.searchRead(
                "truck.weighing",
                [],
                ["name", "truck_plate", "state", "write_date", "net_weight", "partner_id", "operation_type"],
                { limit: 8, order: "write_date desc" }
            );
            this.state.recentActivity = recentWeighings;
        } catch (error) {
            console.error("Error loading recent activity:", error);
        }
    }
    
    getActivityColor(state) {
        const colors = {
            draft: '#6c757d',
            first: '#17a2b8',
            second: '#ffc107',
            done: '#28a745'
        };
        return colors[state] || '#6c757d';
    }

    async refreshData() {
        this.state.loading = true;
        try {
            await this.loadPendingPickings();
            await this.loadWeighings();
            await this.loadAnalytics();
            await this.loadRecentActivity();
            this.checkUrgentOrders();
            this.state.lastRefresh = new Date();
        } finally {
            this.state.loading = false;
        }
    }
    
    getActivityIcon(state) {
        const icons = {
            draft: 'fa-clock',
            first: 'fa-weight',
            second: 'fa-balance-scale',
            done: 'fa-check-circle'
        };
        return icons[state] || 'fa-circle';
    }
    
    getActivityTime(writeDate) {
        const now = Date.now();
        const activityTime = new Date(writeDate + ' UTC').getTime();
        const diffMinutes = Math.floor((now - activityTime) / 60000);
        if (diffMinutes < 1) return 'Just now';
        if (diffMinutes < 60) return `${diffMinutes}m ago`;
        const hours = Math.floor(diffMinutes / 60);
        if (hours < 24) return `${hours}h ago`;
        return `${Math.floor(hours / 24)}d ago`;
    }
    
    getLastRefreshTime() {
        const now = new Date();
        const diff = Math.floor((now - this.state.lastRefresh) / 1000);
        if (diff < 60) return `${diff}s ago`;
        const mins = Math.floor(diff / 60);
        if (mins < 60) return `${mins}m ago`;
        const hours = Math.floor(mins / 60);
        return `${hours}h ago`;
    }
    
    selectWeighing(weighingId) {
        this.state.selectedWeighing = weighingId;
    }
    
    async handleKeyPress(ev) {
        if (ev.target.tagName === 'INPUT') return;
        
        switch(ev.key) {
            case 'F1':
                ev.preventDefault();
                await this.createNewWeighing();
                break;
            case 'F2':
                ev.preventDefault();
                await this.refreshData();
                this.notification.add('Data refreshed', { type: 'success' });
                break;
            case 'F3':
                ev.preventDefault();
                this.openWeighingList('in_progress');
                break;
            case 'F4':
                ev.preventDefault();
                this.openWeighingList('done');
                break;
        }
    }
    
    checkUrgentOrders() {
        const urgentPickings = this.state.pickings.filter(p => {
            if (!p.scheduled_date) return false;
            const scheduled = new Date(p.scheduled_date);
            const now = new Date();
            return scheduled <= now;
        });
        if (urgentPickings.length > 0) {
            this.notification.add(`${urgentPickings.length} urgent orders waiting!`, { type: 'warning' });
        }
    }
    
    getWorkflowProgress(state) {
        const steps = { draft: 25, first: 50, second: 75, done: 100 };
        return steps[state] || 0;
    }
    
    getWorkflowColor(state) {
        const colors = { draft: '#6c757d', first: '#17a2b8', second: '#ffc107', done: '#28a745' };
        return colors[state] || '#6c757d';
    }
    
    openWeighingList(filter) {
        let domain = [];
        let name = "Weighings";
        
        if (filter === "in_progress") {
            domain = [["state", "in", ["draft", "first", "second"]]];
            name = "In Progress Weighings";
        } else if (filter === "draft") {
            domain = [["state", "=", "draft"]];
            name = "Draft Weighings";
        } else if (filter === "done") {
            domain = [["state", "=", "done"]];
            name = "Done Weighings";
        }
        
        this.action.doAction({
            type: "ir.actions.act_window",
            name: name,
            res_model: "truck.weighing",
            views: [[false, "kanban"], [false, "list"], [false, "form"]],
            view_mode: "kanban,list,form",
            domain: domain,
            target: "current",
        });
    }
}

WeighingWeighPointInterface.template = "inventory_scale_integration_weighpoint.WeighPointInterface";

registry.category("actions").add("weighing_weighpoint_interface", WeighingWeighPointInterface);
