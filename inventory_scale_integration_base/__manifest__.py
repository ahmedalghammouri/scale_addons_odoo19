{
'name': 'Scale Integration - Base',
'version': '19.0.1.0.0',
'category': 'Operations/Weighing',
'summary': 'Core weighing scale integration - basic truck and scale management',
'author': 'Gemy',
'website': 'https://www.example.com',
'license': 'LGPL-3',
'depends': ['base', 'product', 'mail', 'web','stock'],
'data': [
'data/sequences.xml',
'security/security.xml',
'security/ir.model.access.csv',
'views/truck_weighing_views.xml',
'views/truck_fleet_views.xml',
'views/weighing_scale_views.xml',
'views/product_views.xml',
'views/weighing_overview_views.xml',
'views/menu_items_views.xml',
],
'assets': {
'web.assets_backend': [
'inventory_scale_integration_base/static/src/js/weighing_dashboard.js',
'inventory_scale_integration_base/static/src/xml/weighing_dashboard.xml',
'inventory_scale_integration_base/static/src/scss/weighing_dashboard.scss',
],
'web.assets_web_dark': [
'inventory_scale_integration_base/static/src/scss/weighing_dashboard.scss',
],
},
'installable': True,
'application': True,
}