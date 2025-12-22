# Complete Module Split Instructions

## Overview
Split `inventory_scale_integration` into 4 modular components without field duplication.

## Module Dependencies Tree
```
inventory_scale_integration_base (mail, web)
    ├── inventory_scale_integration_stock (base, stock)
    │   ├── inventory_scale_integration_purchase (base, stock_module, purchase)
    │   └── inventory_scale_integration_sale (base, stock_module, sale)
```

## Detailed File Distribution

### BASE MODULE (inventory_scale_integration_base)
**Models:**
- `weighing_scale.py` - Complete scale model (with weighing_count)
- `truck_fleet.py` - Complete truck model (with weighing_count, last_weighing_date)
- `truck_type.py` - Complete truck type model
- `res_users.py` - Scale assignment fields
- `product_template.py` - is_weighable field
- `truck_weighing.py` - Base weighing model (NO PO/SO fields, NO stock-specific methods)
  - Keep: scale_id, truck_id, partner_id, product_id, operation_type
  - Keep: weights, states, basic CRUD
  - REMOVE: picking_id, delivery_id, stock methods
  - REMOVE: All PO/SO fields and methods

**Views:**
- `weighing_scale_views.xml` - Scale CRUD (with weighing button)
- `truck_fleet_views.xml` - Truck CRUD (with weighing button)
- `truck_weighing_views.xml` - Basic weighing CRUD (NO stock/PO/SO fields)
- `res_users_views.xml` - User scale tab
- `product_views.xml` - Weighable product flag
- `menu_items_views.xml` - Base menus + weighing records menu

**Security:**
- Groups: group_scale_user, group_scale_manager
- Access: truck.fleet, truck.type, weighing.scale, truck.weighing

**Data:**
- Sequence: truck.weighing.sequence

---

### STOCK MODULE (inventory_scale_integration_stock)
**Models:**
- `truck_weighing.py` - Extend base weighing with stock operations
  - Add: picking_id, delivery_id, location_dest_id
  - Add: _update_receipt_quantity(), _update_delivery_quantity()
  - Add: action_update_inventory()
  - Add: _onchange_picking_id(), _onchange_delivery_id()

- `stock_picking.py` - Inherit stock.picking
  ```python
  weighing_count = fields.Integer(compute='_compute_weighing_count')
  has_weighable_products = fields.Boolean(compute='_compute_has_weighable_products')
  total_net_weight = fields.Float(compute='_compute_weighing_data')
  total_net_weight_display = fields.Char(compute='_compute_weighing_data')
  
  def action_view_weighing_records(self)
  ```

- `weighing_overview.py` - Dashboard data model

**Views:**
- `truck_weighing_views.xml` - Extend base weighing views (add stock fields/buttons)
- `stock_picking_views.xml` - Picking weighing button
- `weighing_overview_views.xml` - Dashboard action
- `menu_items_views.xml` - Operations, Overview, Reports menus

**Controllers:**
- `scale_controller.py` - Weight API endpoint
- `weighing_dashboard.py` - Dashboard controller

**Assets:**
- `weighing_dashboard.js`
- `weighing_dashboard.xml`
- `weighing_dashboard.scss`

**Security:**
- Access: weighing.overview

---

### PURCHASE MODULE (inventory_scale_integration_purchase)
**Models:**
- `truck_weighing.py` - Extend stock weighing
  ```python
  purchase_order_id = fields.Many2one('purchase.order')
  purchase_line_id = fields.Many2one('purchase.order.line')
  
  @api.onchange('purchase_order_id')
  @api.onchange('purchase_line_id')
  def _create_draft_receipt_from_po(self)
  def action_view_purchase_order(self)
  
  # Extend _auto_populate_from_context
  # Extend _compute_operation_type
  # Extend _onchange_picking_id
  ```

- `purchase_order.py` - Inherit purchase.order
  ```python
  weighing_count = fields.Integer(compute='_compute_weighing_data')
  total_net_weight = fields.Float(compute='_compute_weighing_data')
  total_net_weight_display = fields.Char(compute='_compute_weighing_data')
  has_weighable_products = fields.Boolean(compute='_compute_has_weighable_products')
  
  def action_view_weighing_records(self)
  ```

- `purchase_order_line.py` - Inherit purchase.order.line
  ```python
  weighing_ids = fields.One2many('truck.weighing', 'purchase_line_id')
  total_received_weight = fields.Float(compute='_compute_total_received_weight')
  ```

**Views:**
- `truck_weighing_views.xml` - Add PO fields/buttons (inherit stock views)
- `purchase_order_views.xml` - PO weighing button
- `menu_items_views.xml` - POs to Weigh menu

---

### SALE MODULE (inventory_scale_integration_sale)
**Models:**
- `truck_weighing.py` - Extend stock weighing
  ```python
  sale_order_id = fields.Many2one('sale.order')
  sale_line_id = fields.Many2one('sale.order.line')
  
  @api.onchange('sale_order_id')
  @api.onchange('sale_line_id')
  def _create_draft_delivery_from_so(self)
  def action_view_sale_order(self)
  
  # Extend _auto_populate_from_context
  # Extend _compute_operation_type
  # Extend _onchange_picking_id
  ```

- `sale_order.py` - Inherit sale.order
  ```python
  weighing_count = fields.Integer(compute='_compute_weighing_data')
  total_net_weight = fields.Float(compute='_compute_weighing_data')
  total_net_weight_display = fields.Char(compute='_compute_weighing_data')
  has_weighable_products = fields.Boolean(compute='_compute_has_weighable_products')
  
  def action_view_weighing_records(self)
  ```

- `sale_order_line.py` - Inherit sale.order.line
  ```python
  weighing_ids = fields.One2many('truck.weighing', 'sale_line_id')
  total_delivered_weight = fields.Float(compute='_compute_total_delivered_weight')
  ```

**Views:**
- `truck_weighing_views.xml` - Add SO fields/buttons (inherit stock views)
- `sale_order_views.xml` - SO weighing button
- `menu_items_views.xml` - Sales/Deliveries to Weigh menus

---

## Critical Rules

1. **NO DUPLICATE FIELDS**: Each field defined ONCE in appropriate module
2. **PROPER INHERITANCE**: Use `_inherit` to extend models from other modules
3. **VIEW INHERITANCE**: Use xpath to add fields/buttons to existing views
4. **CLEAN DEPENDENCIES**: Only depend on what you actually use
5. **OPTIONAL MODULES**: Purchase/Sale modules are optional add-ons

## Installation Scenarios

| Scenario | Modules | Result |
|----------|---------|--------|
| Basic | base only | Basic weighing records (no stock integration) |
| + Stock | base + stock | Weighing with stock operations |
| + Purchase | base + stock + purchase | Add PO integration |
| + Sales | base + stock + sale | Add SO integration |
| Full | base + stock + purchase + sale | Complete original functionality |

## Testing Matrix

- [ ] Base alone: Scales, trucks, products, basic weighing work
- [ ] Base + Stock: Stock integration works, no PO/SO fields
- [ ] + Purchase: PO fields appear, PO integration works
- [ ] + Sale: SO fields appear, SO integration works
- [ ] All together: Identical to original module
- [ ] No duplicate fields in database
- [ ] No missing functionality
- [ ] All menus accessible
- [ ] Dashboard works correctly
