"""

AI Provider — LLM adapter with deterministic fallback.



Three operating modes:

  - provider_configured (openai / azure_openai / google_ai):  real LLM is available

  - provider_not_configured:                       no env key present at all

  - deterministic_fallback:                         no key → structured template response



Core principle: if a provider is not configured the system must say so and fall back

deterministically.  No fake AI, no fake underwriting, no fake production.

"""



from __future__ import annotations



from dataclasses import dataclass, field

from math import isfinite

from typing import Any, Literal



from app.core.config import get_settings



import httpx



# ---------------------------------------------------------------------------

# Optional LLM library import — graceful degradation if not installed

# ---------------------------------------------------------------------------

try:

    import openai as _openai



    _OPENAI_AVAILABLE = True

except ImportError:

    _OPENAI_AVAILABLE = False



# ---------------------------------------------------------------------------

# Types

# ---------------------------------------------------------------------------



AIMode = Literal["deterministic_fallback", "openai", "azure_openai", "google_ai", "provider_not_configured"]





@dataclass

class AdvisorySource:

    """A single cited source returned alongside an advisory answer."""



    title: str

    snippet: str | None = None

    document_id: str | None = None





@dataclass

class AdvisoryResponse:

    """Structured response from the AI CFO service."""



    ai_mode: AIMode

    answer: str

    sources: list[AdvisorySource] = field(default_factory=list)

    disclaimer: str = ""

    warnings: list[str] = field(default_factory=list)





# ---------------------------------------------------------------------------

# Safety system prompt (always injected regardless of mode)

# ---------------------------------------------------------------------------



SAFETY_SYSTEM_PROMPT = (

    "You are a financial advisory assistant. "

    "You MUST NOT provide loan approval, underwriting decisions, or guaranteed funding. "

    "You MUST NOT make any binding financial commitments. "

    "Any recommendations are for informational purposes only and require review by "

    "a qualified Relationship Manager (RM) and BOCHK credit officers before any action. "

    "You must clearly cite your sources where possible and note when data is incomplete."

)



# ---------------------------------------------------------------------------

# AI CFO persona — layered on top of safety prompt in LLM mode

# ---------------------------------------------------------------------------



AI_CFO_SYSTEM_PROMPT = (

    "You are AI CFO, a financial advisory assistant for BOCHK Relationship Managers. "

    "Your role is to provide insightful financial analysis and answer questions based "

    "on the provided workspace data. You MUST cite specific figures and data points "

    "from the context provided. If the context doesn't contain enough information to "

    "answer a question, state that clearly. Keep responses professional, concise, and "

    "grounded in the data provided. Always use markdown formatting for readability."

)



# ---------------------------------------------------------------------------

# Deterministic fallback templates

# ---------------------------------------------------------------------------



_FALLBACK_TEMPLATES: dict[str, str] = {

    "financial_health": (

        "**Financial Health Assessment (Deterministic Fallback)**\n\n"

        "Based on the available financial data for this workspace:\n"

        "- {company_name} shows a revenue trend of {revenue_trend} over recent periods.\n"

        "- The current ratio is {current_ratio}, indicating {liquidity_assessment}.\n"

        "- Debt-to-equity ratio stands at {debt_to_equity}, suggesting {leverage_assessment}.\n\n"

        "**Important**: This is a deterministic summary based on structured financial fields. "

        "A full AI-powered analysis requires an LLM provider to be configured (set OPENAI_API_KEY "

        "or AZURE_OPENAI_API_KEY + LLM_PROVIDER in environment).\n\n"

        "*Always consult with a qualified RM and BOCHK credit officers before making decisions.*"

    ),

    "funding_readiness": (

        "**Funding Readiness Overview (Deterministic Fallback)**\n\n"

        "The workspace shows the following borrowing-base indicators:\n"

        "- Revenue: {revenue}\n"

        "- EBITDA: {ebitda}\n"

        "- Cash & Equivalents: {cash}\n"

        "- Total Assets: {total_assets}\n"

        "- Total Liabilities: {total_liabilities}\n\n"

        "**Risk Metrics:**\n"

        "- CDI Score: {cdi_score}\n"

        "- PD Estimate: {pd_estimate}\n"

        "- Stress Test Loss: {stress_loss}\n\n"

        "**Note**: These figures are extracted from structured workspace data. "

        "Configure an LLM provider for natural-language advisory generation.\n\n"

        "*Always consult with a qualified RM and BOCHK credit officers before making decisions.*"

    ),

    "default": (

        "**Advisory Response (Deterministic Fallback)**\n\n"

        "Thank you for your question. The AI CFO is currently operating in "

        "**deterministic fallback mode** because no LLM provider is configured.\n\n"

        "To enable full AI-powered advisory responses, set the following environment variables:\n"

        "- `OPENAI_API_KEY` (for OpenAI), or\n"

        "- `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT` and `LLM_PROVIDER=azure_openai` "

        "(for Azure OpenAI)\n\n"

        "Until then, responses are generated from structured templates using the workspace's "

        "available financial data.\n\n"

        "**What I can tell you based on available data:**\n"

        "- Workspace: {workspace_name}\n"

        "- Period: {period_label}\n"

        "- Revenue: {revenue}\n"

        "- Net Income: {net_income}\n\n"

        "*Always consult with a qualified RM and BOCHK credit officers before making decisions.*"

    ),

}





