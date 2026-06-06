"""Safe Twilio webhook payload fields for structured logs."""

VOICE_LOG_FIELDS = frozenset(
    {
        "CallSid",
        "AccountSid",
        "From",
        "To",
        "CallStatus",
        "Direction",
        "ForwardedFrom",
        "CallerName",
        "ApiVersion",
    }
)

STATUS_LOG_FIELDS = frozenset(
    {
        "CallSid",
        "AccountSid",
        "From",
        "To",
        "CallStatus",
        "CallDuration",
        "Duration",
        "RecordingUrl",
        "RecordingSid",
        "Timestamp",
        "SequenceNumber",
        "ParentCallSid",
        "Direction",
    }
)


def twilio_payload_for_log(
    params: dict[str, str], *, fields: frozenset[str]
) -> dict[str, str]:
    return {key.lower(): value for key, value in params.items() if key in fields}
