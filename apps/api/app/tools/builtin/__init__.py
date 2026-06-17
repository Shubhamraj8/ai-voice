"""Built-in tools. Importing this package registers them (ticket 4.08+)."""

from app.tools.builtin import (
    escalate,  # noqa: F401  (registers escalateToOwner)
    sms,  # noqa: F401  (registers sendSms)
    transfer,  # noqa: F401  (registers transferToHuman)
)

__all__ = ["escalate", "sms", "transfer"]
