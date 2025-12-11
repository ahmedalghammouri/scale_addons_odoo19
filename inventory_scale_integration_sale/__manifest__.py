{
'name': 'Scale Integration - Sales',
'version': '19.0.1.0.0',
'category': 'Operations/Weighing',
'summary': 'Sales Order integration for weighing scale operations',
'author': 'Gemy',
'website': 'https://www.example.com',
'license': 'LGPL-3',
'depends': ['inventory_scale_integration_base', 'sale', 'stock'],
'data': [
'views/truck_weighing_views.xml',
'views/sale_order_views.xml',
'views/stock_picking_views.xml',
'views/menu_items_views.xml',
],
'assets': {
'web.assets_backend': [
'inventory_scale_integration_sale/static/src/js/weighing_dashboard_sale.js',
'inventory_scale_integration_sale/static/src/xml/weighing_dashboard_sale.xml',
],
},
'auto_install': False,
'installable': True,
}