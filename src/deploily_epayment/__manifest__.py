# -*- coding: utf-8 -*-
{
    "name": "CIB Epay",
    "summary": """Payment gateway for Algerian CIB cards""",
    "description": """
        Payment gateway for Algerian CIB cards
    """,
    "author": "SARL TransformaTek",
    "website": "https://transformatek.dz",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Accounting/Payment Providers",
    "version": "2.0",
    # any module necessary for this one to work correctly
    "depends": ["payment"],
    # always loaded
    "data": [
        "views/payment_provider_views.xml",
        "views/payment_transaction_views.xml",
        "views/cibepay_templates.xml",
        "data/payment_provider_data.xml",
        "data/payment_method_data.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "deploily_epayment/static/src/js/**",
        ],
    },
    # "installable": True,
    # "application": True,
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
}
