# -*- coding: utf-8 -*-
{
    'name': "CIB IPay Gateway",

    'summary': """Payment gateway for Algerian CIB cards""",

    'description': """
        Payment gateway for Algerian CIB cards
    """,
    'author': "SARL TransformaTek",
    'website': "https://transformatek.dz",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting/Payment Acquirers',
    'version': '3.1',

    # any module necessary for this one to work correctly
    'depends': ['payment'],

    # always loaded
    'data': [
        'views/cibipay_views.xml',
        'views/cibipay_transaction_views.xml',
        'views/cibipay_templates.xml',
        'data/payment_acquirer_data.xml',
        'report/cibipay_payment_reports.xml',
        'security/ir.model.access.csv',
        'wizard/cibipay_transaction_wizard_views.xml',
    ],
    'installable': True,
    'application': True,
    'post_init_hook': 'create_missing_journal_for_acquirers',
    'uninstall_hook': 'uninstall_hook',

}
