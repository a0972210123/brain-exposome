#!/usr/bin/env python3
"""Optional LLM relevance-triage for the literature radar — 3-provider fallback.

Ported from the owner's dreamcatcher `ai-worker` (tela-aurea-ai-worker): the same
resilient chain **NVIDIA NIM → Groq → Cloudflare → (fail-open)**, the same env-var
names, the same robust JSON parsing. Here it scores whether a paper could UPDATE a
figure the brain-exposome map uses, instead of writing a healing message.

Stdlib only (urllib) — no pip in CI. **Fail-open**: if no keys are set, or every
tier errors, `triage()` returns None and the caller keeps the candidate. So the
literature radar always produces output; the LLM only *ranks/filters* it.

**Model ids are not pinned.** They rot on the provider's schedule, silently: Groq
retired every Llama in 2026-08, so the id this file used to hardcode
(`llama-3.1-8b-instant`) now 404s. In a monthly cron that fails open nobody would
have noticed — the report would still have said "LLM-triaged" while filtering
nothing. So each tier asks its provider what it serves *today*, and the verdict
carries the model that produced it so the report can name it.

Env (copy from the dreamcatcher .env; set as GitHub Actions secrets):
  NVIDIA_API_KEY            tier 1 (NIM)     + optional NIM_MODEL
  GROQ_API_KEY             tier 2 (Groq)    + optional GROQ_MODEL   (GroqCloud_API_KEY also accepted)
  CF_ACCOUNT_ID + CF_API_TOKEN   tier 3 (Cloudflare Workers AI via REST) + optional CF_AI_MODEL
The optional *_MODEL vars pin one id and skip discovery — for reproducing an old
run, not as the normal path.
"""
import json
import os
import re
import urllib.error
import urllib.request

TIMEOUT = 40

# Groq's edge rejects urllib's default `Python-urllib/3.x` with 403 on BOTH
# /models and /chat/completions — measured 2026-08-19, and it is not about the
# key: the same key over an explicit UA returns 200. Without this header the Groq
# tier could never have worked from CI no matter which model id was configured.
UA = "brain-exposome-literature-watch/1.0 (+https://github.com/matt-ye/brain-exposome)"

