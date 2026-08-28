import hashlib
import hmac
import html
import os
from typing import Any, Literal
from urllib.parse import urlencode

from pydantic import BaseModel, EmailStr, Field


class PaymentEvent(BaseModel):
    event_id: str = Field(min_length=1)
    kind: Literal["payment_method_attached", "checkout_started", "payment_authorized"]
    amount_minor: int = Field(ge=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")


class SignupRequest(BaseModel):
    signup_id: str = Field(min_length=1)
    email: EmailStr
    risk_score: int = Field(ge=0, le=100)
    payment_event: PaymentEvent


class AuditRecord(BaseModel):
    event: Literal["signup_verification_requested", "signup_review_requested"]
    signup_id: str
    payment_event_id: str
    risk_score: int


class SignupResult(BaseModel):
    action: Literal["verification_sent", "manual_review"]
    audit: AuditRecord
    message_id: str | None = None


def _verification_token(signup_id: str, email: str, secret: str) -> str:
    message = f"{signup_id}:{email}".encode()
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


def process_signup(request: SignupRequest, sender: Any, base_url: str, signing_secret: str) -> SignupResult:
    if request.risk_score >= 70:
        return SignupResult(
            action="manual_review",
            audit=AuditRecord(
                event="signup_review_requested",
                signup_id=request.signup_id,
                payment_event_id=request.payment_event.event_id,
                risk_score=request.risk_score,
            ),
        )

    token = _verification_token(request.signup_id, str(request.email), signing_secret)
    query = urlencode({"token": token, "signup_id": request.signup_id})
    verification_url = f"{base_url.rstrip('/')}/verify-email?{query}"
    body = (
        "<h1>Confirm your email</h1>"
        "<p>Finish setting up your checkout account:</p>"
        f'<p><a href="{html.escape(verification_url, quote=True)}">Verify email</a></p>'
        "<p>If you did not start this signup, you can ignore this message.</p>"
    )
    delivery = sender.send(
        to=str(request.email),
        subject="Verify your email for checkout",
        html=body,
        idempotency_key=f"signup-verification:{request.signup_id}",
    )
    return SignupResult(
        action="verification_sent",
        message_id=str(delivery["message_id"]),
        audit=AuditRecord(
            event="signup_verification_requested",
            signup_id=request.signup_id,
            payment_event_id=request.payment_event.event_id,
            risk_score=request.risk_score,
        ),
    )


def environment_settings() -> tuple[str, str]:
    return os.environ.get("APP_BASE_URL", "http://localhost:8000"), os.environ.get(
        "VERIFICATION_SIGNING_SECRET", "local-demo-signing-secret"
    )
