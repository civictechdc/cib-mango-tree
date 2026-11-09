"""Compare-users helpers (ported from cib-time-analysis stepper_compare)."""

from __future__ import annotations

from dateutil import parser


def format_post_body(content, raw_time) -> str:
    """Put separate date and time lines above the post text."""
    text = str(raw_time).strip()
    body = str(content)
    if not text:
        return body
    try:
        dt = parser.parse(text)
    except (TypeError, ValueError, OverflowError):
        # Already a datetime-like, or unparseable string.
        if hasattr(raw_time, "strftime"):
            return (
                f"{raw_time.strftime('%Y-%m-%d')}\n"
                f"{raw_time.strftime('%H:%M:%S')}\n\n{body}"
            )
        return f"{text}\n\n{body}"
    return f"{dt.strftime('%Y-%m-%d')}\n{dt.strftime('%H:%M:%S')}\n\n{body}"
