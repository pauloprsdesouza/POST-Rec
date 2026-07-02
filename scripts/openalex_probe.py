#!/usr/bin/env python3
import httpx
import os
import json
import sys

def probe(label, url, params=None, headers=None):
    params = dict(params or {})
    headers = dict(headers or {"Accept": "application/json"})
    try:
        r = httpx.get(url, params=params, headers=headers, timeout=45)
        rl = {
            k: r.headers.get(k)
            for k in r.headers
            if k.lower().startswith("x-ratelimit") or k.lower() == "retry-after"
        }
        print(json.dumps({
            "label": label,
            "status": r.status_code,
            "rate": rl,
            "body": r.text[:400],
        }))
    except Exception as e:
        print(json.dumps({"label": label, "error": str(e)}))

api_key = os.environ.get("OPENALEX_API_KEY", "").strip()
email = os.environ.get("OPENALEX_EMAIL", "").strip()
ua = f"POST-Rec/0.1 (OpenAlex; mailto:{email})" if email else "POST-Rec/0.1"
base = {"Accept": "application/json", "User-Agent": ua}

probe("works_simple_no_key", "https://api.openalex.org/works", {"per_page": 1}, base)
if email:
    probe("works_simple_mailto", "https://api.openalex.org/works", {"per_page": 1, "mailto": email}, base)
if api_key:
    probe("works_simple_with_key", "https://api.openalex.org/works", {"per_page": 1, "api_key": api_key}, base)

probe("topics_no_key", "https://api.openalex.org/topics", {"search": "recommender systems", "per_page": 3}, base)
if api_key:
    probe("topics_with_key", "https://api.openalex.org/topics", {"search": "recommender systems", "per_page": 3, "api_key": api_key}, base)

flt = (
    "has_abstract:true,is_retracted:false,is_paratext:false,publication_year:>2021,"
    "type:article|review|preprint|book-chapter|proceedings-article,cited_by_count:>2,"
    "primary_topic.subfield.id:1710|1702"
)
params_complex = {
    "per_page": 50,
    "filter": flt,
    "search": "Social Capital",
    "sort": "cited_by_count:desc",
}
probe("works_complex_no_key", "https://api.openalex.org/works", params_complex, base)
if api_key:
    probe("works_complex_with_key", "https://api.openalex.org/works", {**params_complex, "api_key": api_key}, base)

print("ENV_OPENALEX_API_KEY_SET", bool(api_key), file=sys.stderr)
print("ENV_OPENALEX_EMAIL", email or "(empty)", file=sys.stderr)
