# -*- coding: utf-8 -*-
{
    "name": "Odoo 14 GA-4",
    "summary": """
        Replace Google Analytics UA with GA-4 in Odoo 14""",
    "description": """
        Replace Google Analytics UA with GA-4 in Odoo 14
    """,
    "author": "SARL Transformatek",
    "website": "https://www.transformatek.dz",
    # for the full list
    "category": "website",
    "version": "0.1",
    # any module necessary for this one to work correctly
    "depends": ["website"],
    # always loaded
    "data": [
        "views/templates.xml",
    ],
    "installable": True,
    "application": False,
}
