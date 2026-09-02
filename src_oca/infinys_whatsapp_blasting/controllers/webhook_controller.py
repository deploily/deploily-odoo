# -*- coding: utf-8 -*-
import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class WhatsAppWebhookController(http.Controller):

    VERIFY_TOKEN = "mytoken123"  # move later to system parameter

    # --------------------------------------------------------
    # WhatsApp Webhook (Meta verification + incoming messages)
    # --------------------------------------------------------
    @http.route(
        '/isi/wa_incoming',
        type='http',
        auth='public',
        methods=['GET', 'POST'],
        csrf=False
    )
    def wa_incoming(self, **kwargs):
        # ----------------------------------------------------
        # 1. META WEBHOOK VERIFICATION (GET)
        # ----------------------------------------------------
        if request.httprequest.method == 'GET':
            mode = request.params.get("hub.mode")
            token = request.params.get("hub.verify_token")
            challenge = request.params.get("hub.challenge")
            if mode == "subscribe" and token == self.VERIFY_TOKEN:
                _logger.info("WhatsApp webhook verified successfully")
                return challenge or ""

            _logger.warning("WhatsApp webhook verification failed")
            return "Forbidden", 403

        # ----------------------------------------------------
        # 2. INCOMING MESSAGES (POST)
        # ----------------------------------------------------
        try:
            payload = request.httprequest.get_json(force=True)

            _logger.info("WhatsApp incoming payload: %s", payload)

            results = []

            for entry in payload.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})

                    msgs = value.get("messages", [])

                    _logger.info("Extracted raw messages: %s", msgs)

                    for msg in msgs:
                        from_number = msg.get("from")
                        body = msg.get("text", {}).get("body")

                        metadata = value.get("metadata", {})
                        to_number = metadata.get("display_phone_number")
                        phone_number_id = metadata.get("phone_number_id")

                        record = request.env["infinys.whatsapp.incoming"].sudo().create({
                                "name": from_number,
                                "from_number": from_number,
                                "to_number": to_number,
                                "body": body,
                                "raw_data": json.dumps(msg),
                                "phone_number_id": phone_number_id,   # ✅ ADD THIS

                            })

                        results.append({
                            "id": record.id,
                            "from": from_number,
                            "message": body,
                        })

            return request.make_json_response({
                "status": "ok",
                "result": results
            })

        except Exception as e:
            _logger.exception("WhatsApp webhook error")
            return request.make_response(
                json.dumps({
                    "jsonrpc": "2.0",
                    "error": str(e)
                }),
                status=500,
                headers=[("Content-Type", "application/json")]
            )