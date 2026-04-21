from datetime import datetime

from app.analysis_context import AnalysisContext


def analysis_label(analysis: AnalysisContext, now: datetime) -> str:
    timestamp_suffix = (
        " (" + present_timestamp(analysis.create_time, now) + ")"
        if analysis.create_time is not None
        else ""
    )
    return f"{analysis.display_name}{timestamp_suffix}"


def present_timestamp(d: datetime, now: datetime):
    diff = now - d
    s = diff.seconds
    if diff.days > 7 or diff.days < 0:
        return d.strftime("%d %b %y")
    elif diff.days == 1:
        return "1 day ago"
    elif diff.days > 1:
        return "{} days ago".format(diff.days)
    elif s <= 1:
        return "just now"
    elif s < 60:
        return "{} seconds ago".format(s)
    elif s < 120:
        return "1 minute ago"
    elif s < 3600:
        return "{} minutes ago".format(s // 60)
    elif s < 7200:
        return "1 hour ago"
    else:
        return "{} hours ago".format(s // 3600)
