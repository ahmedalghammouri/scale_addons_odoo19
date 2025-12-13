{
    'name': 'Scale Integration - Stock Outgoing',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Stock',
    'summary': 'Weighbridge integration for outgoing stock operations (deliveries)',
    'author': 'Gemy',
    'website': 'https://www.example.com',
    'license': 'LGPL-3',
    'depends': ['inventory_scale_integration_base', 'inventory_scale_integration_dashboard', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'report/truck_weighing_reports.xml',
        'views/truck_weighing_views.xml',
        'views/stock_picking_views.xml',
        'views/weighing_overview_views.xml',
        'views/menu_items_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # 'inventory_scale_integration_stock_out/static/src/js/weighing_dashboard.js',
            # 'inventory_scale_integration_stock_out/static/src/xml/weighing_dashboard.xml',
            # 'inventory_scale_integration_stock_out/static/src/scss/weighing_dashboard.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
