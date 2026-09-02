import logging
import json
from odoo import api, fields, models
from odoo.exceptions import UserError
from ..utils import texttohtml_utils
from ..utils import meta_utils
from ..utils import waha_utils
from odoo.tools import html2plaintext

_logger = logging.getLogger(__name__)
_texttohtml_utils = texttohtml_utils
_waha_utils = waha_utils


class WhatsappIncomingMessage(models.Model):
    _name = 'infinys.whatsapp.incoming'
    _description = 'Whatsapp Incoming Message (Inbox)'
    _order = 'create_date desc'

    name = fields.Char(string="From", store=True)
    from_number = fields.Char(string="Sender Number", required=True, index=True)
    to_number = fields.Char(string="Receiver Number", required=True, index=True)

    raw_data = fields.Text(string="Raw Message")
    body = fields.Text(string="Message", help="The main content of the message.")
    reply_message = fields.Html(string="Reply Message", sanitize=False)
    state = fields.Selection([('unread', 'Unread'), ('read', 'Read')], default='unread')
    quotedMsgId = fields.Char(string="Quoted Message ID")

    contact_id = fields.Many2one('infinys.whatsapp.contact', string="Whatsapp Contact", ondelete='cascade')

    hasmedia = fields.Boolean(string="Has Media", default=False)
    mime_type = fields.Char(string="MIME Type", default='text/plain')

    create_date = fields.Datetime(string="Received At", default=fields.Datetime.now, readonly=True)
    file_media = fields.Binary(string="Media File")

    order_date = fields.Date(
        string='Order Date',
        compute='_compute_order_date',
        store=True
    )

    order_month = fields.Char(
        string='Order Month',
        compute='_compute_order_month',
        store=True
    )
    phone_number_id = fields.Char(string="Phone Number ID", index=True)

    # =========================================================
    # ACTIONS
    # =========================================================

    def action_mark_as_read(self):
        self.write({'state': 'read'})

    def action_mark_as_unread(self):
        self.write({'state': 'unread'})

    # =========================================================
    # COMPUTED FIELDS
    # =========================================================

    @api.depends('create_date')
    def _compute_order_date(self):
        for record in self:
            if record.create_date:
                record.order_date = record.create_date.date()
            else:
                record.order_date = False

    @api.depends('create_date')
    def _compute_order_month(self):
        for record in self:
            if record.create_date:
                record.order_month = record.create_date.strftime("%Y-%b")

    # =========================================================
    # ONCHANGE
    # =========================================================

    @api.onchange('from_number')
    def _onchange_from_number(self):
        if self.from_number:
            self.contact_id = self.env['infinys.whatsapp.contact'].search(
                [('whatsapp_number', '=', self.from_number)], limit=1
            )
            _logger.info("Contact found: %s for number: %s", self.contact_id.id, self.from_number)

            if not self.contact_id.id:
                _logger.info("Creating new contact for number: %s", self.from_number)
                indonesia = self.env['res.country'].sudo().search([('code', '=', 'ID')], limit=1)
                self.contact_id = self.env['infinys.whatsapp.contact'].sudo().create({
                    'name': self.name or self.from_number,
                    'whatsapp_number': self.from_number,
                    'country_id': indonesia.id if indonesia else None,
                    'is_active': True,
                    'is_new_user': False,
                    'is_manual': False,
                    'total_received_messages': 1
                })
                _logger.info("Created new contact: %s", self.contact_id.id)
            else:
                self.name = self.contact_id.name
                self.contact_id.sudo().write({
                    'is_new_user': False,
                    'total_received_messages': self.contact_id.total_received_messages + 1
                })

    # =========================================================
    # REPLY BUTTON
    # =========================================================
    def btn_reply_queue_message(self):
        try:
            if not self.reply_message:
                raise UserError("Please input reply message.")

            if not self.phone_number_id:
                raise UserError("Missing phone_number_id in message.")

            config = self.env['infinys.whatsapp.config'].search([
                ('authentication_user', '=', self.phone_number_id)
            ], limit=1)

            if not config:
                raise UserError(f"No config found for phone_number_id: {self.phone_number_id}")

            text = html2plaintext(
                texttohtml_utils.clean_html_for_whatsapp(self.reply_message)
            )

            result = meta_utils.send_text_message(
                whatsapp_api_url=config.whatsapp_api_url,
                token=config.token,
                phone_number_id=config.authentication_user,
                to_number=self.from_number,
                message=text,
            )

            success = result.get('status') == 'success'

            self.env['infinys.whatsapp.sent'].create({
                'name': self.name or self.from_number,
                'config_id': config.id,
                'contact_id': self.contact_id.id,
                'from_number': self.from_number,
                'to_number': self.from_number,
                'quotedMsgId': self.quotedMsgId or '',
                'body': text,
                'is_queued': not success,
                'error_msg': False if success else result.get('message'),
            })

            self.write({'state': 'read'})

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': "Reply Status",
                    'message': "✅ Sent successfully" if success else "⚠️ Failed to send",
                    'type': 'success' if success else 'warning',
                }
            }

        except Exception as e:
            _logger.exception("Reply error")
            raise UserError(str(e))