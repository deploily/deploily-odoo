# -*- coding: utf-8 -*-
{
    "name": "DZ - Info - Invoice",
    "version": "18.0.1.0.0",
    "category": "Localization",
    "description": """
This module adds additionnal company info to invoices for Algeria in Odoo.
==========================================================================

This module applies to companies based in Algeria.

**Email:** contact@tranformatek.dz
""",
    "author": "SARL Transformatek",
    "website": "https://deploily.cloud",
    "depends": ["account", "l10n_dz_info"],
    "data": [
        "reports/l10n_dz_info_report_invoice_document.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
