"""HTML and plain-text templates for transactional auth emails."""

from html import escape

# Researchly brand tokens (apps/web/src/shared/styles/_tokens.scss)
_PRIMARY = "#4338ca"
_PRIMARY_DARK = "#312e81"
_PRIMARY_LIGHT = "#eef2ff"
_BG = "#e8eaef"
_SURFACE = "#ffffff"
_TEXT = "#0f172a"
_TEXT_SECONDARY = "#334155"
_MUTED = "#64748b"
_BORDER = "#e2e8f0"
_WARNING_BG = "#fffbeb"
_WARNING_BORDER = "#fcd34d"
_WARNING_TEXT = "#92400e"


def _otp_digits_html(code: str) -> str:
    cells = []
    for digit in code:
        cells.append(
            f'<td style="width:44px;height:52px;text-align:center;vertical-align:middle;'
            f"background:{_PRIMARY_LIGHT};border:1px solid #c7d2fe;border-radius:10px;"
            f"font-family:Consolas,Monaco,monospace;font-size:28px;font-weight:700;"
            f'color:{_PRIMARY_DARK};letter-spacing:0;">{escape(digit)}</td>'
        )
        cells.append('<td style="width:8px;font-size:0;line-height:0;">&nbsp;</td>')
    if cells:
        cells.pop()  # trailing spacer
    return (
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
        'style="margin:0 auto;border-collapse:separate;border-spacing:0;">'
        f"<tr>{''.join(cells)}</tr></table>"
    )


def render_otp_email(
    *,
    app_name: str,
    code: str,
    ttl_minutes: int,
    purpose: str = "login",
) -> tuple[str, str]:
    """Return plain-text and HTML bodies for an OTP email."""
    action = "sign in" if purpose == "login" else "complete your registration"
    subject_line = f"{app_name} sign-in code"

    plain = (
        f"{app_name} sign-in code: {code}.\n"
        f"Valid for {ttl_minutes} minutes. Do not share this code.\n\n"
        f"If you did not request this code, you can safely ignore this email."
    )

    safe_app = escape(app_name)
    safe_code = escape(code)
    digits_html = _otp_digits_html(code)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(subject_line)}</title>
</head>
<body style="margin:0;padding:0;background-color:{_BG};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:{_TEXT};">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color:{_BG};">
    <tr>
      <td align="center" style="padding:40px 16px;">
        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="max-width:520px;background-color:{_SURFACE};border-radius:16px;border:1px solid {_BORDER};overflow:hidden;box-shadow:0 4px 24px rgba(15,23,42,0.08);">
          <tr>
            <td style="background:linear-gradient(135deg,{_PRIMARY} 0%,{_PRIMARY_DARK} 100%);padding:28px 32px;text-align:center;">
              <p style="margin:0 0 6px;font-size:13px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:rgba(255,255,255,0.82);">Verification</p>
              <h1 style="margin:0;font-size:24px;font-weight:700;line-height:1.3;color:#ffffff;">{safe_app}</h1>
            </td>
          </tr>
          <tr>
            <td style="padding:32px 32px 8px;text-align:center;">
              <p style="margin:0 0 8px;font-size:16px;line-height:1.5;color:{_TEXT_SECONDARY};">
                Use this code to {action}:
              </p>
              <div style="margin:24px 0 8px;">
                {digits_html}
              </div>
              <p style="margin:12px 0 0;font-family:Consolas,Monaco,monospace;font-size:14px;color:{_MUTED};letter-spacing:0.12em;">
                {safe_code}
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:8px 32px 24px;text-align:center;">
              <p style="margin:0;font-size:14px;line-height:1.6;color:{_MUTED};">
                This code expires in <strong style="color:{_TEXT};">{ttl_minutes} minutes</strong>.
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:0 32px 32px;">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color:{_WARNING_BG};border:1px solid {_WARNING_BORDER};border-radius:12px;">
                <tr>
                  <td style="padding:14px 16px;font-size:13px;line-height:1.55;color:{_WARNING_TEXT};text-align:center;">
                    Never share this code with anyone. {safe_app} will never ask for it by phone or message.
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:20px 32px 28px;border-top:1px solid {_BORDER};text-align:center;">
              <p style="margin:0 0 6px;font-size:12px;line-height:1.5;color:{_MUTED};">
                If you did not request this code, you can safely ignore this email.
              </p>
              <p style="margin:0;font-size:12px;line-height:1.5;color:{_MUTED};">
                &copy; {safe_app}
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    return plain, html
