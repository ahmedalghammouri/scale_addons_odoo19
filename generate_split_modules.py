#!/usr/bin/env python3
"""
Script to generate split modules from inventory_scale_integration
Run this script to create all 4 modules with proper structure
"""

import os
import shutil

# Base paths
BASE_PATH = r"c:\Users\ODOO\Documents\ODOO 19\odoo\scale_addons"
SOURCE_MODULE = os.path.join(BASE_PATH, "inventory_scale_integration")

# Module definitions
MODULES = {
    'base': 'inventory_scale_integration_base',
    'stock': 'inventory_scale_integration_stock',
    'purchase': 'inventory_scale_integration_purchase',
    'sale': 'inventory_scale_integration_sale',
}

def create_module_structure(module_name):
    """Create basic module directory structure"""
    module_path = os.path.join(BASE_PATH, module_name)
    
    dirs = [
        'models',
        'views',
        'security',
        'controllers',
        'static/src/js',
        'static/src/xml',
        'static/src/scss',
        'static/description',
    ]
    
    for dir_name in dirs:
        os.makedirs(os.path.join(module_path, dir_name), exist_ok=True)
    
    print(f"✓ Created structure for {module_name}")

def copy_icon():
    """Copy icon to all modules"""
    source_icon = os.path.join(SOURCE_MODULE, 'static/description/icon.svg')
    if os.path.exists(source_icon):
        for module in MODULES.values():
            dest = os.path.join(BASE_PATH, module, 'static/description/icon.svg')
            shutil.copy2(source_icon, dest)
            print(f"✓ Copied icon to {module}")

def main():
    print("=" * 60)
    print("INVENTORY SCALE INTEGRATION - MODULE SPLIT GENERATOR")
    print("=" * 60)
    print()
    
    # Create all module structures
    for module in MODULES.values():
        create_module_structure(module)
    
    print()
    copy_icon()
    
    print()
    print("=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("1. Review the generated module structures")
    print("2. Copy model files according to SPLIT_INSTRUCTIONS.md")
    print("3. Copy view files according to SPLIT_INSTRUCTIONS.md")
    print("4. Copy controller files to stock module")
    print("5. Copy assets to stock module")
    print("6. Update security files")
    print("7. Test each module independently")
    print("8. Test all modules together")
    print()
    print("See MODULE_SPLIT_GUIDE.md and SPLIT_INSTRUCTIONS.md for details")
    print("=" * 60)

if __name__ == '__main__':
    main()
