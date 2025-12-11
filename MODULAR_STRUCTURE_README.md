# Inventory Scale Integration - Modular Structure

## Overview
The inventory scale integration has been split into 3 modular components for maximum flexibility:

## 1. Base Module: `inventory_scale_integration_base`
**Purpose**: Core weighing scale functionality with stock operations only

### Features:
- ✅ Weighing scale configuration and monitoring
- ✅ Truck fleet management
- ✅ Core weighing operations (Gross/Tare/Net)
- ✅ Stock picking integration
- ✅ User scale assignment
- ✅ Product weighable configuration
- ✅ Basic dashboard (receipts, in-progress, all records)
- ✅ Scale controller API
- ✅ Security groups and access rights

### Dependencies:
- `stock`, `mail`, `web`

### Key Models:
- `weighing.scale` - Scale configuration
- `truck.weighing` - Core weighing records
- `truck.fleet` - Truck management
- `weighing.overview` - Dashboard data (core only)

## 2. Purchase Extension: `inventory_scale_integration_purchase`
**Purpose**: Adds Purchase Order integration

### Features:
- ✅ Purchase Order weighing integration
- ✅ PO dashboard cards
- ✅ Receipt weighing workflows
- ✅ Auto-creation of receipts from POs
- ✅ Purchase line tracking

### Dependencies:
- `inventory_scale_integration_base`, `purchase`
- **Auto-install**: True (installs automatically when both base and purchase are available)

### Extended Models:
- `truck.weighing` - Adds PO fields and methods
- `purchase.order` - Adds weighing statistics
- `weighing.overview` - Adds PO dashboard data

### New Fields Added:
- `purchase_order_id` - Link to purchase order
- `purchase_line_id` - Link to purchase order line

## 3. Sales Extension: `inventory_scale_integration_sale`
**Purpose**: Adds Sales Order integration

### Features:
- ✅ Sales Order weighing integration
- ✅ SO dashboard cards
- ✅ Delivery weighing workflows
- ✅ Auto-creation of deliveries from SOs
- ✅ Sales line tracking

### Dependencies:
- `inventory_scale_integration_base`, `sale`
- **Auto-install**: True (installs automatically when both base and sale are available)

### Extended Models:
- `truck.weighing` - Adds SO fields and methods
- `sale.order` - Adds weighing statistics
- `weighing.overview` - Adds SO dashboard data

### New Fields Added:
- `sale_order_id` - Link to sale order
- `sale_line_id` - Link to sale order line
- `delivery_id` - Link to delivery picking

## Installation Scenarios

### Scenario 1: Stock Only
**Install**: `inventory_scale_integration_base`
**Features**: Core weighing with stock operations only
**Dashboard**: Receipts, In Progress, All Records, Truck Management

### Scenario 2: Stock + Purchase
**Install**: `inventory_scale_integration_base` + `purchase` module
**Auto-installs**: `inventory_scale_integration_purchase`
**Features**: Core + Purchase Order integration
**Dashboard**: + POs to Weigh card

### Scenario 3: Stock + Sales
**Install**: `inventory_scale_integration_base` + `sale` module
**Auto-installs**: `inventory_scale_integration_sale`
**Features**: Core + Sales Order integration
**Dashboard**: + Sales to Weigh, Deliveries to Weigh cards

### Scenario 4: Full Integration
**Install**: `inventory_scale_integration_base` + `purchase` + `sale` modules
**Auto-installs**: Both extensions
**Features**: Complete functionality
**Dashboard**: All cards available

## Menu Structure

### Base Module Menus:
```
Weighbridge
├── Overview (Dashboard)
├── Operations
│   ├── Receipts to Weigh
│   ├── In Progress
│   └── All Records
├── Truck Fleet
├── Reports
│   └── Weighing Analysis
└── Configuration
    ├── Truck Types
    ├── Weighing Scales
    └── Weighable Products
```

### Purchase Extension Adds:
```
Operations
├── POs to Weigh  [NEW]
```

### Sales Extension Adds:
```
Operations
├── Sales to Weigh     [NEW]
├── Deliveries to Weigh [NEW]
```

## Technical Implementation

### Field Extension Pattern:
```python
# In extension modules
class TruckWeighing(models.Model):
    _inherit = 'truck.weighing'
    
    purchase_order_id = fields.Many2one('purchase.order')
    # Extension-specific fields and methods
```

### View Inheritance Pattern:
```xml
<!-- In extension modules -->
<record id="truck_weighing_view_form_purchase" model="ir.ui.view">
    <field name="inherit_id" ref="inventory_scale_integration_base.truck_weighing_view_form"/>
    <!-- Extension-specific view modifications -->
</record>
```

### Dashboard Extension Pattern:
```python
# In extension modules
class WeighingOverview(models.TransientModel):
    _inherit = 'weighing.overview'
    
    @api.model
    def get_overview_data(self):
        data = super().get_overview_data()
        # Add extension-specific data
        return data
```

## Migration from Original Module

### Step 1: Backup
- Backup existing `inventory_scale_integration` module
- Export current data if needed

### Step 2: Install Base Module
- Install `inventory_scale_integration_base`
- Test core functionality

### Step 3: Install Extensions
- Install `purchase` module (if needed) → auto-installs purchase extension
- Install `sale` module (if needed) → auto-installs sales extension

### Step 4: Verify
- Test all combinations work correctly
- Verify data integrity
- Check dashboard functionality

## Benefits

✅ **Modular**: Clear separation of concerns
✅ **Flexible**: Install only what you need
✅ **Maintainable**: Changes isolated to specific areas
✅ **Extensible**: Easy to add new integrations
✅ **Auto-install**: Extensions install automatically
✅ **No functionality loss**: All original features preserved
✅ **Performance**: Lighter installations for specific needs

## File Structure

```
inventory_scale_integration_base/
├── __manifest__.py
├── __init__.py
├── models/
│   ├── weighing_scale.py
│   ├── truck_weighing.py (core only)
│   ├── truck_fleet.py
│   ├── res_users.py
│   ├── product_product.py
│   ├── stock_picking.py
│   └── weighing_overview.py (core only)
├── views/ (core views)
├── controllers/
├── security/
└── static/

inventory_scale_integration_purchase/
├── __manifest__.py (auto_install: True)
├── __init__.py
├── models/
│   ├── truck_weighing.py (PO extensions)
│   ├── purchase_order.py
│   └── weighing_overview.py (PO data)
└── views/ (PO-specific views)

inventory_scale_integration_sale/
├── __manifest__.py (auto_install: True)
├── __init__.py
├── models/
│   ├── truck_weighing.py (SO extensions)
│   ├── sale_order.py
│   └── weighing_overview.py (SO data)
└── views/ (SO-specific views)
```

This modular approach ensures maximum flexibility while maintaining all existing functionality and allowing clients to use only the modules they need.