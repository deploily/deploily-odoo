# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#
# Copyright (c) 2016  - Osis - www.osis-dz.net

from odoo import api ,fields, models

class ResCompany(models.Model):
    _inherit = 'res.company'

    rc = fields.Char(string='R.C')
    nif = fields.Char(string='N.I.F', size=15)
    nis = fields.Char(string='N.I.S')
    ai = fields.Char(string='Article d\'imposition')

class ResPartner(models.Model):
    _inherit = 'res.partner'

    rc = fields.Char(string='R.C')
    nif = fields.Char(string='N.I.F', size=15)
    nis = fields.Char(string='N.I.S')
    ai = fields.Char(string='Article d\'imposition')
