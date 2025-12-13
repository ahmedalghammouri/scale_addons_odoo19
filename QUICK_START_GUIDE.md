# Quick Start Guide - Split Modules

## What Changed?

The single `inventory_scale_integration_stock` module is now split into:

1. **`inventory_scale_integration_stock_in`** → For Receipts (Incoming)
2. **`inventory_scale_integration_stock_out`** → For Deliveries (Outgoing)

## Quick Installation

### Install Both (Recommended)
```bash
odoo-bin -d your_db -i inventory_scale_integration_stock_in,inventory_scale_integration_stock_out
```

### Install Only Incoming
```bash
odoo-bin -d your_db -i inventory_scale_integration_stock_in
```

### Install Only Outgoing
```bash
odoo-bin -d your_db -i inventory_scale_integration_stock_out
```

## Quick Comparison

| Feature | Incoming Module | Outgoing Module |
|---------|----------------|-----------------|
| **Field** | `picking_id` (Receipt) | `delivery_id` (Delivery) |
| **Operation Type** | `incoming` | `outgoing` |
| **Picking Type** | Receipts | Deliveries |
| **Menu** | "Incoming Weighing" | "Outgoing Weighing" |
| **Dashboard Model** | `weighing.overview.incoming` | `weighing.overview.outgoing` |
| **Update Method** | `_update_receipt_quantity()` | `_update_delivery_quantity()` |

## Quick Test

### Test Incoming Module
1. Go to Inventory → Receipts
2. Create a receipt with weighable product
3. Click "Weighing" button
4. Create weighing record
5. Record weights and update inventory

### Test Outgoing Module
1. Go to Inventory → Deliveries
2. Create a delivery with weighable product
3. Click "Weighing" button
4. Create weighing record
5. Record weights and update inventory

## No Conflicts

✅ Both modules can be installed together
✅ No field conflicts (different fields)
✅ No view conflicts (unique IDs)
✅ No menu conflicts (separate submenus)
✅ Works with all other scale modules

## Key Benefits

- 🎯 **Focused**: Each module does one thing well
- 🔧 **Flexible**: Install only what you need
- 🚀 **Performance**: Less code, faster execution
- 📦 **Maintainable**: Easier to update and debug
- 🔒 **Safe**: No conflicts with existing modules

## Need Help?

See `MODULE_SPLIT_IMPLEMENTATION.md` for detailed documentation.
