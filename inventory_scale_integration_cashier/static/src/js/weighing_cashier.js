/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart, onMounted, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class WeighingCashierInterface extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        
        this.state = useState({
            barcode: "",
            pickings: [],
            pickingsWithWeighing: [],
            recentWeighings: [],
            scaleWeight: 0,
            pickingFilter: "all",
            searchText: "",
        });

        this.refreshInterval = null;

        onWillStart(async () => {
            await this.loadPendingPickings();
            await this.loadWeighings();
        });

        onMounted(() => {
            this.refreshInterval = setInterval(() => {
                this.refreshData();
            }, 60000); // 60000ms = 1 minute
        });

        onWillUnmount(() => {
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
            }
        });
    }

    async loadPendingPickings() {
        let domain = [["state", "in", ["assigned", "confirmed"]]];
        
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
        
        // Get all weighing records for these pickings
        const weighings = await this.orm.searchRead(
            "truck.weighing",
            [["state", "!=", "done"]],
            ["picking_id", "delivery_id"],
            { limit: 100 }
        );
        
        const pickingIdsWithWeighing = new Set();
        weighings.forEach(w => {
            if (w.picking_id) pickingIdsWithWeighing.add(w.picking_id[0]);
            if (w.delivery_id) pickingIdsWithWeighing.add(w.delivery_id[0]);
        });
        
        this.state.pickings = allPickings.filter(p => !pickingIdsWithWeighing.has(p.id));
        this.state.pickingsWithWeighing = allPickings.filter(p => pickingIdsWithWeighing.has(p.id));
    }

    async loadWeighings() {
        let domain = [["state", "in", ["draft", "first", "second"]]];
        
        if (this.state.searchText) {
            domain.push(["name", "ilike", this.state.searchText]);
        }
        
        this.state.recentWeighings = await this.orm.searchRead(
            "truck.weighing",
            domain,
            ["name", "truck_plate", "state", "operation_type", "barcode", "partner_id", "product_id", "net_weight", "gross_weight", "tare_weight"],
            { limit: 30, order: "create_date desc" }
        );
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
    
    async refreshData() {
        await this.loadPendingPickings();
        await this.loadWeighings();
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

WeighingCashierInterface.template = "inventory_scale_integration_cashier.CashierInterface";

registry.category("actions").add("weighing_cashier_interface", WeighingCashierInterface);
