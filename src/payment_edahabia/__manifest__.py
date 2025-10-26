# -*- coding: utf-8 -*-
{
    'name': "EDAHABIA Gateway",

    'summary': """Payment gateway for Algerian EDAHABIA cards""",

    'description': """
        Payment gateway for Algerian EDAHABIA cards from Algerie Poste
    """,
    'author': "SARL TransformaTek",
    'website': "https://transformatek.dz",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting/Payment Acquirers',
    'version': '3.0',

    # any module necessary for this one to work correctly
    'depends': ['payment', 'website_sale'],

    # always loaded
    'data': [
        'views/edahabia_views.xml',
        'views/edahabia_transaction_views.xml',
        'views/edahabia_templates.xml',
        'data/payment_acquirer_data.xml',
        'report/edahabia_payment_reports.xml',
        'security/ir.model.access.csv',
        'wizard/edahabia_transaction_wizard_views.xml',
    ],
    'installable': True,
    'application': True,
    'post_init_hook': 'create_missing_journal_for_acquirers',
    'uninstall_hook': 'uninstall_hook',

}
