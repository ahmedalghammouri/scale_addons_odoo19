{
    'name': 'Scale Integration - ZPL Printer',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Stock',
    'summary': 'ZPL thermal printer integration for weighing labels and tickets',
    'description': '''
ZPL Printer Integration for Weighbridge
========================================
Professional thermal printer support:
* Configure ZPL printers (Zebra, compatible brands)
* Assign printers to scales and users
* Auto-print labels and tickets
* Network and USB printer support
* Custom label templates
* Print queue management
    ''',
    'author': 'Gemy',
    'website': 'https://www.example.com',
    'license': 'LGPL-3',
    'depends': [
        'inventory_scale_integration_base',
        'inventory_scale_integration_cashier',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/zpl_printer_views.xml',
        'views/truck_weighing_views.xml',
        'views/weighing_cashier_zpl_views.xml',
        'views/menu_items_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
