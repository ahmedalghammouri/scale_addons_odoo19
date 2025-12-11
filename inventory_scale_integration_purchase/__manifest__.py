{
    'name': 'Scale Integration - Purchase',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Stock',
    'summary': 'Weighbridge integration for purchase operations',
    'author': 'Gemy',
    'website': 'https://www.example.com',
    'license': 'LGPL-3',
    'depends': ['inventory_scale_integration_base', 'inventory_scale_integration_stock', 'purchase'],
    'data': [
        'views/truck_weighing_views.xml',
        'views/purchase_order_views.xml',
        'views/menu_items_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
