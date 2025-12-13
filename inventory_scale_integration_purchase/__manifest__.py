{
    'name': 'Scale Integration - Purchase',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Stock',
    'summary': 'Weighbridge integration for purchase operations',
    'author': 'Gemy',
    'website': 'https://www.example.com',
    'license': 'LGPL-3',
    'depends': ['inventory_scale_integration_base', 'inventory_scale_integration_stock_in', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'report/truck_weighing_reports.xml',
        'views/truck_weighing_views.xml',
        'views/purchase_order_views.xml',
        'views/menu_items_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'inventory_scale_integration_purchase/static/src/js/weighing_dashboard_purchase.js',
            'inventory_scale_integration_purchase/static/src/xml/weighing_dashboard_purchase.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