def _fmt(val: Any) -> str:

    """Format a numeric value with thousand separators; pass strings through."""

    if isinstance(val, (int, float)):

        if not isinstance(val, bool) and isfinite(val):

            return f"{val:,.0f}" if val == int(val) else f"{val:,}"

    return str(val)





def _build_rag_context(

    workspace_data: dict[str, Any] | None,

) -> str:

    """Build a bounded RAG context string from workspace snapshot data."""

    if not workspace_data:

        return "No workspace data available."



    parts: list[str] = []



    # Financial summary

    fs = workspace_data.get("financial_summary", {}) or {}

    fin_fields = (

        ("Revenue", "revenue"),

        ("Gross Profit", "gross_profit"),

        ("EBITDA", "ebitda"),

        ("Net Income", "net_income"),

        ("Cash & Equivalents", "cash_and_equivalents"),

        ("Total Assets", "total_assets"),

        ("Total Liabilities", "total_liabilities"),

    )

    parts.append("=== FINANCIAL SUMMARY ===")

    for label, key in fin_fields:

        parts.append(f"{label}: {_fmt(fs.get(key, 'N/A'))}")

    parts.append(f"Period: {fs.get('period_label', 'N/A')}")

    parts.append(f"Currency: {fs.get('currency', 'N/A')}")



    # Ratios

    ratios = workspace_data.get("ratios", {}) or {}

    parts.append("=== RATIOS ===")

    for key, val in ratios.items():

        parts.append(f"{key}: {val}")



    # Valuation

    val = workspace_data.get("valuation_summary", {}) or {}

    parts.append("=== VALUATION ===")

    for key, val_item in val.items():

        parts.append(f"{key}: {val_item}")



    # CDI / PD / Stress / Structuring

    for section in ("cdi_output", "pd_estimate", "stress_test", "structuring"):

        data = workspace_data.get(section, {}) or {}

        if data:

            parts.append(f"=== {section.upper()} ===")

            if isinstance(data, dict):

                for k, v in data.items():

                    parts.append(f"{k}: {v}")

            else:

                parts.append(str(data))



    # Document excerpts

    docs = workspace_data.get("document_excerpts", []) or []

    if docs:

        parts.append("=== RELEVANT DOCUMENT EXCERPTS ===")

        for i, doc in enumerate(docs[:5]):  # cap at 5 excerpts

            parts.append(f"[{i+1}] {doc.get('title', 'Untitled')}")

            snippet = doc.get("snippet", "")

            if snippet:

                parts.append(f"    {snippet[:300]}")



    return "\n".join(parts)





