# -*- coding: utf-8 -*-

import babel.dates
import re
import werkzeug

from ast import literal_eval
from collections import Counter
from werkzeug.exceptions import NotFound

from odoo import fields, http, _
from odoo.addons.website.controllers.main import QueryURL
from odoo.http import request
from odoo.osv import expression
from odoo.tools.misc import get_lang
from odoo.tools import lazy
from odoo.exceptions import UserError
from odoo.addons.website_event.controllers.main import WebsiteEventController

class DeploilyWebsiteEventController(WebsiteEventController):

    @http.route(['''/event/<model("event.event"):event>/registration/confirm'''], type='http', auth="public", methods=['POST'], website=True)
    def registration_confirm(self, event, **post):
            """ Check before creating and finalize the creation of the registrations
                that we have enough seats for all selected tickets.
                If we don't, the user is instead redirected to page to register with a
                formatted error message. """
            if not post.get('terms_conditions'):
                   raise UserError(_("You must accept the Terms and Conditions and the Privacy Policy to continue."))
            if not request.env['ir.http']._verify_request_recaptcha_token('website_event_registration'):
                raise UserError(_('Suspicious activity detected by Google reCaptcha.'))
            registrations_data = self._process_attendees_form(event, post)
            registration_tickets = Counter(registration['event_ticket_id'] for registration in registrations_data)
            event_tickets = request.env['event.event.ticket'].browse(list(registration_tickets.keys()))
            if any(event_ticket.seats_limited and event_ticket.seats_available < registration_tickets.get(event_ticket.id) for event_ticket in event_tickets):
                return request.redirect('/event/%s/register?registration_error_code=insufficient_seats' % event.id)
            attendees_sudo = self._create_attendees_from_registration_post(event, registrations_data)

            return request.redirect(('/event/%s/registration/success?' % event.id) + werkzeug.urls.url_encode({'registration_ids': ",".join([str(id) for id in attendees_sudo.ids])}))










