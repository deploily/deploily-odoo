# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#
# Copyright (c) 2016  - Osis - www.osis-dz.net

# Copyright (c) 2021 TransformaTek.dz  (<https://transformatek.dz/>)


{
    "name": "Algeria - Amount to Text",
    "version": "14.0",
    "category": "Accounting",
    "website": "https://transformatek.dz/",
    "summary": "This is the module print amount to Text in the Orders and Invoices reports.",
    "license": "AGPL-3",
    "description": """
This is the module print amount to Text in the purchase reports.
========================================================================

This module applies to companies based in Algeria.

**Email:** contact@transformatek.dz
""",
    "author": "Osis + TransformaTek",
    "website": "https://transformatek.dz/",
    "version": "14.0.0",
    "depends": ["purchase", "sale", "account"],
    "data": [
        "reports/orders_invoice_reports.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
