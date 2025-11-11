# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json

from datetime import datetime

from werkzeug.exceptions import Forbidden, NotFound
from werkzeug.urls import url_decode, url_encode, url_parse

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.fields import Command
from odoo.http import request, route
from odoo.osv import expression
from odoo.tools import clean_context, float_round, groupby, lazy, single_email_re, str2bool, SQL
from odoo.tools.image import image_data_uri
from odoo.tools.json import scriptsafe as json_scriptsafe
from odoo.tools.translate import _
from odoo.exceptions import AccessDenied, ValidationError, UserError

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment.controllers import portal as payment_portal
from odoo.addons.portal.controllers.portal import _build_url_w_params
from odoo.addons.sale.controllers import portal as sale_portal
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website.models.ir_http import sitemap_qs2dom
from odoo.addons.website_sale.controllers.main import WebsiteSale
import logging
_logger = logging.getLogger(__name__)
class DeploilyWebsiteSale(WebsiteSale):


    @route(
        '/shop/address/submit', type='http', methods=['POST'], auth='public', website=True,
        sitemap=False
    )
    def shop_address_submit(
        self, partner_id=None, address_type='billing', use_delivery_as_billing=None, callback=None,
        required_fields=None, **form_data
    ):
        """ Create or update an address.

        If it succeeds, it returns the URL to redirect (client-side) to. If it fails (missing or
        invalid information), it highlights the problematic form input with the appropriate error
        message.

        :param str partner_id: The partner whose address to update with the address form, if any.
        :param str address_type: The type of the address: 'billing' or 'delivery'.
        :param str use_delivery_as_billing: Whether the provided address should be used as both the
                                            billing and the delivery address. 'true' or 'false'.
        :param str callback: The URL to redirect to in case of successful address creation/update.
        :param str required_fields: The additional required address values, as a comma-separated
                                    list of `res.partner` fields.
        :param dict form_data: The form data to process as address values.
        :return: A JSON-encoded feedback, with either the success URL or an error message.
        :rtype: str
        """
        order_sudo = request.website.sale_get_order()
        if redirection := self._check_cart(order_sudo):
            return json.dumps({'redirectUrl': redirection.location})

        partner_sudo, address_type = self._prepare_address_update(
            order_sudo, partner_id=partner_id and int(partner_id), address_type=address_type
        )
        use_delivery_as_billing = str2bool(use_delivery_as_billing or 'false')
        required_fields = required_fields or ''

        # Parse form data into address values, and extract incompatible data as extra form data.
        address_values, extra_form_data = self._parse_form_data(form_data)
       
        is_anonymous_cart = order_sudo._is_anonymous_cart()
        is_main_address = is_anonymous_cart or order_sudo.partner_id.id == partner_sudo.id
        # Validate the address values and highlights the problems in the form, if any.
        invalid_fields, missing_fields, error_messages = self._validate_address_values(
            address_values,
            partner_sudo,
            address_type,
            use_delivery_as_billing,
            required_fields,
            is_main_address=is_main_address,
            **extra_form_data,
        )

        if not isinstance(error_messages, dict):
            error_messages = {}

        # Check terms_conditions
        if not form_data.get('terms_conditions'):
            invalid_fields.add('terms_conditions')
            error_messages['terms_conditions'] = [
                _("You must accept the Terms and Conditions and the Privacy Policy to continue.")
            ]

        if error_messages:
            return json.dumps({
                'invalid_fields': list(invalid_fields | missing_fields),
                'messages': error_messages,
            })

        is_new_address = False
        if not partner_sudo:  # Creation of a new address.
            is_new_address = True
            self._complete_address_values(
                address_values, address_type, use_delivery_as_billing, order_sudo
            )
            create_context = clean_context(request.env.context)
            create_context.update({
                'tracking_disable': True,
                'no_vat_validation': True,  # Already verified in _validate_address_values
            })
            partner_sudo = request.env['res.partner'].sudo().with_context(
                create_context
            ).create(address_values)
        elif not self._are_same_addresses(address_values, partner_sudo):
            partner_sudo.write(address_values)  # Keep the same partner if nothing changed.

        partner_fnames = set()
        if is_main_address:  # Main address updated.
            partner_fnames.add('partner_id')  # Force the re-computation of partner-based fields.

        if address_type == 'billing':
            partner_fnames.add('partner_invoice_id')
            if is_new_address and order_sudo.only_services:
                # The delivery address is required to make the order.
                partner_fnames.add('partner_shipping_id')
            callback = callback or self._get_extra_billing_info_route(order_sudo)
        elif address_type == 'delivery':
            partner_fnames.add('partner_shipping_id')
            if use_delivery_as_billing:
                partner_fnames.add('partner_invoice_id')

        order_sudo._update_address(partner_sudo.id, partner_fnames)

        if is_anonymous_cart:
            # Unsubscribe the public partner if the cart was previously anonymous.
            order_sudo.message_unsubscribe(order_sudo.website_id.partner_id.ids)

        if is_new_address or order_sudo.only_services:
            callback = callback or '/shop/checkout?try_skip_step=true'
        else:
            callback = callback or '/shop/checkout'

        self._handle_extra_form_data(extra_form_data, address_values)

        return json.dumps({
            'redirectUrl': callback,
        })