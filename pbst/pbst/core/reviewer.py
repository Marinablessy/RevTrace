import json
import re

from openai import OpenAI

from config import GROQ_API_KEY, GROQ_BASE_URL, GROQ_MODEL


client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url=GROQ_BASE_URL
)


def extract_json(text):
    text = text.strip()

    # Remove Markdown code fences
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)

    # First attempt: entire response
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Second attempt: find the outermost JSON object
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        candidate = text[start:end + 1]

        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    raise ValueError(
        "Reviewer returned invalid JSON. "
        f"Raw response:\n{text}"
    )


def review_proposal(rfp_text, requirements, proposal, evidence):
    evidence_text = ""

    for item in evidence:
        evidence_text += (
            f"\n--- Evidence ---\n"
            f"{item.get('text', '')}\n"
        )

    requirements_text = json.dumps(
        requirements,
        indent=2
    )

    prompt = f"""
You are a strict proposal compliance reviewer.

Your task is to compare an RFP against a generated proposal
using ONLY the supplied RFP, proposal and historical evidence.

Do NOT use outside knowledge.

IMPORTANT GROUNDING RULES:

1. "WON" means the historical proposal won.
   It does NOT mean award-winning, industry-leading, or best-in-class.

2. "Proposed" does NOT mean "implemented", "delivered",
   "deployed", or "successfully used".

3. Historical evidence saying "remote support" does NOT
   support "24/7 on-site support".

4. Never infer a capability merely because it would be reasonable
   for such a company to have it.

5. If evidence is insufficient, classify the requirement as
   "Missing" or "Human Verification".

6. Every claim marked Supported must have clear evidence.

7. Partial means some but not all of the requirement is supported.

8. Human Verification should be used when the requirement may
   be possible but the supplied evidence does not establish it.

RFP:
{rfp_text}

REQUIREMENTS:
{requirements_text}

GENERATED PROPOSAL:
{proposal}

HISTORICAL EVIDENCE:
{evidence_text}

Return ONLY valid JSON.

Use exactly this structure:

{{
  "summary": "brief overall assessment",
  "coverage": [
    {{
      "id": "R1",
      "status": "Supported",
      "reason": "why this status was assigned",
      "evidence": "specific supporting evidence"
    }}
  ],
  "gaps": [],
  "unsupported_claims": [],
  "contradictions": [],
  "human_verification": []
}}

Allowed statuses:

- Supported
- Partial
- Missing
- Human Verification

Do not add Markdown.
Do not add explanations outside the JSON.
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
    "content": (
        "You are an adversarial factual auditor. "
        "Your job is to find unsupported claims, "
        "not to defend the proposal. "
        "A proposed, planned, intended, or hypothetical "
        "capability is still unsupported when no evidence "
        "explicitly confirms it. "
        "An RFP requirement is never evidence of vendor capability. "
        "Be highly skeptical. Return valid JSON only."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    raw = response.choices[0].message.content

    return extract_json(raw)