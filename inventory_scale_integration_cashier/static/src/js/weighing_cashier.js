/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class WeighingCashierInterface extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        
        this.state = useState({
            barcode: "",
            pickings: [],
            recentWeighings: [],
            doneWeighings: [],
            scaleWeight: 0,
            pickingFilter: "all",
            weighingFilter: "in_progress",
            searchText: "",
        });

        onWillStart(async () => {
            await this.loadPendingPickings();
            await this.loadWeighings();
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
        
        this.state.pickings = await this.orm.searchRead(
            "stock.picking",
            domain,
            ["name", "partner_id", "scheduled_date", "picking_type_code", "origin"],
            { limit: 20, order: "scheduled_date desc" }
        );
    }

    async loadWeighings() {
        let domain = [];
        
        if (this.state.weighingFilter === "in_progress") {
            domain = [["state", "in", ["draft", "gross"]]];
        } else if (this.state.weighingFilter === "done") {
            domain = [["state", "=", "done"]];
        } else {
            domain = [["state", "in", ["draft", "gross", "tare", "done"]]];
        }
        
        if (this.state.searchText) {
            domain.push(["name", "ilike", this.state.searchText]);
        }
        
        const weighings = await this.orm.searchRead(
            "truck.weighing",
            domain,
            ["name", "truck_plate", "state", "operation_type", "barcode", "partner_id", "product_id", "net_weight", "gross_weight", "tare_weight"],
            { limit: 20, order: "create_date desc" }
        );
        
        if (this.state.weighingFilter === "in_progress") {
            this.state.recentWeighings = weighings;
            this.state.doneWeighings = [];
        } else if (this.state.weighingFilter === "done") {
            this.state.recentWeighings = [];
            this.state.doneWeighings = weighings;
        } else {
            this.state.recentWeighings = weighings.filter(w => ["draft", "gross"].includes(w.state));
            this.state.doneWeighings = weighings.filter(w => w.state === "done");
        }
    }

    async onBarcodeInput(ev) {
        if (ev.key === "Enter" && this.state.barcode) {
            await this.scanBarcode();
        }
    }

    async scanBarcode() {
        try {
            const weighing = await this.orm.call(
                "truck.weighing",
                "action_scan_barcode",
                [[], this.state.barcode]
            );
            
            if (weighing) {
                this.action.doAction({
                    type: "ir.actions.act_window",
                    res_model: "truck.weighing",
                    res_id: weighing.id,
                    views: [[false, "form"]],
                    view_mode: "form",
                    target: "current",
                });
            }
        } catch (error) {
            this.notification.add(error.message || "Barcode not found", { type: "danger" });
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
    
    async onWeighingFilterChange(filter) {
        this.state.weighingFilter = filter;
        await this.loadWeighings();
    }
    
    async onSearchChange(ev) {
        this.state.searchText = ev.target.value;
    }
    
    async onSearch() {
        await this.loadPendingPickings();
        await this.loadWeighings();
    }
}

WeighingCashierInterface.template = "inventory_scale_integration_cashier.CashierInterface";

registry.category("actions").add("weighing_cashier_interface", WeighingCashierInterface);