def _get_deterministic_response(

    question: str,

    workspace_data: dict[str, Any] | None,

) -> AdvisoryResponse:

    """Build a deterministic template-based answer."""

    ws = workspace_data or {}

    company_name = ws.get("company_name", "this workspace")

    fs = ws.get("financial_summary", {}) or {}



    # Determine template key

    q_lower = question.lower()

    template_key = "default"

    if any(w in q_lower for w in ("health", "financial health", "ratio")):

        template_key = "financial_health"

    elif any(w in q_lower for w in ("funding", "borrow", "readiness", "facility")):

        template_key = "funding_readiness"



    # Build template vars

    context = {

        "company_name": company_name,

        "workspace_name": ws.get("name", company_name),

        "period_label": fs.get("period_label", "most recent"),

        "revenue": _fmt(fs.get("revenue", "N/A")),

        "revenue_trend": fs.get("revenue_trend", "stable"),

        "net_income": _fmt(fs.get("net_income", "N/A")),

        "ebitda": _fmt(fs.get("ebitda", "N/A")),

        "cash": _fmt(fs.get("cash_and_equivalents", "N/A")),

        "total_assets": _fmt(fs.get("total_assets", "N/A")),

        "total_liabilities": _fmt(fs.get("total_liabilities", "N/A")),

        "current_ratio": ws.get("ratios", {}).get("current_ratio", "N/A"),

        "debt_to_equity": ws.get("ratios", {}).get("debt_to_equity", "N/A"),

        "liquidity_assessment": "adequate" if ws.get("ratios", {}).get("current_ratio", 0) else "needs review",

        "leverage_assessment": "elevated leverage" if float(ws.get("ratios", {}).get("debt_to_equity", 0) or 0) > 2 else "manageable",

        "cdi_score": ws.get("cdi_output", {}).get("score", "N/A"),

        "pd_estimate": ws.get("pd_estimate", {}).get("probability", "N/A"),

        "stress_loss": ws.get("stress_test", {}).get("loss_given_default", "N/A"),

    }



    template = _FALLBACK_TEMPLATES.get(template_key, _FALLBACK_TEMPLATES["default"])

    answer = template.format(**context)



    # Build sources from workspace data

    sources: list[AdvisorySource] = []

    if fs:

        sources.append(AdvisorySource(title="Financial Summary", snippet="Structured financial fields from workspace snapshot"))

    if ws.get("ratios"):

        sources.append(AdvisorySource(title="Financial Ratios", snippet="Key ratio calculations"))

    if ws.get("cdi_output"):

        sources.append(AdvisorySource(title="CDI Assessment", snippet="Credit Decision Index output"))

    if ws.get("pd_estimate"):

        sources.append(AdvisorySource(title="Probability of Default", snippet="PD estimate"))

    if ws.get("stress_test"):

        sources.append(AdvisorySource(title="Stress Test", snippet="Stress test results"))

    if ws.get("valuation_summary"):

        sources.append(AdvisorySource(title="Valuation Summary", snippet="Valuation data"))



    return AdvisoryResponse(

        ai_mode="deterministic_fallback",

        answer=answer,

        sources=sources,

        disclaimer="This is a deterministic fallback response. No AI provider is configured. "

        "All information is for reference only and requires review by a qualified RM and BOCHK credit officers.",

        warnings=["No LLM provider configured — operating in deterministic fallback mode."],

    )





def _build_sources_from_workspace(

    workspace_data: dict[str, Any] | None,

) -> list[AdvisorySource]:

    """Derive sources from workspace data (shared by deterministic and LLM modes)."""

    if not workspace_data:

        return []



    sources: list[AdvisorySource] = []

    fs = workspace_data.get("financial_summary", {}) or {}

    if fs:

        sources.append(AdvisorySource(

            title="Financial Summary",

            snippet="Structured financial fields from workspace snapshot",

        ))

    if workspace_data.get("ratios"):

        sources.append(AdvisorySource(

            title="Financial Ratios",

            snippet="Key ratio calculations",

        ))

    if workspace_data.get("cdi_output"):

        sources.append(AdvisorySource(

            title="CDI Assessment",

            snippet="Credit Decision Index output",

        ))

    if workspace_data.get("pd_estimate"):

        sources.append(AdvisorySource(

            title="Probability of Default",

            snippet="PD estimate",

        ))

    if workspace_data.get("stress_test"):

        sources.append(AdvisorySource(

            title="Stress Test",

            snippet="Stress test results",

        ))

    if workspace_data.get("valuation_summary"):

        sources.append(AdvisorySource(

            title="Valuation Summary",

            snippet="Valuation data",

        ))



    # Add document excerpts as individual sources

    docs = workspace_data.get("document_excerpts", []) or []

    for doc in docs[:5]:

        sources.append(AdvisorySource(

            title=doc.get("title", "Document Excerpt"),

            snippet=(doc.get("snippet", "") or "")[:200],

            document_id=doc.get("document_id"),

        ))



    return sources





# ---------------------------------------------------------------------------

# LLM client initialisation (lazy, on first call)

# ---------------------------------------------------------------------------





def _get_openai_client() -> tuple[Any, str] | None:

    """Return (OpenAI client, model_name) or None if config is incomplete."""

    settings = get_settings()

    key = settings.OPENAI_API_KEY.strip()

    model = settings.OPENAI_MODEL.strip() or "gpt-4o-mini"

    if not key:

        return None

    try:

        client = _openai.OpenAI(api_key=key)

        return client, model

    except Exception:

        return None





