{
    'name': 'Scale Integration - Sale',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Stock',
    'summary': 'Weighbridge integration for sale operations',
    'author': 'Gemy',
    'website': 'https://www.example.com',
    'license': 'LGPL-3',
    'depends': ['inventory_scale_integration_base', 'inventory_scale_integration_stock', 'sale'],
    'data': [
        'report/truck_weighing_reports.xml',
        'views/truck_weighing_views.xml',
        'views/sale_order_views.xml',
        'views/menu_items_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'inventory_scale_integration_sale/static/src/js/weighing_dashboard_sale.js',
            'inventory_scale_integration_sale/static/src/xml/weighing_dashboard_sale.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
