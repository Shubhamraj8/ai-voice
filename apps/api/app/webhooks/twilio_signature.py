"""Twilio webhook request signature validation (ticket 2.02)."""

from starlette.requests import Request
from twilio.request_validator import RequestValidator

from app.config import Settings, get_settings
from app.errors import api_error

TWILIO_SIGNATURE_HEADER = "X-Twilio-Signature"


def build_validation_url(request: Request, settings: Settings) -> str:
    """URL Twilio signed — must match the public URL Twilio POSTed to."""
    path = request.url.path
    query = request.url.query
    url_path = path + (f"?{query}" if query else "")

    if settings.public_api_base_url:
        return f"{settings.public_api_base_url.rstrip('/')}{url_path}"

    forwarded_proto = request.headers.get("x-forwarded-proto")
    forwarded_host = request.headers.get("x-forwarded-host") or request.headers.get(
        "host"
    )
    if forwarded_proto and forwarded_host:
        return f"{forwarded_proto}://{forwarded_host}{url_path}"

    return str(request.url)


def validate_twilio_request(request: Request, params: dict[str, str]) -> None:
    settings = get_settings()

    if not settings.twilio_signature_validation:
        return

    if not settings.twilio_auth_token:
        raise api_error(
            403,
            "twilio_not_configured",
            "Twilio auth token is not configured",
        )

    signature = request.headers.get(TWILIO_SIGNATURE_HEADER)
    if not signature:
        raise api_error(
            403,
            "twilio_signature_missing",
            "Missing Twilio request signature",
        )

    url = build_validation_url(request, settings)
    validator = RequestValidator(settings.twilio_auth_token)
    if not validator.validate(url, params, signature):
        raise api_error(
            403,
            "twilio_signature_invalid",
            "Invalid Twilio request signature",
        )
