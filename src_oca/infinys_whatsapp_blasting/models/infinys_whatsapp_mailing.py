import logging
import re
import json
from odoo import models, fields, api, tools
import werkzeug.urls
import pytz
import time
from datetime import datetime, timedelta
from odoo.tools import html_sanitize, html_escape
from odoo.tools.safe_eval import safe_eval
from odoo.tools.float_utils import float_round
from odoo.exceptions import UserError
import requests
from ..utils import waha_utils
from ..utils import meta_utils
from ..utils import texttohtml_utils
from ..utils import n8n_utils
from odoo.tools import html2plaintext

_logger = logging.getLogger(__name__)
_waha_utils = waha_utils
_meta_utils = meta_utils
_texttohtml_utils = texttohtml_utils


class WhatsappMailing(models.Model):
    _name = 'infinys.whatsapp.mailing'
    _description = 'WhatsApp Mass Messaging'
    _order = 'id desc, state_idx asc, name asc'

    name = fields.Char(string='Subject', required=True, store=True, index=True)
    error_msg = fields.Char(string="Error Message", default="")
    whatsapp_config_id = fields.Many2one(
        'infinys.whatsapp.config',
        string='Whatsapp Account',
        domain=[('active', '=', True)],
        required=True)

    responsible_id = fields.Many2one(
        'res.users',
        string='Responsible',
        default=lambda self: self.env.user,
    )

    mailing_list_id = fields.Many2one(
        'infinys.whatsapp.mailinglist',
        string='Mailing List'
    )

    sent_date = fields.Datetime(string='Sent Date')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submit'),
        ('done', 'Done'),
        ('failed', 'Partial Failure'),
        ('canceled', 'Cancelled')
    ], string='Status', default='draft', required=True, copy=False)

    recipients = fields.Selection([
        ('mailinglist', 'Mailing List'),
        ('mailinglistcontact', 'Mailing List Contact'),
    ], string="Recipients", default='mailinglist')

    message = fields.Html(string="Message", sanitize=False)
    is_body_empty = fields.Boolean(string="Is Body Empty", compute="_compute_statistics", store=True, default=False)
    header_type = fields.Selection([
        ('none', 'None'),
        ('text', 'Text'),
    ], string="Header Type", default='none')

    header_text = fields.Char(string="Template Header Text", size=60)
    footer_text = fields.Char(string="Footer Message", size=150)

    # Statistics are now computed from lines
    total_recipients = fields.Integer(string="Total")
    sent_count = fields.Integer(string="Sent")
    failed_count = fields.Integer(string="Failed")
    schedule_date = fields.Datetime(string='Schedule Date', default=fields.Datetime.now, required=True,
                                    help="If set, the mailing will be sent on this date/time.", store=True)
    create_year = fields.Integer(string="Year", compute="_compute_create_year", store=True)

    state_idx = fields.Integer(
        string='State Index',
        compute='_compute_state_idx',
        store=True,
        index=True
    )

    contact_ids = fields.Many2many(
        'infinys.whatsapp.contact',
        string='Contact List',
        help='Select contacts to include in this mailing list.'
    )

    _sql_constraints = {
        ('name_uniq', 'unique(name)', 'The name must be unique'),
    }

    # =========================================================
    # CONSTRAINTS
    # =========================================================

    @api.constrains('schedule_date')
    def _check_schedule_date(self):
        _logger.info("Checking schedule date constraints")
        sts = True
        for rec in self:
            _logger.info("Schedule date: %s", rec.schedule_date)
            _logger.info("State: %s", rec.state)
            if rec.state in ['submit', 'failed']:
                if rec.schedule_date and rec.schedule_date <= fields.Datetime.now():
                    raise UserError("Schedule date must be greater than today")
        return sts

    # =========================================================
    # COMPUTED FIELDS
    # =========================================================

    def _compute_statistics(self):
        for mailing in self:
            mailing.is_body_empty = tools.is_html_empty(mailing.message)

    @api.depends('create_date')
    def _compute_create_year(self):
        for rec in self:
            rec.create_year = rec.create_date.year if rec.create_date else False

    @api.depends('state', 'state_idx')
    def _compute_state_idx(self):
        self.state_idx = 1
        for record in self:
            idx = 1
            match record.state:
                case 'draft':
                    idx = 1
                case 'submit':
                    idx = 2
                case 'done':
                    idx = 3
                case 'failed':
                    idx = 4
                case 'canceled':
                    idx = 5
            record.state_idx = idx

    # =========================================================
    # BUTTON ACTIONS
    # =========================================================

    def btn_submit(self):
        _logger.info("btn_submit")
        if self.schedule_date:
            self.state = "submit"
            if not self._check_schedule_date():
                self.state = "draft"
        else:
            raise UserError("Schedule cannot be empty if you want to send now, please set it to today")
        return ""

    def btn_back_draft(self):
        _logger.info("btn_back_draft")
        self._compute_state_idx()
        self.state = "draft"
        return True

    def btn_cancel(self):
        self.state = "canceled"

    def btn_test(self):
        """Test Meta API connection using Phone Number ID from config."""
        _logger.info("btn_test")

        config = self.whatsapp_config_id

        # authentication_user field = Phone Number ID (e.g. 1549322289878086)
        phone_number_id = config.authentication_user

        if not phone_number_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': "Configuration Error",
                    'message': "Phone Number ID is missing. Please set the Auth User/App ID field in WhatsApp Configuration.",
                    'type': 'warning',
                    'sticky': False,
                }
            }

        data = _meta_utils.test_connection(
            whatsapp_api_url=config.whatsapp_api_url,
            token=config.token,
            phone_number_id=phone_number_id,
        )

        _logger.info("META TEST RESPONSE: %s", data)

        if data.get('status') == 'success':
            message = "Test WhatsApp successful ✔  Phone Number ID: " + str(phone_number_id)
            status = 'success'
        else:
            message = "Connection failed ❌  Error: " + data.get('message', 'Unknown error')
            status = 'warning'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': "WhatsApp Connection Test",
                'message': message,
                'type': status,
                'sticky': False,
            }
        }

    def btn_send_now(self):
        """Send WhatsApp messages immediately to all active contacts."""
        _logger.info("btn_send_now")

        record = self

        # Resolve contacts
        if record.recipients == 'mailinglistcontact':
            contact_ids = record.contact_ids.filtered('is_active')
        else:
            if not record.mailing_list_id:
                raise UserError("No Mailing List selected.")
            contact_ids = record.mailing_list_id.contact_ids.filtered('is_active')

        if not contact_ids:
            raise UserError("No active contacts found.")

        total = len(contact_ids)
        record.total_recipients = total

        _logger.info("Total contacts to send: %s", total)

        self._send_now_immediately(record, contact_ids)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': "WhatsApp Sent",
                'message': f"Message sent immediately to {total} contacts",
                'type': 'success',
                'sticky': False,
            }
        }

    # =========================================================
    # CORE SEND LOGIC
    # =========================================================

    def _send_now_immediately(self, mailing_record, contact_ids):
        """Send WhatsApp text messages immediately via Meta Cloud API."""
        _logger.info("Sending WhatsApp immediately")

        config = mailing_record.whatsapp_config_id

        # Phone Number ID is stored in authentication_user field
        phone_number_id = config.authentication_user

        if not phone_number_id:
            raise UserError(
                "Phone Number ID is missing in WhatsApp configuration.\n"
                "Please set the 'Auth User/App ID' field to your Meta Phone Number ID."
            )

        if not config.token:
            raise UserError("Access Token is missing in WhatsApp configuration.")

        success_count = 0
        fail_count = 0

        for contact in contact_ids:

            if not contact.whatsapp_number:
                _logger.warning("Skipping contact %s — no WhatsApp number", contact.name)
                fail_count += 1
                continue

            if not contact.is_active:
                _logger.warning("Skipping contact %s — inactive", contact.name)
                continue

            # Build message with variable replacements
            text_message = self.set_wa_messsage(
                mailing_record,
                contact.name,
                contact.full_name
            )

            # Convert HTML to plain text for WhatsApp
            text_message = html2plaintext(text_message)

            _logger.info(
                "Sending to %s (%s): %s",
                contact.name,
                contact.whatsapp_number,
                text_message
            )

            result = meta_utils.send_text_message(
                whatsapp_api_url=config.whatsapp_api_url,
                token=config.token,
                phone_number_id=phone_number_id,
                to_number=contact.whatsapp_number,
                message=text_message,
            )

            if result.get('status') == 'success':
                success_count += 1

                _logger.info("✅ Sent to %s", contact.whatsapp_number)
            else:
                fail_count += 1
                _logger.error("❌ Failed to send to %s: %s", contact.whatsapp_number, result.get('message'))

        _logger.info("Send complete — success: %s | failed: %s", success_count, fail_count)

        final_state = 'done' if fail_count == 0 else 'failed'
        error_msg = False if fail_count == 0 else f"{fail_count} message(s) failed to send"

        mailing_record.write({
            'state': final_state,
            'sent_date': fields.Datetime.now(),
            'sent_count': success_count,
            'failed_count': fail_count,
            'error_msg': error_msg,
        })

    def set_wa_messsage(self, mailing_record, to_contact_name, to_contact_fullname):
        """Build the WhatsApp message body with variable substitution."""
        mailing_record = self.env["infinys.whatsapp.mailing"].browse(mailing_record.id)
        text_message = mailing_record.message

        contact_variable = to_contact_name
        subject_variable = mailing_record.name
        milingList_text = mailing_record.mailing_list_id.name if mailing_record.mailing_list_id else ""
        header_text = mailing_record.header_text
        footer_text = mailing_record.footer_text

        if header_text:
            header_text = _texttohtml_utils.safe_replace(header_text, "{{subject}}", subject_variable)
            header_text = _texttohtml_utils.safe_replace(header_text, "{{contact.name}}", contact_variable)
            header_text = _texttohtml_utils.safe_replace(header_text, "{{contact.full_name}}", to_contact_fullname)
            header_text = _texttohtml_utils.safe_replace(header_text, "{{mailingList.name}}", milingList_text)
        else:
            header_text = ""

        if footer_text:
            footer_text = _texttohtml_utils.safe_replace(footer_text, "{{subject}}", subject_variable)
            footer_text = _texttohtml_utils.safe_replace(footer_text, "{{contact.name}}", contact_variable)
            footer_text = _texttohtml_utils.safe_replace(footer_text, "{{contact.full_name}}", to_contact_fullname)
            footer_text = _texttohtml_utils.safe_replace(footer_text, "{{mailingList.name}}", milingList_text)
        else:
            footer_text = ""

        _logger.info("text_message before replace: %s", text_message)

        if text_message:
            text_message = _texttohtml_utils.safe_replace(text_message, "{{subject}}", subject_variable)
            text_message = _texttohtml_utils.safe_replace(text_message, "{{contact.name}}", contact_variable)
            text_message = _texttohtml_utils.safe_replace(text_message, "{{contact.full_name}}", to_contact_fullname)
            text_message = _texttohtml_utils.safe_replace(text_message, "{{mailingList.name}}", milingList_text)

        # Bold header
        text_message = f"*{header_text}*\n" + text_message if len(header_text) > 0 else text_message

        # Italic footer
        text_message = f"{text_message}\n" + f"_{footer_text}_" if len(footer_text) > 0 else text_message

        text_message = _texttohtml_utils.clean_html_for_whatsapp(text_message)

        return text_message

    # =========================================================
    # QUEUE / SCHEDULER LOGIC
    # =========================================================

    def mailing_queue(self, mailing_record, contact_ids, state):
        """Create a mailing log and queue messages for sending."""
        try:
            rec_mailing_log = []
            mailing_record = self.env["infinys.whatsapp.mailing"].browse(mailing_record.id)
            total_contact = len(contact_ids)

            _logger.info("mailing_record: %s", mailing_record.id)
            _logger.info("total contact: %s", total_contact)

            if total_contact > 0:
                rec_mailing_log = self.env["infinys.whatsapp.mailing.log"].create({
                    'name': mailing_record.name,
                    'mailing_id': mailing_record.id,
                    'mailing_list_id': mailing_record.mailing_list_id.id if mailing_record.mailing_list_id else 0,
                    'total_contact': total_contact,
                    'state': state,
                    'sent_date': fields.Datetime.now()
                })

                self.set_webhook_message(mailing_record, rec_mailing_log, contact_ids)

                mailing_record.sent_date = fields.Datetime.now()
                mailing_record.error_msg = ""

                time.sleep(10)

                if state == "submit":
                    mailing_record.state = "done"

        except Exception as e:
            _logger.error("Error in mailing_queue: %s", e)
            mailing_record.error_msg = str(e)
            mailing_record.state = "failed"
            raise UserError(f"Error in mailing_queue: {e}")

        return True

    def set_webhook_message(self, mailing_record, rec_mailing_log, contact_ids):
        """Create queued sent records for each contact (used by n8n webhook flow)."""
        _logger.info("set_webhook_message")
        sts = False

        try:
            for contact in contact_ids:
                _logger.info(
                    "Processing contact: %s | number: %s | lists: %s",
                    contact.name,
                    contact.whatsapp_number,
                    contact.mailinglist_ids.ids
                )

                if not contact.whatsapp_number:
                    _logger.warning("Contact %s has no WhatsApp number — skipping.", contact.name)
                    continue

                if not contact.is_active:
                    continue

                text_message = self.set_wa_messsage(mailing_record, contact.name, contact.full_name)

                if text_message:
                    contact_data = {
                        "contact_id": f"{contact.id}",
                        "contact_name": f"{contact.name}",
                        "contact_whatsapp": f"{contact.whatsapp_number}",
                        "message": f"{text_message}",
                    }

                    payload = {
                        "jsonrpc": "2.0",
                        "wa_config_id": f"{mailing_record.whatsapp_config_id.id}",
                        "wa_config_name": f"{mailing_record.whatsapp_config_id.name}",
                        "mailing_id": f"{mailing_record.id}",
                        "mailing_list": f"{mailing_record.mailing_list_id.id}" if mailing_record.mailing_list_id else "0",
                        "mailing_list_name": f"{mailing_record.mailing_list_id.name}" if mailing_record.mailing_list_id else "",
                        "mailing_log_id": f"{rec_mailing_log.id}",
                        "session": "default",
                        "reply_to": f"{mailing_record.whatsapp_config_id.whatsapp_number}",
                        "contact": f"{json.dumps(contact_data)}"
                    }

                    self.env['infinys.whatsapp.sent'].create({
                        'name': contact.name,
                        'config_id': mailing_record.whatsapp_config_id.id,
                        'mailing_id': mailing_record.id,
                        'mailing_list_id': mailing_record.mailing_list_id.id if mailing_record.mailing_list_id else False,
                        'mailing_log_id': rec_mailing_log.id,
                        'contact_id': contact.id,
                        'from_number': contact.whatsapp_number,
                        'to_number': mailing_record.whatsapp_config_id.whatsapp_number,
                        'body': text_message,
                        'json_message': json.dumps(payload),
                        'json_contact': json.dumps(contact_data),
                        'mime_type': 'text/plain',
                        'hasmedia': False,
                        'is_queued': True
                    })

            sts = True

        except Exception as e:
            sts = False
            raise UserError(f"Error in set_webhook_message: {e}")

        return sts

    def _send_whatsapp_blasting(self):
        """Cron job: find submitted mailings due now and send them."""
        _logger.info("_send_whatsapp_blasting cron started")
        now = fields.Datetime.now()

        one_minute_ago = now - timedelta(minutes=1)
        one_minute_after = now + timedelta(minutes=1)

        _logger.info("now: %s | window: %s → %s", now, one_minute_ago, one_minute_after)

        records = self.sudo().search([
            ('state', '=', 'submit'),
            ('schedule_date', '>=', one_minute_ago),
            ('schedule_date', '<=', one_minute_after),
        ])

        _logger.info("Records found to process: %s", records.ids)

        for record in records:
            try:
                # Resolve active contacts
                if record.recipients == 'mailinglistcontact':
                    contact_ids = record.contact_ids.filtered('is_active')
                else:
                    if not record.mailing_list_id:
                        _logger.warning("Record %s has no mailing list — skipping.", record.id)
                        record.write({'state': 'failed', 'error_msg': 'No mailing list selected'})
                        continue
                    contact_ids = record.mailing_list_id.contact_ids.filtered('is_active')

                if not contact_ids:
                    _logger.warning("No active contacts for record %s", record.id)
                    record.write({'state': 'failed', 'error_msg': 'No active contacts found'})
                    continue

                record.total_recipients = len(contact_ids)

                self._send_now_immediately(record, contact_ids)

            except Exception as e:
                _logger.error("Error processing record %s: %s", record.id, e)
                record.write({'state': 'failed', 'error_msg': str(e)})

        return True

    # =========================================================
    # ENQUEUE PROCESSOR (n8n webhook flow)
    # =========================================================

    def _execute_enqueue(self):
        """Process queued messages and send via n8n webhook."""
        _logger.info("_execute_enqueue")

        records = self.env['infinys.whatsapp.sent'].search([('is_queued', '=', True)], limit=10)

        for record in records:
            try:
                record.error_msg = ""

                contact_data = {
                    "sent_id": f"{record.id}",
                    "contact_id": f"{record.contact_id.id}",
                    "contact_name": f"{record.name}",
                    "contact_whatsapp": f"{record.from_number}",
                    "message": f"{record.body}",
                }

                _logger.info("Sending contact_data: %s", contact_data)

                payload = {
                    "jsonrpc": "2.0",
                    "wa_config_id": f"{record.config_id.id}",
                    "wa_config_name": f"{record.config_id.name}",
                    "mailing_id": f"{record.mailing_id.id}" if record.mailing_id else "0",
                    "mailing_list": f"{record.mailing_list_id.id}" if record.mailing_list_id else "0",
                    "mailing_list_name": f"{record.mailing_list_id.name}" if record.mailing_list_id else "",
                    "mailing_log_id": f"{record.mailing_log_id.id}" if record.mailing_log_id else "0",
                    "session": "default",
                    "reply_to": f"{record.to_number}",
                    "contact": f"{json.dumps(contact_data)}"
                }

                _logger.info("Sending payload: %s", payload)

                n8n_utils.send_message(
                    record,
                    record.config_id.webhook_url,
                    record.config_id.authentication_user,
                    record.config_id.authentication_password,
                    payload
                )

                time.sleep(3)

            except Exception as e:
                _logger.error("Error in _execute_enqueue for record %s: %s", record.id, e)
                record.error_msg = f"Error in _execute_enqueue: {e}"
                record.is_queued = True

        return True

    # =========================================================
    # UTILITY
    # =========================================================

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        default.update({
            'name': f"{self.name} (Copy)-{self.id}",
            'state': 'draft',
        })
        return super(WhatsappMailing, self).copy(default=default)