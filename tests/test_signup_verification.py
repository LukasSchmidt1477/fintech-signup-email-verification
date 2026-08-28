from fintech_signup.signup_verification import PaymentEvent, SignupRequest, process_signup


class RecordingSender:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def send(self, *, to: str, subject: str, html: str, idempotency_key: str) -> dict[str, object]:
        self.calls.append({"to": to, "subject": subject, "html": html, "idempotency_key": idempotency_key})
        return {"message_id": "msg_test_42"}


def signup(risk_score: int) -> SignupRequest:
    return SignupRequest(
        signup_id="signup_1042",
        email="buyer@example.com",
        risk_score=risk_score,
        payment_event=PaymentEvent(
            event_id="payevt_7331",
            kind="payment_method_attached",
            amount_minor=0,
            currency="USD",
        ),
    )


def test_low_risk_signup_sends_auditable_verification() -> None:
    sender = RecordingSender()
    result = process_signup(signup(12), sender, "https://shop.example", "test-secret")

    assert result.action == "verification_sent"
    assert result.message_id == "msg_test_42"
    assert result.audit.event == "signup_verification_requested"
    assert result.audit.payment_event_id == "payevt_7331"
    assert sender.calls[0]["idempotency_key"] == "signup-verification:signup_1042"
    assert "https://shop.example/verify-email?" in sender.calls[0]["html"]


def test_high_risk_signup_is_held_without_email() -> None:
    sender = RecordingSender()
    result = process_signup(signup(70), sender, "https://shop.example", "test-secret")

    assert result.action == "manual_review"
    assert result.audit.event == "signup_review_requested"
    assert result.message_id is None
    assert sender.calls == []
