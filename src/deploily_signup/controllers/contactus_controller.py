import base64
import json
import psycopg2

from markupsafe import Markup
from psycopg2 import IntegrityError
import re
from werkzeug.exceptions import BadRequest

from odoo import http, SUPERUSER_ID
from odoo.addons.base.models.ir_qweb_fields import nl2br, nl2br_enclose
from odoo.http import request
from odoo.tools import plaintext2html
from odoo.exceptions import AccessDenied, ValidationError, UserError
from odoo.tools.misc import hmac, consteq
from odoo.tools.translate import _, LazyTranslate
from odoo.addons.website.controllers.form import WebsiteForm
_lt = LazyTranslate(__name__)
import logging
_logger = logging.getLogger(__name__)

class DeploilyWebsiteForm(WebsiteForm): 

 # Check and insert values from the form on the model <model>
    @http.route('/website/form/<string:model_name>', type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def website_form(self, model_name, **kwargs):
        # Partial CSRF check, only performed when session is authenticated, as there
        # is no real risk for unauthenticated sessions here. It's a common case for
        # embedded forms now: SameSite policy rejects the cookies, so the session
        # is lost, and the CSRF check fails, breaking the post for no good reason.
        csrf_token = request.params.pop('csrf_token', None)
        if request.session.uid and not request.validate_csrf(csrf_token):
            raise BadRequest('Session expired (invalid CSRF token)')

        try:
            # The except clause below should not let what has been done inside
            # here be committed. It should not either roll back everything in
            # this controller method. Instead, we use a savepoint to roll back
            # what has been done inside the try clause.
            with request.env.cr.savepoint() as sp:
                if request.env['ir.http']._verify_request_recaptcha_token('website_form'):
                    # request.params was modified, update kwargs to reflect the changes
                    kwargs = dict(request.params)
                    kwargs.pop('model_name')
                    if not kwargs.get('terms_conditions'):
                      raise ValidationError(_("You must accept the Terms and Conditions before submitting the form."))
                    res = self._handle_website_form(model_name, **kwargs)
                    # ignore savepoint closing error if the transaction was committed
                    try:
                        sp.close(rollback=False)
                    except psycopg2.errors.InvalidSavepointSpecification:
                        sp.closed = True
                    return res
            error = _("Suspicious activity detected by Google reCaptcha.")
        except (ValidationError, UserError) as e:
            error = e.args[0]
        return json.dumps({
            'error': error,
        })
