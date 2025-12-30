{
    "name": "Website Sale Terms",
    "ressource": """
        Website Sales Terms and Conditions and Privacy Policy Management
    """,
    "author": "SARL Transformatek",
    "website": "https://transformatek.dz",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    "category": "Uncategorized",
    "version": "0.1",
    # any module necessary for this one to work correctly
    "depends": ["website_terms", "website_sale"],
    # always loaded
    "data": [
        "views/address_template.xml",
        # "views/newsletter_template.xml",
    ],
    "license": "Other proprietary",
    "assets": {
        "web.assets_frontend": [],
    },
    "application": True,
    "installable": True,
    "auto_install": False,
}