def _get_azure_openai_client() -> tuple[Any, str] | None:

    """Return (AzureOpenAI client, deployment_name) or None if config is incomplete."""

    settings = get_settings()

    key = settings.AZURE_OPENAI_API_KEY.strip()

    endpoint = settings.AZURE_OPENAI_ENDPOINT.strip()

    deployment = settings.AZURE_OPENAI_DEPLOYMENT.strip()

    if not key or not endpoint or not deployment:

        return None

    try:

        client = _openai.AzureOpenAI(

            api_key=key,

            azure_endpoint=endpoint,

            api_version="2024-06-01",

        )

        return client, deployment

    except Exception:

        return None





# ---------------------------------------------------------------------------

# Google AI (Gemini) via direct REST API

# ---------------------------------------------------------------------------





def _get_google_ai_config() -> tuple[str, str, str] | None:

    """Return (api_key, model, base_url) or None if config is incomplete."""

    settings = get_settings()

    key = settings.GOOGLE_API_KEY.strip()

    model = settings.GOOGLE_AI_MODEL.strip() or "gemini-1.5-flash"

    base_url = (settings.GOOGLE_AI_BASE_URL.strip()

                or "https://generativelanguage.googleapis.com/v1beta")

    if not key:

        return None

    return key, model, base_url





# ---------------------------------------------------------------------------

# Safety: forbidden banking word replacement

# ---------------------------------------------------------------------------



_FORBIDDEN_WORDS: dict[str, str] = {

    "approved": "reviewed / conditionally eligible",

    "guaranteed": "estimated",

    "no risk": "managed risk",

    "final decision": "indicative assessment",

    "automated credit decision": "decision-support analysis",

}





def _sanitize_response(text: str) -> str:

    """Replace forbidden banking words with safe alternatives."""

    result = text

    for word, replacement in _FORBIDDEN_WORDS.items():

        result = result.replace(word, replacement)

    return result





# ---------------------------------------------------------------------------

# LLM call

# ---------------------------------------------------------------------------



_LLM_MAX_TOKENS = 2048

_LLM_TEMPERATURE = 0.3

_LLM_TIMEOUT_SECONDS = 60





def _call_llm(

    mode: str,

    system_prompt: str,

    user_prompt: str,

) -> tuple[str | None, str | None]:

    """Call the configured LLM and return (answer_text, error_message).



    Supports:

      - openai / azure_openai: uses the openai SDK client

      - google_ai:             uses httpx to call the Gemini generateContent REST API



    Returns (None, error_message) on any failure so the caller can fall back

    deterministically.

    """



    if mode == "google_ai":

        return _call_google_gemini(system_prompt, user_prompt)



    # --- openai / azure_openai path ---

    if not _OPENAI_AVAILABLE:

        return None, "openai package is not installed."



    if mode == "openai":

        client_info = _get_openai_client()

    elif mode == "azure_openai":

        client_info = _get_azure_openai_client()

    else:

        return None, f"Unknown LLM mode: {mode}"



    if client_info is None:

        return None, f"LLM provider '{mode}' is not fully configured. Check your environment variables."



    client, model = client_info



    try:

        response = client.chat.completions.create(

            model=model,

            messages=[

                {"role": "system", "content": system_prompt},

                {"role": "user", "content": user_prompt},

            ],

            temperature=_LLM_TEMPERATURE,

            max_tokens=_LLM_MAX_TOKENS,

            timeout=_LLM_TIMEOUT_SECONDS,

        )

    except _openai.AuthenticationError as e:

        return None, f"LLM authentication error: {e}"

    except _openai.RateLimitError as e:

        return None, f"LLM rate limit exceeded: {e}"

    except _openai.APIConnectionError as e:

        return None, f"LLM connection error: {e}"

    except _openai.APIError as e:

        return None, f"LLM API error: {e}"

    except Exception as e:

        return None, f"Unexpected LLM error: {e}"



    if not response.choices:

        return None, "LLM returned an empty response (no choices)."



    answer = response.choices[0].message.content

    if not answer:

        return None, "LLM returned an empty response (no content)."



    return answer.strip(), None