# The verdict is ~20 tokens, but the budget is not for the verdict. Every model
# still on Groq's roster in 2026-08 reasons before answering, and the reasoning
# spends this allowance first: gpt-oss-20b at 60 returns content='' with
# finish_reason='length' (or a 400 in JSON mode) and answers correctly at 300.
# max_tokens is a ceiling, not a bill, so the non-reasoning tiers pay nothing for
# the headroom.
MAX_TOKENS = 400

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
        {**headers, "Content-Type": "application/json", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def _get(url, headers):
    req = urllib.request.Request(url, headers={**headers, "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


# ── model discovery ───────────────────────────────────────────────────
# One list call per provider per process. `triage()` runs once per paper, so
# re-listing each time would turn a 40-paper run into 120 extra requests.
_OVERRIDE_VAR = {"nim": "NIM_MODEL", "groq": "GROQ_MODEL", "cf": "CF_AI_MODEL"}
_model_cache = {}

# Patterns, not ids — a pinned id dies the day the provider retires it, a pattern
# survives the version bump that replaces it. Ordered best-first per provider.
_PREFER = {
    # No qwen here on purpose: qwen3.6-27b writes its <think> block straight into
    # `content` and never reaches the JSON, even at max_tokens=800 (measured
    # 2026-08-19). It is not a budget problem, so no budget fixes it.
    "groq": [r"gpt-oss-20b$", r"gpt-oss-120b$"],
    "nim": [r"^meta/llama-3\.1-8b-instruct$", r"^nvidia/.*nemotron.*(9|12)b", r"^mistralai/.*small"],
    "cf": [r"llama.*3\.3.*70b", r"llama.*4", r"qwen.*(32|72)b"],
}
# Non-chat models that share the flat /v1/models list on NIM and Groq: speech,
# embeddings, rerankers, safety classifiers, vision, and Groq's tool-using
# compound systems (far too expensive for a one-line keep/drop verdict).
_EXCLUDE = (r"whisper|orpheus|embed|bge-|rerank|guard|safeguard|moderation"
            r"|vision|ocr|kosmos|deplot|diffusion|compound")


def list_models(provider, env):
    """Ids the provider serves right now, in the provider's own listing order.

    Only Cloudflare can filter by task server-side; NIM and Groq return one flat
    list that also holds embeddings, vision, speech and guard models. That
    asymmetry is why `choose_model` cannot simply take ids[0].
    """
    if provider in _model_cache:
        return _model_cache[provider]

    if provider == "nim":
        d = _get("https://integrate.api.nvidia.com/v1/models",
                 {"Authorization": f"Bearer {env.get('NVIDIA_API_KEY')}"})
        ids = [m.get("id") for m in d.get("data") or []]
    elif provider == "groq":
        key = env.get("GROQ_API_KEY") or env.get("GroqCloud_API_KEY")
        d = _get("https://api.groq.com/openai/v1/models", {"Authorization": f"Bearer {key}"})
        ids = [m.get("id") for m in d.get("data") or []]
    else:  # cf
        d = _get(f"https://api.cloudflare.com/client/v4/accounts/{env.get('CF_ACCOUNT_ID')}"
                 "/ai/models/search?task=Text%20Generation&hide_experimental=true&per_page=100",
                 {"Authorization": f"Bearer {env.get('CF_API_TOKEN')}"})
        ids = [m.get("name") for m in d.get("result") or []]

    ids = [i for i in ids if isinstance(i, str)]
    _model_cache[provider] = ids
    return ids


def choose_model(provider, ids):
    """Pick the id this tier uses for keep/drop triage, or None to skip the tier.

    provider : "nim" | "groq" | "cf"
    ids      : list[str] — everything the provider serves now, in its own order
    returns  : str (one of `ids`) or None

    Returning None makes `resolve_model` raise, which `triage()` catches and falls
    through to the next tier. That is deliberate, and it is the interesting call
    here: a wrong pick does not raise — it quietly returns bad keep/drop verdicts,
    and a dropped paper is never looked at again.

    What the lists actually look like (2026-08-19 live snapshots):
      groq — 13 ids, only ~3 usable for chat. The rest: whisper-large-v3*,
             canopylabs/orpheus-* (TTS), meta-llama/llama-prompt-guard-2-*
             (injection detection), openai/gpt-oss-safeguard-20b (moderation),
             allam-2-7b (Arabic). ids[0] today is groq/compound — a tool-using
             agent system, wrong and costly for a one-line verdict.
      nim  — 102 ids: writer/palmyra-med-70b, baai/bge-m3 (embeddings),
             microsoft/kosmos-2 (vision), nvidia/*, meta/*, deepseek-ai/*, ...
             Some ids are listed but do not serve chat (meta/llama-3.3-70b-instruct
             timed out at 60s on 2026-08-19), so prefer ids known to work.
      cf   — ~26 ids, already filtered to Text Generation server-side, so the
             exclusion problem mostly disappears there.

    The task is small: one abstract in, {"verdict","reason"} out. It is not
    cheap in tokens, though — everything Groq still serves reasons first, so the
    budget (MAX_TOKENS) has to cover the thinking, not the answer. A model that
    reasons *inside* `content` rather than in a separate field can never satisfy
    "JSON only" and must not be preferred at all (see _PREFER).
    """
    usable = [i for i in ids if not re.search(_EXCLUDE, i, re.I)]
    for pat in _PREFER.get(provider, []):
        for i in usable:
            if re.search(pat, i, re.I):
                return i
    # Only Cloudflare gets a "something is better than nothing" fallback: its list
    # arrives pre-filtered to Text Generation, so an unknown id there is still a
    # chat model. On NIM and Groq an unrecognised id is more likely a new modality
    # than a new instruct model, and a bad triage model is worse than no triage —
    # the caller keeps every candidate when a tier declines, and says so.
    return usable[0] if provider == "cf" and usable else None


def resolve_model(provider, env):
    """Return (model_id, how). Raises ValueError when the tier has nothing usable."""
    pinned = env.get(_OVERRIDE_VAR[provider])
    if pinned:
        return pinned, f"pinned by {_OVERRIDE_VAR[provider]}"
    ids = list_models(provider, env)
    if not ids:
        raise ValueError(f"{provider}: model list is empty")
    chosen = choose_model(provider, ids)
    if not chosen:
        raise ValueError(f"{provider}: no acceptable model among {len(ids)}")
    return chosen, f"auto-picked from {len(ids)}"


def _stamp(verdict, model, how):
    if verdict:
        verdict["model"], verdict["how"] = model, how
    return verdict


# ── providers: return a verdict dict, or None if unconfigured ──
def _nim(title, abstract, env):
    key = env.get("NVIDIA_API_KEY")
    if not key:
        return None
    model, how = resolve_model("nim", env)
    d = _post("https://integrate.api.nvidia.com/v1/chat/completions",
              {"Authorization": f"Bearer {key}"},
              {"model": model,
               "messages": _messages(title, abstract), "temperature": 0.1,
               "max_tokens": MAX_TOKENS, "response_format": {"type": "json_object"}})
    return _stamp(_parse(d["choices"][0]["message"]["content"]), model, how)


def _groq(title, abstract, env):
    key = env.get("GROQ_API_KEY") or env.get("GroqCloud_API_KEY")
    if not key:
        return None
    model, how = resolve_model("groq", env)
    d = _post("https://api.groq.com/openai/v1/chat/completions",
              {"Authorization": f"Bearer {key}"},
              {"model": model,
               "messages": _messages(title, abstract), "temperature": 0.1,
               "max_tokens": MAX_TOKENS, "response_format": {"type": "json_object"}})
    return _stamp(_parse(d["choices"][0]["message"]["content"]), model, how)


def _cloudflare(title, abstract, env):
    acct, tok = env.get("CF_ACCOUNT_ID"), env.get("CF_API_TOKEN")
    if not (acct and tok):
        return None
    model, how = resolve_model("cf", env)
    d = _post(f"https://api.cloudflare.com/client/v4/accounts/{acct}/ai/run/{model}",
              {"Authorization": f"Bearer {tok}"},
              {"messages": _messages(title, abstract), "max_tokens": MAX_TOKENS})
    return _stamp(_parse(d.get("result", {}).get("response")), model, how)


TIERS = [_nim, _groq, _cloudflare]   # dreamcatcher order: NIM → Groq → Cloudflare


def available(env=None):
    e = env or os.environ
    return bool(e.get("NVIDIA_API_KEY")
                or e.get("GROQ_API_KEY") or e.get("GroqCloud_API_KEY")
                or (e.get("CF_ACCOUNT_ID") and e.get("CF_API_TOKEN")))


def triage(title, abstract="", env=None):
    """Return {'verdict','reason','tier','model','how'} from the first working provider, or None."""
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
