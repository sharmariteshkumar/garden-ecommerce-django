import os
import requests


BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def send_customer_email(
    to_email,
    subject,
    message,
):
    api_key = os.environ.get("BREVO_API_KEY")
    sender_email = os.environ.get("BREVO_SENDER_EMAIL")
    sender_name = os.environ.get(
        "BREVO_SENDER_NAME",
        "ShopEasy Garden",
    )

    if not api_key:
        print("BREVO EMAIL FAILED: BREVO_API_KEY is missing")
        return False

    if not sender_email:
        print("BREVO EMAIL FAILED: BREVO_SENDER_EMAIL is missing")
        return False

    if not to_email:
        print("BREVO EMAIL FAILED: customer email is missing")
        return False

    payload = {
        "sender": {
            "name": sender_name,
            "email": sender_email,
        },
        "to": [
            {
                "email": to_email,
            }
        ],
        "subject": subject,
        "textContent": message,
    }

    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json",
    }

    try:
        response = requests.post(
            BREVO_API_URL,
            json=payload,
            headers=headers,
            timeout=15,
        )

        if 200 <= response.status_code < 300:
            print(
                f"BREVO EMAIL SENT: "
                f"{to_email} | {subject}"
            )
            return True

        print(
            f"BREVO EMAIL FAILED: "
            f"{to_email} | "
            f"HTTP {response.status_code} | "
            f"{response.text}"
        )
        return False

    except Exception as e:
        print(
            f"BREVO EMAIL FAILED: "
            f"{to_email} | {repr(e)}"
        )
        return False