import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fintech_signup.infrai_email import InfraiEmail
from fintech_signup.signup_verification import PaymentEvent, SignupRequest, environment_settings, process_signup


def main() -> None:
    request = SignupRequest(
        signup_id="demo-checkout-signup",
        email=os.environ["DEMO_EMAIL_TO"],
        risk_score=12,
        payment_event=PaymentEvent(
            event_id="demo-payment-event",
            kind="payment_method_attached",
            amount_minor=0,
            currency="USD",
        ),
    )
    base_url, signing_secret = environment_settings()
    result = process_signup(request, InfraiEmail(), base_url, signing_secret)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
