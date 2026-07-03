"""HTML and plain-text templates for run notification emails."""

from html import escape

from apps.api.features.auth.email_templates import (
    _BG,
    _BORDER,
    _MUTED,
    _PRIMARY,
    _PRIMARY_DARK,
    _SURFACE,
    _TEXT,
    _TEXT_SECONDARY,
)

_SUCCESS = "#047857"
_SUCCESS_BG = "#ecfdf5"
_SUCCESS_BORDER = "#6ee7b7"
_DANGER = "#b91c1c"
_DANGER_BG = "#fef2f2"
_DANGER_BORDER = "#fca5a5"


def _cta_button(label: str, url: str) -> str:
    safe_label = escape(label)
    safe_url = escape(url, quote=True)
    return (
        f'<a href="{safe_url}" style="display:inline-block;margin:24px 0 8px;padding:14px 28px;'
        f"background:{_PRIMARY};color:#ffffff;text-decoration:none;border-radius:10px;"
        f'font-size:15px;font-weight:600;">{safe_label}</a>'
    )


def _email_shell(*, app_name: str, badge: str, title: str, body_html: str, accent: str) -> str:
    safe_app = escape(app_name)
    safe_badge = escape(badge)
    safe_title = escape(title)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{safe_title}</title>
</head>
<body style="margin:0;padding:0;background-color:{_BG};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:{_TEXT};">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color:{_BG};">
    <tr>
      <td align="center" style="padding:40px 16px;">
        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="max-width:520px;background-color:{_SURFACE};border-radius:16px;border:1px solid {_BORDER};overflow:hidden;box-shadow:0 4px 24px rgba(15,23,42,0.08);">
          <tr>
            <td style="background:linear-gradient(135deg,{accent} 0%,{_PRIMARY_DARK} 100%);padding:28px 32px;text-align:center;">
              <p style="margin:0 0 6px;font-size:13px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:rgba(255,255,255,0.88);">{safe_badge}</p>
              <h1 style="margin:0;font-size:22px;font-weight:700;line-height:1.35;color:#ffffff;">{safe_title}</h1>
            </td>
          </tr>
          <tr>
            <td style="padding:32px 32px 28px;text-align:center;">
              {body_html}
              <p style="margin:24px 0 0;font-size:12px;line-height:1.5;color:{_MUTED};">&copy; {safe_app}</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def render_run_completed_email(
    *,
    app_name: str,
    recommendation_count: int,
    topic_line: str,
    app_url: str,
    run_url: str,
) -> tuple[str, str, str]:
    subject = f"{app_name}: Your recommendations are ready"
    plain = (
        f"{app_name}: Your recommendations are ready!\n\n"
        f"{recommendation_count} research ideas generated.\n"
        f"Topics: {topic_line}\n\n"
        f"Open the app to review: {run_url}"
    )

    safe_topics = escape(topic_line)
    body_html = (
        f'<p style="margin:0 0 16px;font-size:16px;line-height:1.6;color:{_TEXT_SECONDARY};">'
        f"<strong style=\"color:{_TEXT};\">{recommendation_count}</strong> research ideas are ready for you."
        f"</p>"
        f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" '
        f'style="background:{_SUCCESS_BG};border:1px solid {_SUCCESS_BORDER};border-radius:12px;margin:0 0 8px;">'
        f'<tr><td style="padding:14px 16px;font-size:14px;line-height:1.55;color:{_SUCCESS};text-align:left;">'
        f"<strong>Topics:</strong> {safe_topics}"
        f"</td></tr></table>"
        f"{_cta_button('Review recommendations', run_url)}"
        f'<p style="margin:16px 0 0;font-size:13px;line-height:1.5;color:{_MUTED};">Or open {escape(app_name)} at {escape(app_url)}</p>'
    )
    html = _email_shell(
        app_name=app_name,
        badge="Run complete",
        title="Your recommendations are ready",
        body_html=body_html,
        accent=_SUCCESS,
    )
    return subject, plain, html


def render_run_failed_email(
    *,
    app_name: str,
    error_message: str,
    app_url: str,
    runs_url: str,
) -> tuple[str, str, str]:
    subject = f"{app_name}: Recommendation run could not be completed"
    plain = (
        f"{app_name}: Your recommendation run could not be completed.\n\n"
        f"Reason: {error_message}\n\n"
        f"Open the app to try again: {runs_url}"
    )

    safe_error = escape(error_message)
    body_html = (
        f'<p style="margin:0 0 16px;font-size:16px;line-height:1.6;color:{_TEXT_SECONDARY};">'
        f"We couldn't finish generating your recommendations."
        f"</p>"
        f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" '
        f'style="background:{_DANGER_BG};border:1px solid {_DANGER_BORDER};border-radius:12px;margin:0 0 8px;">'
        f'<tr><td style="padding:14px 16px;font-size:14px;line-height:1.55;color:{_DANGER};text-align:left;">'
        f"<strong>Reason:</strong> {safe_error}"
        f"</td></tr></table>"
        f"{_cta_button('Try again', runs_url)}"
        f'<p style="margin:16px 0 0;font-size:13px;line-height:1.5;color:{_MUTED};">Or open {escape(app_name)} at {escape(app_url)}</p>'
    )
    html = _email_shell(
        app_name=app_name,
        badge="Run failed",
        title="We couldn't complete your run",
        body_html=body_html,
        accent=_DANGER,
    )
    return subject, plain, html
