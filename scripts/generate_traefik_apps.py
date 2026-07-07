#!/usr/bin/env python3
"""Generate Traefik routing, landing page, and 404 page from deploy/apps/registry.json."""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = PROJECT_ROOT / "deploy" / "apps" / "registry.json"
LANDING_TEMPLATE = PROJECT_ROOT / "deploy" / "landing" / "index.template.html"
UNKNOWN_TEMPLATE = PROJECT_ROOT / "deploy" / "unknown-app" / "index.template.html"


def load_registry(path: Path = REGISTRY_PATH) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not data or "domain" not in data or "apps" not in data:
        raise ValueError(f"Invalid registry: {path}")
    return data


def landing_config(reg: dict) -> dict:
    return reg.get("landing") or {}


def show_apps_on_landing(reg: dict, apps: dict) -> bool:
    if not landing_config(reg).get("show_apps", False):
        return False
    return any(app.get("list_publicly", True) for app in apps.values())


def publicly_listed_apps(apps: dict) -> dict:
    return {name: app for name, app in apps.items() if app.get("list_publicly", True)}


def app_links_html(apps: dict, *, base_url: str = "") -> str:
    items = []
    for name, app in sorted(apps.items()):
        path = app.get("base_path", f"/{name}")
        title = html.escape(app.get("title", name))
        desc = html.escape(app.get("description", ""))
        href = html.escape(f"{base_url}{path}")
        items.append(
            f'    <li><a class="app" href="{href}"><strong>{title}</strong>'
            f"<span>{desc}</span></a></li>"
        )
    return "\n".join(items)


def apps_section_html(apps: dict) -> str:
    if not apps:
        return ""
    links = app_links_html(apps)
    return (
        '  <p class="lead">Published applications</p>\n'
        "  <style>\n"
        "    ul { list-style: none; padding: 0; }\n"
        "    li { margin: 0.75rem 0; }\n"
        "    a.app {\n"
        "      display: block; padding: 1rem 1.25rem; border: 1px solid #ccc; border-radius: 8px;\n"
        "      text-decoration: none; color: inherit;\n"
        "    }\n"
        "    a.app:hover { border-color: #888; }\n"
        "    a.app strong { display: block; }\n"
        "    a.app span { font-size: 0.9rem; color: #666; }\n"
        "  </style>\n"
        "  <ul>\n"
        f"{links}\n"
        "  </ul>"
    )


