{
    'name': 'Gas Retailer Management',
    'version': '1.0',
    'sequence': 2,
    'category': 'Manufacturing',
    'summary': 'Manage gas retailer business',
    'description': """
The aim is to have a complete module to manage all operations of gas retailer.
==============================================================================

The following topics are covered by this module:
------------------------------------------------------
    * Add/remove storage types for gases
    * Impact for stocks
    * Invoicing (storages and/or services)
    * Types of gases
    * Quotations
    * Notes for the manager and for the final customer
    """,
    'depends': ['product', 'stock', 'sale_management', 'account', 'portal'],
    'data': [
        'views/package.xml',
        'views/menu.xml',
    ],
    'demo': ['data/crio_demo.yml'],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}