#!/usr/bin/env python3
import json
import os

import httpx

out: dict = {}
api_key = os.environ.get("OPENALEX_API_KEY", "")
model = os.environ.get("GEMINI_GENERATION_MODEL", "")

try:
    r = httpx.get(
        "https://api.openalex.org/works",
        params={"api_key": api_key, "per_page": 1, "search": "machine learning", "filter": "has_abstract:true"},
        timeout=45,
    )
    out["openalex_search"] = r.status_code
except Exception as exc:
    out["openalex_search"] = str(exc)[:80]

try:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    client.models.generate_content(
        model=model,
        contents='Reply JSON {"ok":true}',
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0),
    )
    out["gemini"] = {"status": "ok", "model": model}
except Exception as exc:
    out["gemini"] = {"status": "error", "model": model, "error": str(exc)[:120]}

print(json.dumps(out))