def generate_landing(domain: str, reg: dict, apps: dict) -> str:
    landing = landing_config(reg)
    tagline = html.escape(landing.get("tagline", ""))
    listed = publicly_listed_apps(apps) if show_apps_on_landing(reg, apps) else {}

    if LANDING_TEMPLATE.is_file():
        content = LANDING_TEMPLATE.read_text(encoding="utf-8")
        tagline_block = f'  <p class="lead">{tagline}</p>\n' if tagline else ""
        return (
            content.replace("<!-- DOMAIN -->", html.escape(domain))
            .replace("<!-- TAGLINE_BLOCK -->", tagline_block)
            .replace("<!-- APPS_SECTION -->", apps_section_html(listed))
        )

    links = app_links_html(listed)
    apps_block = (
        f'  <p class="lead">Published applications</p>\n  <ul>\n{links}\n  </ul>'
        if listed
        else ""
    )
    tagline_block = f'  <p class="lead">{tagline}</p>\n' if tagline else ""
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="robots" content="noindex, nofollow" />
  <title>{html.escape(domain)}</title>
  <style>
    :root {{ color-scheme: light dark; font-family: system-ui, sans-serif; }}
    body {{ max-width: 42rem; margin: 4rem auto; padding: 0 1.5rem; line-height: 1.6; }}
    h1 {{ font-size: 1.75rem; margin-bottom: 0.25rem; }}
    p.lead {{ color: #666; margin-top: 0; }}
  </style>
</head>
<body>
  <h1>{html.escape(domain)}</h1>
{tagline_block}{apps_block}
</body>
</html>
"""


def generate_unknown_page(reg: dict, apps: dict) -> str:
    listed = publicly_listed_apps(apps) if show_apps_on_landing(reg, apps) else {}
    apps_section = ""
    if listed:
        links = "\n".join(
            f'    <li><a href="{html.escape(app.get("base_path", f"/{name}"))}">'
            f'{html.escape(app.get("title", name))}</a></li>'
            for name, app in sorted(listed.items())
        )
        apps_section = f'  <p>Available apps:</p>\n  <ul>\n{links}\n  </ul>'

    if UNKNOWN_TEMPLATE.is_file():
        content = UNKNOWN_TEMPLATE.read_text(encoding="utf-8")
        return content.replace("<!-- APPS_SECTION -->", apps_section)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="robots" content="noindex, nofollow" />
  <title>Not found</title>
</head>
<body>
  <h1>Not found</h1>
  <p>The page you requested does not exist.</p>
{apps_section}
</body>
</html>
"""


def _middlewares(*names: str) -> list[str]:
    return [name for name in names if name]


def _middleware_line(names: list[str]) -> list[str]:
    if not names:
        return []
    return [f"      middlewares: [{', '.join(names)}]"]


def generate_traefik(domain: str, apps: dict) -> str:
    hosts = f"Host(`{domain}`) || Host(`www.{domain}`)"
    lines = [
        "# Auto-generated from deploy/apps/registry.json — do not edit manually.",
        "# Re-run: python scripts/generate_traefik_apps.py --write",
        "",
        "http:",
        "  routers:",
    ]

    for name, app in apps.items():
        base = app.get("base_path", f"/{name}").rstrip("/")
        svc = f"app-{name}"
        app_middlewares = _middlewares(
            "redirect-to-https",
            f"strip-{name}" if app.get("strip_prefix") else None,
        )
        https_middlewares = _middlewares(
            "security-headers",
            f"strip-{name}" if app.get("strip_prefix") else None,
        )
        http_block = [
            f"    {name}-http:",
            f"      rule: ({hosts}) && PathPrefix(`{base}`)",
            "      entryPoints: [http]",
            *_middleware_line(app_middlewares),
            f"      service: {svc}",
            "      priority: 100",
            "",
        ]

        https_block = [
            f"    {name}-https:",
            f"      rule: ({hosts}) && PathPrefix(`{base}`)",
            "      entryPoints: [https]",
            *_middleware_line(https_middlewares),
            f"      service: {svc}",
            "      tls:",
            "        certResolver: letsencrypt",
            "      priority: 100",
            "",
        ]
        lines.extend(http_block + https_block)

        for i, root_path in enumerate(app.get("root_paths") or []):
            rp = root_path.rstrip("/") or root_path
            rule_path = f"PathPrefix(`{rp}`)"
            rid = f"{name}-root{i}"
            for suffix, entrypoints, tls_lines, middlewares in [
                ("-http", ["http"], [], _middlewares("redirect-to-https")),
                (
                    "-https",
                    ["https"],
                    ["      tls:", "        certResolver: letsencrypt"],
                    _middlewares("security-headers"),
                ),
            ]:
                root_block = [
                    f"    {rid}{suffix}:",
                    f"      rule: ({hosts}) && {rule_path}",
                    f"      entryPoints: [{', '.join(entrypoints)}]",
                    *_middleware_line(middlewares),
                    f"      service: {svc}",
                    "      priority: 105",
                    *tls_lines,
                    "",
                ]
                lines.extend(root_block)

    for suffix, entrypoints, tls_lines, middlewares in [
        ("-http", ["http"], [], _middlewares("redirect-to-https")),
        ("-https", ["https"], ["      tls:", "        certResolver: letsencrypt"], _middlewares("security-headers")),
    ]:
        lines.extend(
            [
                f"    www-redirect{suffix}:",
                f"      rule: Host(`www.{domain}`)",
                f"      entryPoints: [{', '.join(entrypoints)}]",
                "      middlewares: [www-to-apex]",
                "      service: noop",
                "      priority: 90",
                *tls_lines,
                "",
            ]
        )

    for suffix, entrypoints, tls_lines, middlewares in [
        ("-http", ["http"], [], _middlewares("redirect-to-https")),
        ("-https", ["https"], ["      tls:", "        certResolver: letsencrypt"], _middlewares("security-headers")),
    ]:
        lines.extend(
            [
                f"    landing{suffix}:",
                f"      rule: Host(`{domain}`) && Path(`/`)",
                f"      entryPoints: [{', '.join(entrypoints)}]",
                *_middleware_line(middlewares),
                "      service: landing",
                "      priority: 80",
                *tls_lines,
                "",
            ]
        )

    excludes = " && ".join(
        f"!PathPrefix(`{app.get('base_path', f'/{name}').rstrip('/')}`)" for name, app in apps.items()
    )
    root_excludes = " && ".join(
        f"!PathPrefix(`{rp}`)"
        for app in apps.values()
        for rp in (app.get("root_paths") or [])
    )
    if root_excludes:
        excludes = f"{excludes} && {root_excludes}" if excludes else root_excludes
    unknown_rule = (
        f"({hosts}) && PathPrefix(`/`) && !Path(`/`) && {excludes}"
        if excludes
        else f"({hosts}) && PathPrefix(`/`) && !Path(`/`)"
    )
    for suffix, entrypoints, tls_lines, middlewares in [
        ("-http", ["http"], [], _middlewares("redirect-to-https")),
        ("-https", ["https"], ["      tls:", "        certResolver: letsencrypt"], _middlewares("security-headers")),
    ]:
        lines.extend(
            [
                f"    unknown-app{suffix}:",
                f"      rule: {unknown_rule}",
                f"      entryPoints: [{', '.join(entrypoints)}]",
                *_middleware_line(middlewares),
                "      service: unknown-app",
                "      priority: 50",
                *tls_lines,
                "",
            ]
        )

    domain_escaped = domain.replace(".", "\\.")
    strip_lines: list[str] = []
    for name, app in apps.items():
        if app.get("strip_prefix"):
            base = app.get("base_path", f"/{name}").rstrip("/")
            strip_lines.extend(
                [
                    f"    strip-{name}:",
                    "      stripPrefix:",
                    "        prefixes:",
                    f"          - {base}",
                    "",
                ]
            )
    lines.extend(
        [
            "  middlewares:",
            *strip_lines,
            "    redirect-to-https:",
            "      redirectScheme:",
            "        scheme: https",
            "        permanent: true",
            "",
            "    security-headers:",
            "      headers:",
            "        browserXssFilter: true",
            "        contentTypeNosniff: true",
            "        frameDeny: true",
            "        referrerPolicy: strict-origin-when-cross-origin",
            "        permissionsPolicy: camera=(), microphone=(), geolocation=()",
            "        stsSeconds: 31536000",
            "        stsIncludeSubdomains: true",
            "        stsPreload: true",
            "",
            "    www-to-apex:",
            "      redirectRegex:",
            f"        regex: '^https?://www\\.{domain_escaped}/(.*)'",
            f'        replacement: "https://{domain}/${{1}}"',
            "        permanent: true",
            "",
            "  services:",
        ]
    )

    for name, app in apps.items():
        host = app["service_host"]
        port = app.get("service_port", 80)
        lines.extend(
            [
                f"    app-{name}:",
                "      loadBalancer:",
                "        servers:",
                f"          - url: http://{host}:{port}",
                "",
            ]
        )

    lines.extend(
        [
            "    landing:",
            "      loadBalancer:",
            "        servers:",
            "          - url: http://postrec-landing:80",
            "",
            "    unknown-app:",
            "      loadBalancer:",
            "        servers:",
            "          - url: http://postrec-unknown-app:80",
            "",
            "    noop:",
            "      loadBalancer:",
            "        servers:",
            "          - url: http://127.0.0.1:9",
            "",
        ]
    )
    return "\n".join(lines)


def generate_traefik_static(domain: str) -> str:
    return f"""# Auto-generated static Traefik config — do not edit manually.
# Re-run: python scripts/generate_traefik_apps.py --write

api:
  dashboard: false

log:
  level: INFO

entryPoints:
  http:
    address: ":80"
  https:
    address: ":443"

providers:
  file:
    directory: /etc/traefik/dynamic
    watch: true

certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@{domain}
      storage: /etc/traefik/acme/acme.json
      httpChallenge:
        entryPoint: http
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=REGISTRY_PATH)
    parser.add_argument("--write", action="store_true", help="Write generated files to deploy/")
    args = parser.parse_args()

    reg = load_registry(args.registry)
    domain = reg["domain"]
    apps = reg["apps"]

    traefik = generate_traefik(domain, apps)
    traefik_static = generate_traefik_static(domain)
    landing = generate_landing(domain, reg, apps)
    unknown = generate_unknown_page(reg, apps)

    if args.write:
        out_traefik = PROJECT_ROOT / "deploy" / "traefik" / "apps.yaml"
        out_static = PROJECT_ROOT / "deploy" / "traefik" / "traefik.yml"
        out_landing = PROJECT_ROOT / "deploy" / "landing" / "index.html"
        out_unknown = PROJECT_ROOT / "deploy" / "unknown-app" / "index.html"
        out_traefik.write_text(traefik.replace("\r\n", "\n"), encoding="utf-8", newline="\n")
        out_static.write_text(traefik_static.replace("\r\n", "\n"), encoding="utf-8", newline="\n")
        out_landing.write_text(landing, encoding="utf-8", newline="\n")
        out_unknown.write_text(unknown, encoding="utf-8", newline="\n")
        print(f"Wrote {out_traefik}")
        print(f"Wrote {out_static}")
        print(f"Wrote {out_landing}")
        print(f"Wrote {out_unknown}")
    else:
        sys.stdout.write(traefik)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
