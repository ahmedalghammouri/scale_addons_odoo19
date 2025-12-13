{
    'name': 'Weigh Point',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Stock',
    'summary': 'Weigh Point Interface - Quick Weighing Operations',
    'description': '''
Weigh Point Interface
=====================
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
    'depends': ['inventory_scale_integration_base','stock'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/truck_selection_wizard_views.xml',
        'views/weighing_weighpoint_views.xml',
        'views/menu_items_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'inventory_scale_integration_weighpoint/static/src/js/weighing_weighpoint.js',
            'inventory_scale_integration_weighpoint/static/src/xml/weighing_weighpoint.xml',
            'inventory_scale_integration_weighpoint/static/src/scss/weighing_weighpoint.scss',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
