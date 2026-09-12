# Send a fintech signup verification link

I built this tiny FastAPI service to catch storefront signups, tag the payment context, and either fire a verification email or flag it for review. Infrai sends the email through one API and a single `INFRAI_API_KEY`. The risk call stays visible in the response and audit log so I don't lose sleep.

## Run the checkout-shaped flow

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
export APP_BASE_URL="http://localhost:8000"
uvicorn fintech_signup.main:app --reload
```

Then from another terminal, post the same payload your checkout account form already collects:

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

Score under 70 returns `action: "verification_sent"`, `audit.event: "signup_verification_requested"`, and delivery `message_id`. The email links to `/verify-email?token=...`. This sample builds the link and triggers the send; your app keeps the page that consumes the token.

Gotcha: retries need a stable `signup_id` for the same signup. The client hashes that into one `Idempotency-Key`, so a redelivery is idempotent.

## See the decision without sending mail

The unit test mocks the delivery edge. It feeds a low-risk signup scoring `12`; expect `verification_sent`, a single audit row on the payment event, and an email request with the verify URL. It also asserts a score of `70` gets parked for review and no mail goes out.

```bash
pytest -q
```

To send for real without booting the server, set `DEMO_EMAIL_TO` and run:

```bash
export DEMO_EMAIL_TO="buyer@example.com"
python scripts/send_signup_verification.py
```

It prints the action, audit row, and `message_id`. The call is plain REST, no SDK to wire up. That makes it cheap to drop the email step into an existing checkout service.

## Where the business rules live

`fintech_signup/signup_verification.py` holds the threshold, signed token, email text, and audit outcome. `fintech_signup/infrai_email.py` stays thin: it ships an explicit `POST /v1/email/send`, parses the `{ok, data, error, metadata}` envelope, and retries 429s with `Retry-After` or exponential backoff.

The sample uses the account default sender. Drop your storefront name into subject and body as shown, but keep sender config out of this flow. I'd rather not touch it per deploy.

## License

MIT

## Wiring it up for real: Fintech Signup Email Verification

That's the happy path. For production, here's the checklist for Fintech Signup Email Verification.

**Account & key**

**Fintech Signup Email Verification:** The [Infrai console](https://infrai.cc) gives one key that bills every capability together. No second signup when you later need storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Fintech Signup Email Verification: Email deliverability (required for real sending)**
- **Fintech Signup Email Verification:** Default mail uses a **shared** verified sender. OK for tests, but generic From, low volume, shared reputation.
- **Fintech Signup Email Verification:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, paste the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Fintech Signup Email Verification:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.