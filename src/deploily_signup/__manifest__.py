{
    "name": "deploily_signup",
    "ressource": """
        Signup with Deploily
    """,
    "author": "SARL Transformatek",
    "website": "https://transformatek.dz",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    "category": "Uncategorized",
    "version": "0.1",
    # any module necessary for this one to work correctly
    "depends": ["base", "contacts","website", "auth_signup","website_event"],
    # always loaded
    "data": [
        "views/signup_login_templates.xml",
        "views/website_views.xml",
        "views/modal_ticket_registration.xml",
        "views/address_template.xml",
        "views/menus.xml",
        # "views/newsletter_template.xml",
        "data/contactus_templates.xml",
    ],
    "license": "Other proprietary",
    "assets": {
        "web.assets_frontend": [],
    },
    "application": True,
    "installable": True,
    "auto_install": False,
}
