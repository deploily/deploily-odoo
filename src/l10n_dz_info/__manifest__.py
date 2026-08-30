# -*- coding: utf-8 -*-
{
    "name": "DZ - Info",
    "version": "18.0.1.0.0",
    "category": "Localization",
    "description": """
This is the module to manage the accounting chart for Algeria in Odoo.
========================================================================

This module applies to companies based in Algeria.

**Email:** contact@osis.dz
""",
    "author": "Osis + SARL Transformatek",
    "website": "https://deploily.cloud",
    "depends": ["account", "sale"],
    "data": [
        "security/ir.model.access.csv",
        "data/dz_wilayas.xml",
        "data/dz_commune.xml",
        "views/l10n_dz_info_view.xml",
        "reports/l10n_dz_info_external_layout.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3",
}
