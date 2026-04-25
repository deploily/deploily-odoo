# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#
# Copyright (c) 2016  - Osis - www.osis-dz.net

{
    'name': 'Algeria - Accounting',
    'version': '1.1',
    'category': 'Localization',
    'description': """
This is the module to manage the accounting chart for Algeria in Odoo.
========================================================================

This module applies to companies based in Algeria.
.

**Email:** contact@osis.dz
""",
    'author': 'Osis + Transformatek',
    'website': 'ttps://transformatek.dz/',
    'depends': ['account','sale'],
    'data': [
        'views/l10n_dz_info_view.xml',
        'reports/l10n_dz_info_external_layout.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
}
