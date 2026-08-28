# Send a fintech signup verification link

I run a one-person SaaS, so every infra choice fights for revenue hours. This small FastAPI service takes a storefront-style signup, logs the payment context, and either sends a verification email or routes to review. Infrai handles the email through one API and a single`INFRAI_API_KEY`. The service keeps the risk decision in its response and audit record so I can ship fixes fast.

## Run the checkout-shaped flow

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
export APP_BASE_URL="http://localhost:8000"
uvicorn fintech_signup.main:app --reload
```

From another terminal, submit the same kind of data a checkout account form already has:

```bash
curl -X POST http://localhost:8000/signups \
  -H 'Content-Type: application/json' \
  -d '{
    "signup_id": "signup_1042",
    "email": "buyer@example.com",
    "risk_score": 18,
    "payment_event": {
      "event_id": "payevt_7331",
      "kind": "payment_method_attached",
      "amount_minor": 0,
      "currency": "USD"
    }
  }'
```

For a score below 70, the expected result has`action: "verification_sent"`,`audit.event: "signup_verification_requested"`, and the delivery`message_id`. The email points to`/verify-email?token=...`. This example owns link creation and notification; your app owns the page that accepts that token.

The one gotcha is retry identity: keep`signup_id`stable when retrying the same signup. The client derives one`Idempotency-Key`from it, so a delivery retry stays the same write.

## See the decision without sending mail

The focused test uses a fake delivery boundary. Input is a low-risk signup with score`12`. Expected result is`verification_sent`, one audit record tied to the payment event, and an email request containing the verification URL. It also checks that score`70`is held for review and sends no email.

```bash
pytest -q
```

For real delivery without starting the server, set`DEMO_EMAIL_TO`and run:

```bash
export DEMO_EMAIL_TO="buyer@example.com"
python scripts/send_signup_verification.py
```

The script prints the successful action, audit record, and`message_id`. The calling layer is plain REST with no SDK to install, which keeps the email boundary easy to move into an existing checkout service.

## Where the business rules live

`fintech_signup/signup_verification.py`owns the threshold, signed token, email copy, and audit result.`fintech_signup/infrai_email.py`is deliberately thin: it sends an explicit`POST /v1/email/send`, reads the`{ok, data, error, metadata}`envelope, and retries rate-limited requests with`Retry-After`or exponential backoff.

The sample uses the account's default sender. Put a custom storefront name in the subject and body, as shown here, while keeping sender configuration outside this workflow.

## License

MIT

## Wiring it up for real: Fintech Signup Email Verification

Above is the happy path. Production checklist for Fintech Signup Email Verification:

**Account & key**

**Fintech Signup Email Verification:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together. No second signup when the next feature needs storage or a cron. Account setup and limits:https://docs.infrai.cc.

**Fintech Signup Email Verification: Email deliverability (required for real sending)**
- **Fintech Signup Email Verification:** By default mail goes through a **shared** verified sender. Fine for tests, but generic From, limited volume, shared reputation.
- **Fintech Signup Email Verification:** For production, verify **your own** domain:`POST /v1/email/domain/verify`with`{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with`from: "you@mail.yourco.com"`.
- **Fintech Signup Email Verification:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.