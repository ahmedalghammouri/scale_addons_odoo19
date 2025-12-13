{
    'name': 'Scale Integration - Dashboard',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Stock',
    'summary': 'Base dashboard for weighbridge operations',
    'author': 'Gemy',
    'website': 'https://www.example.com',
    'license': 'LGPL-3',
    'depends': ['inventory_scale_integration_base', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        # 'report/truck_weighing_reports.xml',
        # 'views/truck_weighing_views.xml',
        # 'views/stock_picking_views.xml',
        'views/weighing_overview_views.xml',
        'views/menu_items_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'inventory_scale_integration_dashboard/static/src/js/weighing_dashboard.js',
            'inventory_scale_integration_dashboard/static/src/xml/weighing_dashboard.xml',
            # 'inventory_scale_integration_stock/static/src/css/weighing_dashboard.css',
            'inventory_scale_integration_dashboard/static/src/scss/weighing_dashboard.scss',
            # 'inventory_scale_integration_dashboard/static/src/js/weighing_dashboard_purchase.js',
            # 'inventory_scale_integration_dashboard/static/src/xml/weighing_dashboard_purchase.xml',
            # 'inventory_scale_integration_dashboard/static/src/js/weighing_dashboard_sale.js',
            # 'inventory_scale_integration_dashboard/static/src/xml/weighing_dashboard_sale.xml',

        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