def _call_google_gemini(

    system_prompt: str,

    user_prompt: str,

) -> tuple[str | None, str | None]:

    """Call the Google Gemini generateContent REST API via httpx."""

    config = _get_google_ai_config()

    if config is None:

        return None, "Google AI is not configured. Set GOOGLE_API_KEY in environment."



    api_key, model, base_url = config

    url = f"{base_url}/models/{model}:generateContent"



    payload = {

        "contents": [

            {

                "role": "user",

                "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}],

            }

        ],

        "generationConfig": {

            "temperature": _LLM_TEMPERATURE,

            "maxOutputTokens": _LLM_MAX_TOKENS,

        },

    }



    import time

    max_retries = 3
    retry_delay = 1.0
    resp = None

    for attempt in range(max_retries):
        try:
            with httpx.Client(timeout=_LLM_TIMEOUT_SECONDS) as http:
                resp = http.post(
                    url,
                    params={"key": api_key},
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
            if resp.status_code in (429, 503):
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
            break
        except httpx.TimeoutException:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            return None, "Google AI request timed out."
        except httpx.RequestError as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            return None, f"Google AI request error: {e}"
        except Exception as e:
            return None, f"Unexpected Google AI error: {e}"

    if resp is None:
        return None, "Google AI request failed (no response)."

    if resp.status_code != 200:
        body = resp.text[:300] if resp.text else "(empty body)"
        return None, f"Google AI HTTP error: {resp.status_code} {body}"



    try:

        data = resp.json()

    except Exception as e:

        return None, f"Google AI response parse error: {e}"



    # Parse the response

    candidates = data.get("candidates", [])

    if not candidates:

        # Check for blocked content

        prompt_feedback = data.get("promptFeedback", {})

        block_reason = prompt_feedback.get("blockReason")

        if block_reason:

            return None, f"Google AI request blocked: {block_reason}"

        return None, "Google AI returned an empty response (no candidates)."



    parts = candidates[0].get("content", {}).get("parts", [])

    if not parts:

        finish_reason = candidates[0].get("finishReason", "unknown")

        if finish_reason != "STOP":

            return None, f"Google AI response finished early: {finish_reason}"

        return None, "Google AI returned an empty response (no parts)."



    text = parts[0].get("text", "").strip()

    if not text:

        return None, "Google AI returned an empty response (no text)."



    # Apply safety post-processing

    text = _sanitize_response(text)



    return text, None





# ---------------------------------------------------------------------------

# Public API

# ---------------------------------------------------------------------------





def get_ai_mode() -> AIMode:

    """Detect the current AI provider mode from environment."""

    return get_settings().normalized_ai_mode  # type: ignore[return-value]





def get_advisory_response(

    question: str,

    workspace_data: dict[str, Any] | None = None,

) -> AdvisoryResponse:

    """Return an advisory response based on the current AI mode.



    When an LLM provider is configured (openai or azure_openai), the response

    is generated by a real LLM call using the bounded RAG context.  On any

    failure (network, auth, rate-limit, etc.) the system falls back to the

    deterministic template and reports the error as a warning.

    """

    mode = get_ai_mode()



    if mode == "provider_not_configured":

        return AdvisoryResponse(

            ai_mode="provider_not_configured",

            answer="AI CFO is not available. No LLM provider is configured.",

            disclaimer="Configure an LLM provider via environment variables to enable AI-powered advisory.",

            warnings=["AI provider not configured."],

        )



    if mode == "deterministic_fallback":

        return _get_deterministic_response(question, workspace_data)



    # --- real LLM call (openai / azure_openai / google_ai) ---



    # Build the bounded RAG context

    rag_context = _build_rag_context(workspace_data)



    # Build system prompt: safety first, then persona

    system_prompt = f"{SAFETY_SYSTEM_PROMPT}\n\n{AI_CFO_SYSTEM_PROMPT}"



    # Build user prompt: context + question

    user_prompt = (

        "=== WORKSPACE DATA ===\n"

        f"{rag_context}\n\n"

        "=== QUESTION ===\n"

        f"{question}"

    )



    answer_text, error_msg = _call_llm(mode, system_prompt, user_prompt)



    sources = _build_sources_from_workspace(workspace_data)



    if answer_text is not None:

        # Successful LLM inference

        return AdvisoryResponse(

            ai_mode=mode,  # type: ignore[arg-type]

            answer=answer_text,

            sources=sources,

            disclaimer=(

                "This response was generated by an AI language model and is for "

                "informational purposes only. All information requires review by "

                "a qualified Relationship Manager (RM) and BOCHK credit officers "

                "before any action."

            ),

            warnings=[],

        )



    # LLM call failed — fall back to deterministic but report the issue

    fallback = _get_deterministic_response(question, workspace_data)

    fallback.ai_mode = mode  # type: ignore[assignment]  # signal provider was available

    fallback.warnings = [

        f"LLM provider '{mode}' is configured but the API call failed. "

        f"Falling back to deterministic template. Details: {error_msg}"

    ]

    if error_msg:

        fallback.warnings.append(error_msg)

    return fallback

