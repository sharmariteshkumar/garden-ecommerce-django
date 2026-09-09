import json
import os
import urllib.request
import urllib.error


BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def send_brevo_email(to_email, subject, html_content, to_name="Customer"):
    api_key = os.environ.get("BREVO_API_KEY")
    sender_email = os.environ.get("BREVO_SENDER_EMAIL")
    sender_name = os.environ.get(
        "BREVO_SENDER_NAME",
        "ShopEasy Garden"
    )

    if not api_key:
        print("BREVO EMAIL ERROR: BREVO_API_KEY is missing")
        return False

    if not sender_email:
        print("BREVO EMAIL ERROR: BREVO_SENDER_EMAIL is missing")
        return False

    payload = {
        "sender": {
            "name": sender_name,
            "email": sender_email,
        },
        "to": [
            {
                "email": to_email,
                "name": to_name or "Customer",
            }
        ],
        "subject": subject,
        "htmlContent": html_content,
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        BREVO_API_URL,
        data=data,
        headers={
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            response_data = json.loads(
                response.read().decode("utf-8")
            )

            print(
                f"BREVO EMAIL SENT: {to_email} | "
                f"{response_data.get('messageId', 'OK')}"
            )

            return True

    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode(
            "utf-8",
            errors="replace"
        )

        print(
            f"BREVO EMAIL FAILED: {to_email} | "
            f"HTTP {exc.code} | {error_body}"
        )

        return False

    except Exception as exc:
        print(
            f"BREVO EMAIL ERROR: {to_email} | "
            f"{repr(exc)}"
        )

        return False