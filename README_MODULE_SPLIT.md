# Inventory Scale Integration - Module Split Implementation

## Summary

The original `inventory_scale_integration` module has been split into 4 modular components:

1. **inventory_scale_integration_base** - Core functionality (scales, trucks, products)
2. **inventory_scale_integration_stock** - Stock operations and weighing records
3. **inventory_scale_integration_purchase** - Purchase order integration (optional)
4. **inventory_scale_integration_sale** - Sales order integration (optional)

## Quick Start

### Option 1: Use Pre-Created Base Module
The base module structure has been created in `inventory_scale_integration_base/` with:
- ✅ Complete models (weighing_scale, truck_fleet, truck_type, res_users, product_template)
- ✅ All views
- ✅ Security configuration
- ✅ Menu structure

### Option 2: Complete Manual Split

Follow the detailed instructions in `SPLIT_INSTRUCTIONS.md`

## Installation Order

```bash
# 1. Install base module (required)
odoo-bin -d your_database -i inventory_scale_integration_base

# 2. Install stock module (required for weighing)
odoo-bin -d your_database -i inventory_scale_integration_stock

# 3. Install purchase module (optional)
odoo-bin -d your_database -i inventory_scale_integration_purchase

# 4. Install sale module (optional)
odoo-bin -d your_database -i inventory_scale_integration_sale
```

## Module Comparison

| Feature | Base | Stock | Purchase | Sale |
|---------|------|-------|----------|------|
| Scale Configuration | ✅ | | | |
| Truck Fleet | ✅ | | | |
| Weighable Products | ✅ | | | |
| Weighing Records | | ✅ | | |
| Stock Integration | | ✅ | | |
| Dashboard | | ✅ | | |
| PO Integration | | | ✅ | |
| SO Integration | | | | ✅ |

## File Distribution Summary

### Base Module (19 files)
```
inventory_scale_integration_base/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── weighing_scale.py (complete, no weighing_count)
│   ├── truck_fleet.py (base only, no weighing fields)
│   ├── res_users.py
│   └── product_template.py
├── views/
│   ├── weighing_scale_views.xml
│   ├── truck_fleet_views.xml
│   ├── res_users_views.xml
│   ├── product_views.xml
│   └── menu_items_views.xml
├── security/
│   ├── security.xml
│   └── ir.model.access.csv
└── static/description/icon.svg
```

### Stock Module (25+ files)
```
inventory_scale_integration_stock/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── truck_weighing.py (core, no PO/SO fields)
│   ├── stock_picking.py
│   ├── weighing_scale.py (extend with weighing_count)
│   ├── truck_fleet.py (extend with weighing fields)
│   └── weighing_overview.py
├── views/
│   ├── truck_weighing_views.xml (no PO/SO fields)
│   ├── stock_picking_views.xml
│   ├── weighing_overview_views.xml
│   └── menu_items_views.xml
├── controllers/
│   ├── __init__.py
│   ├── scale_controller.py
│   └── weighing_dashboard.py
├── static/src/
│   ├── js/weighing_dashboard.js
│   ├── xml/weighing_dashboard.xml
│   └── scss/weighing_dashboard.scss
└── security/ir.model.access.csv
```

### Purchase Module (8 files)
```
inventory_scale_integration_purchase/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── truck_weighing.py (extend with PO fields)
│   ├── purchase_order.py
│   └── purchase_order_line.py
├── views/
│   ├── truck_weighing_views.xml (inherit, add PO fields)
│   ├── purchase_order_views.xml
│   └── menu_items_views.xml
└── security/ir.model.access.csv
```

### Sale Module (8 files)
```
inventory_scale_integration_sale/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── truck_weighing.py (extend with SO fields)
│   ├── sale_order.py
│   └── sale_order_line.py
├── views/
│   ├── truck_weighing_views.xml (inherit, add SO fields)
│   ├── sale_order_views.xml
│   └── menu_items_views.xml
└── security/ir.model.access.csv
```

## Key Implementation Details

