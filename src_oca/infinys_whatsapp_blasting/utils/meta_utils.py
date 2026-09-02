
import requests
import json
import logging

_logger = logging.getLogger(__name__)


def test_connection(whatsapp_api_url, token, phone_number_id, **kwargs):
    """Test connection to Meta Cloud API."""
    try:
        url = f"https://graph.facebook.com/v25.0/{phone_number_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return {"status": "success", "message": "Connection successful", "data": response.json()}
    except requests.RequestException as e:
        _logger.error("Meta API connection test failed: %s", e)
        return {"status": "error", "message": str(e)}


def send_text_message(whatsapp_api_url, token, phone_number_id, to_number, message, **kwargs):
    """Send a text message via Meta Cloud API."""
    try:
        # Clean phone number: remove +, spaces, dashes
        to_number_clean = str(to_number).replace("+", "").replace(" ", "").replace("-", "").strip()

        url = f"https://graph.facebook.com/v25.0/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number_clean,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message
            }
        }

        _logger.info("META SEND → URL: %s | TO: %s | MSG: %s", url, to_number_clean, message)

        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)

        _logger.info("META RESPONSE → status: %s | body: %s", response.status_code, response.text)

        response.raise_for_status()
        return {"status": "success", "message": "Message sent", "data": response.json()}

    except requests.RequestException as e:
        _logger.error("Meta API send message failed: %s", e)
        return {"status": "error", "message": str(e)}


def send_template_message(whatsapp_api_url, token, phone_number_id, to_number, template_name, language_code="en_US", **kwargs):
    """Send a template message via Meta Cloud API."""
    try:
        to_number_clean = str(to_number).replace("+", "").replace(" ", "").replace("-", "").strip()

        url = f"https://graph.facebook.com/v25.0/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number_clean,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                }
            }
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        response.raise_for_status()
        return {"status": "success", "message": "Template sent", "data": response.json()}

    except requests.RequestException as e:
        _logger.error("Meta API send template failed: %s", e)
        return {"status": "error", "message": str(e)}