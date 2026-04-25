# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#
# Copyright (c) 2016  - Osis - www.osis-dz.net

# Copyright (c) 2021 TransformaTek.dz  (<https://transformatek.dz/>)


{
    "name": "Algeria - Fiscal Timbre ",
    "version": "14.0",
    "category": "Accounting",
    "website": "https://transformatek.dz/",
    "summary": "This is the module calculate the Fiscal Timbre payments in invoices for cash.",
    "license": "AGPL-3",
    "description": """
This is the module to manage the Fiscal Timbre in Odoo.
========================================================================

This module applies to companies based in Algeria.

**Email:** contact@transformatek.dz
""",
    "author": "Osis + TransformaTek",
    "website": "https://transformatek.dz/",
    "version": "14.0.0",
    "depends": ["sale", "account"],
    "data": [
        "security/ir.model.access.csv",
        "views/timbre_view.xml",
        "views/timbre_invoice_view.xml",
        "views/timbre_invoice_template.xml",
        "data/timbre_data.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
