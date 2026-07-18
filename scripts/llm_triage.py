#!/usr/bin/env python3
"""Optional LLM relevance-triage for the literature radar — 3-provider fallback.

Ported from the owner's dreamcatcher `ai-worker` (tela-aurea-ai-worker): the same
resilient chain **NVIDIA NIM → Groq → Cloudflare → (fail-open)**, the same env-var
names, the same robust JSON parsing. Here it scores whether a paper could UPDATE a
figure the brain-exposome map uses, instead of writing a healing message.

Stdlib only (urllib) — no pip in CI. **Fail-open**: if no keys are set, or every
tier errors, `triage()` returns None and the caller keeps the candidate. So the
literature radar always produces output; the LLM only *ranks/filters* it.

Env (copy from the dreamcatcher .env; set as GitHub Actions secrets):
  NVIDIA_API_KEY            tier 1 (NIM)     + optional NIM_MODEL
  GROQ_API_KEY             tier 2 (Groq)    + optional GROQ_MODEL   (GroqCloud_API_KEY also accepted)
  CF_ACCOUNT_ID + CF_API_TOKEN   tier 3 (Cloudflare Workers AI via REST) + optional CF_AI_MODEL
"""
import json
import os
import re
import urllib.error
import urllib.request

TIMEOUT = 40

RUBRIC = (
    "You triage scientific papers for a brain-health data map. Decide whether this paper could "
    "UPDATE a figure the map uses: national or global PREVALENCE of dementia, mild cognitive impairment "
    "(MCI), or subjective cognitive decline (SCD); the dementia risk from PM2.5 / air pollution; "
    "population ageing (65+); or the global prevalence of hypertension, diabetes, obesity, smoking, or "
    "physical inactivity. KEEP only papers that plausibly provide a new NUMBER we could ingest "
    "(a prevalence/incidence estimate, a meta-analysis, a new Lancet Commission, or new demographic "
    "projections). DROP narrow clinical, mechanistic, single-cohort, or bibliometric papers. "
    'Reply with JSON only: {"verdict":"keep"|"drop","reason":"<=4 words"}.'
)


def _messages(title, abstract):
    return [
        {"role": "system", "content": RUBRIC},
        {"role": "user", "content": f"TITLE: {title}\n\nABSTRACT: {abstract or '(none)'}"},
    ]


def _post(url, headers, payload):
    req = urllib.request.Request(
        url, json.dumps(payload).encode("utf-8"),
        {**headers, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


# ── providers: return a verdict dict, or None if unconfigured ──
def _nim(title, abstract, env):
    key = env.get("NVIDIA_API_KEY")
    if not key:
        return None
    d = _post("https://integrate.api.nvidia.com/v1/chat/completions",
              {"Authorization": f"Bearer {key}"},
              {"model": env.get("NIM_MODEL", "meta/llama-3.1-8b-instruct"),
               "messages": _messages(title, abstract), "temperature": 0.1,
               "max_tokens": 60, "response_format": {"type": "json_object"}})
    return _parse(d["choices"][0]["message"]["content"])


def _groq(title, abstract, env):
    key = env.get("GROQ_API_KEY") or env.get("GroqCloud_API_KEY")
    if not key:
        return None
    d = _post("https://api.groq.com/openai/v1/chat/completions",
              {"Authorization": f"Bearer {key}"},
              {"model": env.get("GROQ_MODEL", "llama-3.1-8b-instant"),
               "messages": _messages(title, abstract), "temperature": 0.1,
               "max_tokens": 60, "response_format": {"type": "json_object"}})
    return _parse(d["choices"][0]["message"]["content"])


def _cloudflare(title, abstract, env):
    acct, tok = env.get("CF_ACCOUNT_ID"), env.get("CF_API_TOKEN")
    if not (acct and tok):
        return None
    model = env.get("CF_AI_MODEL", "@cf/meta/llama-3.3-70b-instruct-fp8-fast")
    d = _post(f"https://api.cloudflare.com/client/v4/accounts/{acct}/ai/run/{model}",
              {"Authorization": f"Bearer {tok}"},
              {"messages": _messages(title, abstract), "max_tokens": 60})
    return _parse(d.get("result", {}).get("response"))


TIERS = [_nim, _groq, _cloudflare]   # dreamcatcher order: NIM → Groq → Cloudflare


def available(env=None):
    e = env or os.environ
    return bool(e.get("NVIDIA_API_KEY")
                or e.get("GROQ_API_KEY") or e.get("GroqCloud_API_KEY")
                or (e.get("CF_ACCOUNT_ID") and e.get("CF_API_TOKEN")))


def triage(title, abstract="", env=None):
    """Return {'verdict','reason','tier'} from the first working provider, or None (fail-open)."""
    e = env or os.environ
    for fn in TIERS:
        try:
            v = fn(title, abstract, e)
            if v:
                v["tier"] = fn.__name__.lstrip("_")
                return v
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError, KeyError, TimeoutError):
            continue
    return None


def _parse(content):
    if content is None:
        return None
    if isinstance(content, dict):
        return {"verdict": content["verdict"], "reason": content.get("reason", "")} if content.get("verdict") else None
    m = re.search(r"\{[\s\S]*\}", str(content))
    if m:
        try:
            o = json.loads(m.group(0))
            if o.get("verdict"):
                return {"verdict": o["verdict"], "reason": o.get("reason", "")}
        except ValueError:
            pass
    return None
