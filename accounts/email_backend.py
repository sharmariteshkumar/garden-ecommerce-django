import requests

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


class BrevoEmailBackend(BaseEmailBackend):

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        api_key = settings.BREVO_API_KEY
        sender_email = settings.BREVO_SENDER_EMAIL
        sender_name = settings.BREVO_SENDER_NAME

        sent_count = 0

        for message in email_messages:
            recipients = message.recipients()

            if not recipients:
                continue

            payload = {
                "sender": {
                    "name": sender_name,
                    "email": sender_email,
                },
                "to": [
                    {"email": email}
                    for email in recipients
                ],
                "subject": message.subject,
                "textContent": message.body,
            }

            # If Django generated an HTML alternative, send it too
            if getattr(message, "alternatives", None):
                for content, mimetype in message.alternatives:
                    if mimetype == "text/html":
                        payload["htmlContent"] = content
                        break

            try:
                response = requests.post(
                    "https://api.brevo.com/v3/smtp/email",
                    headers={
                        "accept": "application/json",
                        "api-key": api_key,
                        "content-type": "application/json",
                    },
                    json=payload,
                    timeout=20,
                )

                response.raise_for_status()
                sent_count += 1

            except requests.RequestException:
                if not self.fail_silently:
                    raise

        return sent_count