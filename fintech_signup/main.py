from fastapi import FastAPI

from .infrai_email import InfraiEmail
from .signup_verification import SignupRequest, SignupResult, environment_settings, process_signup

app = FastAPI(title="Checkout email verification")


@app.post("/signups", response_model=SignupResult)
def create_signup(request: SignupRequest) -> SignupResult:
    base_url, signing_secret = environment_settings()
    return process_signup(request, InfraiEmail(), base_url, signing_secret)
