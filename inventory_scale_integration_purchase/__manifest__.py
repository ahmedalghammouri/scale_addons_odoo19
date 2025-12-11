{
'name': 'Scale Integration - Purchase',
'version': '19.0.1.0.0',
'category': 'Operations/Weighing',
'summary': 'Purchase Order integration for weighing scale operations',
'author': 'Gemy',
'website': 'https://www.example.com',
'license': 'LGPL-3',
'depends': ['inventory_scale_integration_base', 'purchase', 'stock'],
'data': [
'views/truck_weighing_views.xml',
'views/purchase_order_views.xml',
'views/stock_picking_views.xml',
'views/menu_items_views.xml',
],
'assets': {
'web.assets_backend': [
'inventory_scale_integration_purchase/static/src/js/weighing_dashboard_purchase.js',
'inventory_scale_integration_purchase/static/src/xml/weighing_dashboard_purchase.xml',
],
},
'auto_install': False,
'installable': True,
}