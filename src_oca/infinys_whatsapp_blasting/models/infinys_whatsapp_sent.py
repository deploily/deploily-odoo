import logging
import json
from odoo import api, fields, models
from odoo.exceptions import UserError
from ..utils import meta_utils

_logger = logging.getLogger(__name__)


class WhatsappSentMessage(models.Model):
    _name = 'infinys.whatsapp.sent'
    _description = 'Whatsapp Sent / Outgoing'
    _order = 'create_date desc'

    name = fields.Char(string="From", store=True)
    from_number = fields.Char(string="Sender Number", required=True, index=True)
    to_number = fields.Char(string="Receiver Number", required=True, index=True)

    body = fields.Text(string="Message", help="The main content of the message.")
    json_message = fields.Text(string="JSON Message")
    json_contact = fields.Text(string="JSON Contact")

    is_queued = fields.Boolean(string="Is Queued", default=True)
    is_sent = fields.Boolean(string="Is Sent", default=False)

    quotedMsgId = fields.Char(string="Quoted Message ID")

    state = fields.Selection([
        ('queued', 'Queued'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ], string="Status", default='queued')

    config_id = fields.Many2one(
        'infinys.whatsapp.config',
        string="Whatsapp Config",
        required=True,
        ondelete='cascade'
    )
    contact_id = fields.Many2one(
        'infinys.whatsapp.contact',
        string="Whatsapp Contact",
        ondelete='cascade'
    )
    mailing_id = fields.Many2one(
        'infinys.whatsapp.mailing',
        string="Mailing",
        ondelete='cascade'
    )
    mailing_list_id = fields.Many2one(
        'infinys.whatsapp.mailinglist',
        string="Mailing List",
        ondelete='cascade'
    )
    mailing_log_id = fields.Many2one(
        'infinys.whatsapp.mailing.log',
        string="Mailing Log",
        ondelete='set null',
        help="Reference to the mailing log for this sent message."
    )

    error_msg = fields.Text(string="Error Message", help="Error message if sending fails.")
    hasmedia = fields.Boolean(string="Has Media", default=False)
    mime_type = fields.Char(string="MIME Type", default='text/plain')

    create_date = fields.Datetime(string="Sent At", default=fields.Datetime.now, readonly=True)
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
    # ACTIONS
    # =========================================================

    def action_retry_send(self):
        """Retry sending a failed or queued message via Meta Cloud API."""
        for record in self:
            try:
                config = record.config_id

                if not config:
                    raise UserError("No WhatsApp configuration linked to this message.")

                phone_number_id = config.authentication_user

                if not phone_number_id:
                    raise UserError("Phone Number ID missing in configuration (Auth User/App ID).")

                if not config.token:
                    raise UserError("Access Token missing in configuration.")

                if not record.body:
                    raise UserError("Message body is empty.")

                _logger.info(
                    "Retrying send to %s via phone_number_id %s",
                    record.to_number,
                    phone_number_id
                )

                result = meta_utils.send_text_message(
                    whatsapp_api_url=config.whatsapp_api_url,
                    token=config.token,
                    phone_number_id=phone_number_id,
                    to_number=record.to_number,
                    message=record.body,
                )

                _logger.info("Retry result for %s: %s", record.to_number, result)

                if result.get('status') == 'success':
                    record.write({
                        'is_queued': False,
                        'is_sent': True,
                        'state': 'sent',
                        'error_msg': False,
                    })
                else:
                    record.write({
                        'state': 'failed',
                        'error_msg': result.get('message', 'Unknown error'),
                    })

            except Exception as e:
                _logger.error("Error retrying send for record %s: %s", record.id, e)
                record.write({
                    'state': 'failed',
                    'error_msg': str(e),
                })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': "Retry Complete",
                'message': "Retry send attempted. Check status column for results.",
                'type': 'success',
                'sticky': False,
            }
        }

    def action_mark_as_sent(self):
        """Manually mark message as sent."""
        self.write({
            'is_queued': False,
            'is_sent': True,
            'state': 'sent',
            'error_msg': False,
        })

    def action_mark_as_failed(self):
        """Manually mark message as failed."""
        self.write({
            'state': 'failed',
            'is_queued': False,
        })

    # =========================================================
    # CRON — Process Queued Messages
    # =========================================================

    def _process_queued_messages(self):
        """Cron job: process all queued sent messages via Meta Cloud API."""
        _logger.info("_process_queued_messages cron started")

        records = self.search([
            ('is_queued', '=', True),
            ('state', '!=', 'sent'),
        ], limit=50)

        _logger.info("Found %s queued messages to process", len(records))

        for record in records:
            try:
                config = record.config_id

                if not config or not config.token or not config.authentication_user:
                    _logger.warning("Skipping record %s — missing config/token/phone_number_id", record.id)
                    continue

                if not record.body:
                    _logger.warning("Skipping record %s — empty body", record.id)
                    continue

                result = meta_utils.send_text_message(
                    whatsapp_api_url=config.whatsapp_api_url,
                    token=config.token,
                    phone_number_id=config.authentication_user,
                    to_number=record.to_number,
                    message=record.body,
                )

                _logger.info("Queue process result for %s: %s", record.to_number, result)

                if result.get('status') == 'success':
                    record.write({
                        'is_queued': False,
                        'is_sent': True,
                        'state': 'sent',
                        'error_msg': False,
                    })
                else:
                    record.write({
                        'state': 'failed',
                        'error_msg': result.get('message', 'Unknown error'),
                        'is_queued': False,
                    })

            except Exception as e:
                _logger.error("Error processing queued record %s: %s", record.id, e)
                record.write({
                    'state': 'failed',
                    'error_msg': str(e),
                    'is_queued': False,
                })

        return True