import os
import requests


EMAILJS_API_URL = "https://api.emailjs.com/api/v1.0/email/send"


def send_otp_email(to_email: str, otp: str) -> bool:
    """
    Send OTP email via EmailJS.
    Returns True on success, False on failure.
    Does NOT raise exceptions — the caller should handle the return value.
    """
    service_id = os.getenv("EMAILJS_SERVICE_ID")
    template_id = os.getenv("EMAILJS_TEMPLATE_ID")
    public_key = os.getenv("EMAILJS_PUBLIC_KEY")

    if not all([service_id, template_id, public_key]):
        print(f"WARNING: EmailJS not configured. OTP for {to_email}: {otp}")
        return False

    payload = {
        "service_id": service_id,
        "template_id": template_id,
        "user_id": public_key,
        "accessToken": os.getenv("EMAILJS_PRIVATE_KEY"),
        "template_params": {
            "to_email": to_email,
            "otp": otp,
        },
    }

    try:
        response = requests.post(EMAILJS_API_URL, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"OTP email sent to {to_email}")
            return True
        else:
            print(f"WARNING: EmailJS returned {response.status_code} for {to_email}. OTP: {otp}")
            return False
    except Exception as e:
        print(f"WARNING: Failed to send OTP email to {to_email}: {e}. OTP: {otp}")
        return False
