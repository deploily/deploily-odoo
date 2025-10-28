# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class DeploilyWebsite(models.Model):
    _inherit = "website"

    terms_conditions_page = fields.Many2one(
        "website.page", string="Terms and Conditions Page"
    )
    privacy_policy_page = fields.Many2one("website.page", string="Privacy Policy Page")
    recaptcha_site_key = fields.Char(string="reCAPTCHA Site Key")
    recaptcha_secret_key = fields.Char(string="reCAPTCHA Secret Key")

    def get_recaptcha_site_key(self):
        self.ensure_one()
        return self.recaptcha_site_key

    # def terms_conditions_page(self):
    #     self.ensure_one()
    #     return self.terms_conditions_page.url
