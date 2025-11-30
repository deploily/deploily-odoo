# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import werkzeug
import werkzeug.exceptions
import werkzeug.urls
import werkzeug.wrappers
import logging
import json
import requests
from collections import OrderedDict, defaultdict
from odoo.exceptions import UserError

import werkzeug
import werkzeug.exceptions
import werkzeug.utils
import werkzeug.wrappers
import werkzeug.wsgi

import odoo
import odoo.modules.registry

from odoo.addons.base.models.ir_qweb import render as qweb_render
from werkzeug.urls import url_encode

from odoo import http
from markupsafe import Markup


from odoo.http import request
from odoo.osv import expression

from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.web.controllers.home import Home
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo import http, tools, _
import re

_logger = logging.getLogger(__name__)

# Shared parameters for all login/signup flows
SIGN_UP_REQUEST_PARAMS = {
    "db",
    "login",
    "debug",
    "token",
    "message",
    "error",
    "scope",
    "mode",
    "redirect",
    "redirect_hostname",
    "email",
    "name",
    "partner_id",
    "password",
    "confirm_password",
    "city",
    "country_id",
    "lang",
}


class DeploilySignup(AuthSignupHome):

    @http.route("/web/signup", type="http", auth="public", website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()

        if not qcontext.get("token") and not qcontext.get("signup_enabled"):
            raise werkzeug.exceptions.NotFound()

        # Get terms and conditions link
        website = request.env["website"].sudo().get_current_website()
        qcontext["terms_conditions_page"] = (
            website.terms_conditions_page.url if website.terms_conditions_page else None
        )
        qcontext["privacy_policy_page"] = (
            website.privacy_policy_page.url if website.privacy_policy_page else None
        )

        if "error" not in qcontext and request.httprequest.method == "POST":
            try:

                if not request.env["ir.http"]._verify_request_recaptcha_token("signup"):
                    raise UserError(
                        _("Suspicious activity detected by Google reCaptcha.")
                    )

                if not kw.get("terms_conditions"):
                    raise UserError(
                        _(
                            "You must accept the Terms and Conditions to create an account."
                        )
                    )
                # rECAPTCHA validation
                recaptcha_response = kw.get("g-recaptcha-response")

                if not recaptcha_response:
                    raise UserError("Please verify that you are not a robot.")

                secret_key = website.recaptcha_secret_key
                payload = {"secret": secret_key, "response": recaptcha_response}
                verify_url = "https://www.google.com/recaptcha/api/siteverify"
                response = requests.post(verify_url, data=payload)
                result = response.json()
                # ---- PASSWORD COMPLEXITY VALIDATION ----
                password = kw.get("password")
                if not password:
                    raise UserError("Password is required.")
                self.validate_password_complexity(password)
                self.do_signup(qcontext)

                if not result.get("success"):
                    raise UserError("Suspicious activity detected by Google reCAPTCHA.")

                # Set user to public if they were not signed in by do_signup
                # (mfa enabled)
                if request.session.uid is None:
                    public_user = request.env.ref("base.public_user")
                    request.update_env(user=public_user)

                # Send an account creation confirmation email
                User = request.env["res.users"]
                user_sudo = User.sudo().search(
                    User._get_login_domain(qcontext.get("login")),
                    order=User._get_login_order(),
                    limit=1,
                )
                template = request.env.ref(
                    "auth_signup.mail_template_user_signup_account_created",
                    raise_if_not_found=False,
                )
                if user_sudo and template:
                    template.sudo().send_mail(user_sudo.id, force_send=True)

                    
                return self.web_login(*args, **kw)
            except UserError as e:
                qcontext["error"] = e.args[0]
            except (SignupError, AssertionError) as e:
                if (
                    request.env["res.users"]
                    .sudo()
                    .search_count([("login", "=", qcontext.get("login"))], limit=1)
                ):
                    qcontext["error"] = _(
                        "Another user is already registered using this email address."
                    )
                else:
                    _logger.warning("%s", e)
                    qcontext["error"] = (
                        _("Could not create a new account.") + Markup("<br/>") + str(e)
                    )

        elif "signup_email" in qcontext:
            user = (
                request.env["res.users"]
                .sudo()
                .search(
                    [
                        ("email", "=", qcontext.get("signup_email")),
                        ("state", "!=", "new"),
                    ],
                    limit=1,
                )
            )
            if user:
                return request.redirect(
                    "/web/login?%s"
                    % url_encode({"login": user.login, "redirect": "/web"})
                )

        response = request.render("auth_signup.signup", qcontext)
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Content-Security-Policy"] = "frame-ancestors 'self'"
        return response


    def validate_password_complexity(self,password):
        if len(password) < 8:
            raise UserError("Password must be at least 8 characters long.")
        if len(password) > 32:
            raise UserError("Password cannot exceed 32 characters.")
        if not re.search(r"[A-Z]", password):
            raise UserError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", password):
            raise UserError("Password must contain at least one lowercase letter.")
        if not re.search(r"[0-9]", password):
            raise UserError("Password must contain at least one number.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise UserError("Password must contain at least one special character.")

        if len(password) < 12:
            raise UserError(
                "We recommend using at least 12 characters for improved security."
            )
        return True
    

    def validate_username(self, username):
        """Validates username (login) for length and allowed characters."""
        if not username:
            raise UserError("Username is required.")
        if len(username) < 3 or len(username) > 50:
            raise UserError("Username must be between 3 and 50 characters.")
        
        # Only allow alphanumeric, underscore, dash, dot
        if not re.match(r"^[a-zA-Z0-9_.-]+$", username):
            raise UserError(
                "Username can only contain letters, numbers, underscores (_), dashes (-), and dots (.)"
            )

    def validate_email(self, email):
        """Basic email format validation."""
        if not email:
            raise UserError("Email is required.")
        pattern = r"^[^@]+@[^@]+\.[^@]+$"
        if not re.match(pattern, email):
            raise UserError("Invalid email format.")


class DeploilyLogin(Home):

    @http.route("/web/login", type="http", auth="public", website=True)
    def web_login(self, **post):
        if request.httprequest.method == "POST":
            recaptcha_response = post.get('g-recaptcha-response')
            website = request.env["website"].sudo().get_current_website()

            secret_key = website.recaptcha_secret_key

            payload = {
                'secret': secret_key,
                'response': recaptcha_response,
                'remoteip': request.httprequest.remote_addr,
            }
            r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=payload)
            result = r.json()

            if not result.get('success'):
                return request.render('web.login', {
                    'error': 'Please verify that you are not a robot.',
                    'login': post.get('login'),
                    'databases': request.env['ir.config_parameter'].sudo().get_param('list_of_databases'),
                })

        # proceed with normal login
        return super(DeploilyLogin, self).web_login(**post)
    
