# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class DeploilyWebsite(models.Model):
    _inherit = "website"

    terms_conditions_page = fields.Many2one(
        "website.page",
        string="Terms and Conditions Page",
    )
    privacy_policy_page = fields.Many2one("website.page", string="Privacy Policy Page")