### 1. No Field Duplication
Each field is defined exactly once:
- `is_weighable` → base module (product_template.py)
- `weighing_count` on weighing.scale → stock module
- `weighing_count` on truck.fleet → stock module
- `purchase_order_id` → purchase module
- `sale_order_id` → sale module

### 2. Proper Model Inheritance
```python
# In stock module
class TruckWeighing(models.Model):
    _name = 'truck.weighing'
    # Define core fields

# In purchase module
class TruckWeighing(models.Model):
    _inherit = 'truck.weighing'
    purchase_order_id = fields.Many2one('purchase.order')
    # Add PO-specific methods

# In sale module
class TruckWeighing(models.Model):
    _inherit = 'truck.weighing'
    sale_order_id = fields.Many2one('sale.order')
    # Add SO-specific methods
```

### 3. View Inheritance
```xml
<!-- In stock module -->
<record id="truck_weighing_view_form" model="ir.ui.view">
    <field name="model">truck.weighing</field>
    <!-- Define base form -->
</record>

<!-- In purchase module -->
<record id="truck_weighing_view_form_purchase" model="ir.ui.view">
    <field name="inherit_id" ref="inventory_scale_integration_stock.truck_weighing_view_form"/>
    <xpath expr="//group[@name='partner_operation']" position="after">
        <!-- Add PO fields -->
    </xpath>
</record>
```

## Migration from Original Module

### Step 1: Backup
```bash
# Backup your database
pg_dump your_database > backup_before_split.sql
```

### Step 2: Install New Modules
```bash
# Install in order
odoo-bin -d your_database -i inventory_scale_integration_base
odoo-bin -d your_database -i inventory_scale_integration_stock
odoo-bin -d your_database -i inventory_scale_integration_purchase
odoo-bin -d your_database -i inventory_scale_integration_sale
```

### Step 3: Verify
- Check all menus are accessible
- Test scale configuration
- Test weighing record creation
- Test PO integration
- Test SO integration
- Verify dashboard displays correctly

### Step 4: Uninstall Original
```bash
odoo-bin -d your_database -u inventory_scale_integration
```

## Testing Checklist

### Base Module Tests
- [ ] Can create/edit scales
- [ ] Can test scale connection
- [ ] Can create/edit trucks
- [ ] Can assign scales to users
- [ ] Can mark products as weighable
- [ ] Menus appear correctly

### Stock Module Tests
- [ ] Can create weighing records
- [ ] Can fetch live weight
- [ ] Can set gross/tare weights
- [ ] Can update inventory
- [ ] Stock picking integration works
- [ ] Dashboard displays correctly
- [ ] Scale weighing_count computed correctly
- [ ] Truck weighing_count computed correctly

### Purchase Module Tests
- [ ] PO fields appear in weighing form
- [ ] Can select PO in weighing record
- [ ] PO weighing button appears
- [ ] PO weighing count correct
- [ ] PO total weight correct
- [ ] "POs to Weigh" menu works

### Sale Module Tests
- [ ] SO fields appear in weighing form
- [ ] Can select SO in weighing record
- [ ] SO weighing button appears
- [ ] SO weighing count correct
- [ ] SO total weight correct
- [ ] "Sales to Weigh" menu works
- [ ] "Deliveries to Weigh" menu works

### Integration Tests
- [ ] All modules together = original functionality
- [ ] No duplicate fields in database
- [ ] No missing functionality
- [ ] No conflicts between modules
- [ ] Can install/uninstall purchase module independently
- [ ] Can install/uninstall sale module independently

## Troubleshooting

### Issue: Duplicate field error
**Solution:** Check that field is only defined once across all modules

### Issue: Missing menu items
**Solution:** Check module dependencies and menu parent IDs

### Issue: View inheritance fails
**Solution:** Verify inherit_id references correct external ID

### Issue: Computed fields not working
**Solution:** Ensure dependent module is installed

## Support

For issues or questions:
1. Check `SPLIT_INSTRUCTIONS.md` for detailed implementation
2. Review `MODULE_SPLIT_GUIDE.md` for architecture overview
3. Verify module dependencies are correct
4. Check Odoo logs for specific errors

## License

LGPL-3 (same as original module)
