{
    'name': 'Weighing Cashier',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Stock',
    'summary': 'Weighbridge Cashier Interface - Quick Weighing Operations',
    'description': '''
Weighbridge Cashier Interface
==============================
Simplified interface for weighbridge operators:
* Barcode scanning for quick access
* Large buttons and displays
* Pending orders management
* Real-time weight capture
* Session management
    ''',
    'author': 'Gemy',
    'website': 'https://www.example.com',
    'license': 'LGPL-3',
    'depends': ['inventory_scale_integration_base', 'inventory_scale_integration_stock'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/truck_selection_wizard_views.xml',
        'views/weighing_cashier_views.xml',
        'views/menu_items_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'inventory_scale_integration_cashier/static/src/js/weighing_cashier.js',
            'inventory_scale_integration_cashier/static/src/xml/weighing_cashier.xml',
            'inventory_scale_integration_cashier/static/src/scss/weighing_cashier.scss',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
