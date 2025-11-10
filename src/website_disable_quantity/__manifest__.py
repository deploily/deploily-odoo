{
    "name": "website_disable_quantity",
    "ressource": """
        Disable quantity on website""",
    "author": "SARL Transformatek",
    "website": "https://transformatek.dz",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    "category": "Uncategorized",
    "version": "0.1",
    # any module necessary for this one to work correctly
    "depends": ["base", "website","website_slides","website_sale","sale_management","sale"],
    # always loaded
    "data": [
        # "views/product_configurator_dialog.xml",
    ],
    "license": "Other proprietary",
    "assets": {

       
        "web.assets_frontend": [          

                'website_disable_quantity/static/src/js/product/product.xml',
                'website_disable_quantity/static/src/js/productlist/product_list.xml',
                'website_disable_quantity/static/src/js/combo_configurator_dialog/combo_configurator_dialog.xml',
],
    },
    "application": True,
    "installable": True,
    "auto_install": False,
}
