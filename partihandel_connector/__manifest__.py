{
    'name': 'Partihandel Connector',
    'version': '19.0.1.0.0',
    'summary': 'Connect Odoo to Partihandel, the order and warehouse system for wholesalers',
    'description': """
Partihandel Connector
=====================

Sets up the connection between this Odoo database and Partihandel in one step:
it creates a dedicated integration user with the access Partihandel needs and
issues an API key for it. Paste the values into Partihandel and customers,
products and invoices start flowing.

Requires a Partihandel account.
    """,
    'author': 'Pifa Group AB',
    'maintainer': 'Pifa Group AB',
    'website': 'https://partihandel.se',
    'support': 'support@partihandel.se',
    'category': 'Accounting/Accounting',
    'license': 'LGPL-3',
    'depends': ['account', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/partihandel_setup_wizard_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
}
