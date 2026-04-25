# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#
# Copyright (c) 2016  - Osis - www.osis-dz.net

# Copyright (c) 2021 TransformaTek.dz  (<https://transformatek.dz/>)


from math import ceil
from odoo import fields, models, api

class AccountInvoiceTimbre(models.Model):
    _inherit = "account.move"

    amount_timbre = fields.Monetary(string='Timbre', readonly=True,
                             compute='_compute_amount_timbre', track_visibility='always')
    amount_total_timbre = fields.Monetary(string='Total avec Timbre', 
                                    readonly=True, compute='_compute_amount_timbre', track_visibility='always')

    @api.depends('amount_total')
    def _compute_amount_timbre(self):
        for order in self:
            timbre = self.env['config.timbre']._timbre(order.amount_total)
            self.amount_timbre = timbre['timbre']
            self.amount_total_timbre = timbre['amount_timbre']


