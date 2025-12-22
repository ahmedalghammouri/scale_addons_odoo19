# Module Split Guide - Inventory Scale Integration

## Module Structure

### 1. inventory_scale_integration_base (Core Module)
**Dependencies:** mail, web
**Contains:**
- Models: weighing.scale, truck.fleet, truck.type, res.users (inherit), product.template (inherit)
- Views: Scale configuration, Truck fleet, User settings, Product weighable flag
- Security groups and access rights
- Base menu structure

### 2. inventory_scale_integration_stock (Stock Operations)
**Dependencies:** inventory_scale_integration_base, stock
**Contains:**
- Models: truck.weighing, stock.picking (inherit), weighing.overview
- Views: Weighing records, Stock picking integration, Dashboard
- Controllers: weighing_dashboard, scale_controller
- Assets: Dashboard JS/XML/SCSS
- Menu: Operations, Overview, Reports

### 3. inventory_scale_integration_purchase (Purchase Operations)
**Dependencies:** inventory_scale_integration_base, inventory_scale_integration_stock, purchase
**Contains:**
- Models: purchase.order (inherit), purchase.order.line (inherit)
- Views: Purchase order integration
- Menu: POs to Weigh

### 4. inventory_scale_integration_sale (Sales Operations)
**Dependencies:** inventory_scale_integration_base, inventory_scale_integration_stock, sale
**Contains:**
- Models: sale.order (inherit), sale.order.line (inherit)
- Views: Sale order integration
- Menu: Sales to Weigh, Deliveries to Weigh

## Key Principles

1. **No Field Duplication:** Each field defined only once in appropriate module
2. **Clean Dependencies:** Each module depends only on what it needs
3. **Modular Installation:** Can install base + any combination of stock/purchase/sale
4. **Full Compatibility:** Installing all 4 modules = original module functionality

## File Distribution

### Base Module Files:
- weighing_scale.py (complete)
- truck_fleet.py (base fields only)
- res_users.py (scale assignment)
- product_template.py (is_weighable field)

### Stock Module Files:
- truck_weighing.py (core weighing logic)
- stock_picking.py (inherit for weighing integration)
- weighing_overview.py (dashboard data)
- weighing_scale.py (add weighing_count computed field)
- truck_fleet.py (add weighing_count, last_weighing_date)
- Controllers: scale_controller.py, weighing_dashboard.py
- Assets: Dashboard UI components

### Purchase Module Files:
- purchase_order.py (weighing integration)
- purchase_order_line.py (weighing tracking)
- Views: Purchase order buttons and stats

### Sale Module Files:
- sale_order.py (weighing integration)
- sale_order_line.py (weighing tracking)
- Views: Sale order buttons and stats

## Migration Steps

1. Install inventory_scale_integration_base
2. Install inventory_scale_integration_stock
3. Install inventory_scale_integration_purchase (if needed)
4. Install inventory_scale_integration_sale (if needed)
5. Uninstall original inventory_scale_integration

## Testing Checklist

- [ ] Scale configuration works
- [ ] Truck fleet management works
- [ ] User scale assignment works
- [ ] Product weighable flag works
- [ ] Weighing records creation works
- [ ] Stock picking integration works
- [ ] Purchase order integration works (if installed)
- [ ] Sale order integration works (if installed)
- [ ] Dashboard displays correctly
- [ ] No duplicate fields
- [ ] No missing functionality
- [ ] All menus accessible
- [ ] Security groups work correctly
